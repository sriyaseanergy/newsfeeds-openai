import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { API } from '../config/api.js'
import { apiFetch } from '../services/api.js'
import { DEFAULT_TECHNOLOGY_DOMAINS } from '../constants/categories.js'

const AppDataContext = createContext(null)

let initialLoadPromise = null
let initialLoadResetTimer = null

export function useAppData() {
  const ctx = useContext(AppDataContext)
  if (!ctx) throw new Error('useAppData must be used within AppDataProvider')
  return ctx
}

function fetchInitialData() {
  if (!initialLoadPromise) {
    initialLoadPromise = Promise.all([
      apiFetch(API.emails).catch(() => []),
      apiFetch(API.articles).catch(() => []),
      apiFetch(API.technologyDomains).catch(() => null),
    ])
  }
  return initialLoadPromise
}

export function AppDataProvider({ children }) {
  const [statusData, setStatusData] = useState(null)
  const [feeds, setFeeds] = useState([])
  const [technologyDomains, setTechnologyDomains] = useState([])
  const [recipients, setRecipients] = useState([])
  const [recipientsLoading, setRecipientsLoading] = useState(false)
  const [articles, setArticles] = useState([])
  const [feedHealth, setFeedHealth] = useState([])
  const [artLoading, setArtLoading] = useState(false)
  const [healthLoading, setHealthLoading] = useState(false)

  const articlesRef = useRef(articles)
  const feedsRef = useRef(feeds)

  articlesRef.current = articles
  feedsRef.current = feeds

  const fetchStatus = useCallback(async () => {
    const currentArticles = articlesRef.current
    const currentFeeds = feedsRef.current
    setStatusData({
      articles: { total: currentArticles.length, pending_security_notification: 0 },
      feeds: {
        healthy: currentFeeds.filter(f => f.is_enabled).length,
        total: currentFeeds.length,
        disabled: currentFeeds.filter(f => !f.is_enabled).length,
      },
    })
  }, [])

  const fetchRecipients = useCallback(async () => {
    setRecipientsLoading(true)
    try {
      const data = await apiFetch(API.emails)
      setRecipients(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error(e)
      setRecipients([])
    } finally {
      setRecipientsLoading(false)
    }
  }, [])

  const fetchFeeds = useCallback(async () => {
    try {
      const d = await apiFetch(API.feeds)
      setFeeds(Array.isArray(d) ? d : [])
    } catch (e) {
      console.error(e)
    }
  }, [])

  const fetchTechnologyDomains = useCallback(async () => {
    try {
      const d = await apiFetch(API.technologyDomains)
      setTechnologyDomains(Array.isArray(d) ? d : [])
    } catch (e) {
      console.error(e)
      setTechnologyDomains(
        DEFAULT_TECHNOLOGY_DOMAINS.map((name, idx) => ({ id: String(idx + 1), name }))
      )
    }
  }, [])

  const fetchArticles = useCallback(async () => {
    setArtLoading(true)
    try {
      const d = await apiFetch(API.articles)
      setArticles(Array.isArray(d) ? d : [])
    } catch (e) {
      console.error(e)
    } finally {
      setArtLoading(false)
    }
  }, [])

  const fetchFeedHealth = useCallback(async () => {
    setHealthLoading(true)
    try {
      setFeedHealth([])
    } finally {
      setHealthLoading(false)
    }
  }, [])

  useEffect(() => {
    if (initialLoadResetTimer) {
      clearTimeout(initialLoadResetTimer)
      initialLoadResetTimer = null
    }

    let cancelled = false
    setRecipientsLoading(true)
    setArtLoading(true)

    fetchInitialData()
      .then(([emails, arts, domains]) => {
        if (cancelled) return

        setRecipients(Array.isArray(emails) ? emails : [])
        setArticles(Array.isArray(arts) ? arts : [])
        if (Array.isArray(domains)) {
          setTechnologyDomains(domains)
        } else {
          setTechnologyDomains(
            DEFAULT_TECHNOLOGY_DOMAINS.map((name, idx) => ({ id: String(idx + 1), name }))
          )
        }
      })
      .catch(e => {
        if (!cancelled) console.error(e)
      })
      .finally(() => {
        if (!cancelled) {
          setRecipientsLoading(false)
          setArtLoading(false)
        }
      })

    const intervalId = setInterval(() => {
      if (!cancelled) fetchStatus()
    }, 30_000)

    return () => {
      cancelled = true
      clearInterval(intervalId)
      initialLoadResetTimer = setTimeout(() => {
        initialLoadPromise = null
        initialLoadResetTimer = null
      }, 200)
    }
  }, [fetchStatus])

  useEffect(() => {
    fetchStatus()
  }, [articles.length, feeds, fetchStatus])

  const value = {
    statusData,
    feeds,
    technologyDomains,
    recipients,
    recipientsLoading,
    articles,
    feedHealth,
    artLoading,
    healthLoading,
    setRecipients,
    fetchStatus,
    fetchRecipients,
    fetchFeeds,
    fetchTechnologyDomains,
    fetchArticles,
    fetchFeedHealth,
  }

  return <AppDataContext.Provider value={value}>{children}</AppDataContext.Provider>
}
