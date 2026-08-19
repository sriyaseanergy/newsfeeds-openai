import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { API } from '../config/api.js'
import { apiFetch } from '../services/api.js'
import { DEFAULT_TECHNOLOGY_DOMAINS } from '../constants/categories.js'

const AppDataContext = createContext(null)

export function useAppData() {
  const ctx = useContext(AppDataContext)
  if (!ctx) throw new Error('useAppData must be used within AppDataProvider')
  return ctx
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
  const [apiError, setApiError] = useState(null)
  const [fetched, setFetched] = useState(false)

  const fetchStatus = useCallback(async () => {
    setStatusData({
      articles: { total: articles.length, pending_security_notification: 0 },
      feeds: {
        healthy: feeds.filter(f => f.is_enabled).length,
        total: feeds.length,
        disabled: feeds.filter(f => !f.is_enabled).length,
      },
    })
    setFetched(true)
  }, [articles.length, feeds])

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
    fetchStatus()
    fetchRecipients()
    fetchArticles()
    fetchFeedHealth()
    fetchTechnologyDomains()
    const t = setInterval(fetchStatus, 30_000)
    return () => clearInterval(t)
  }, [fetchStatus, fetchRecipients, fetchArticles, fetchFeedHealth, fetchTechnologyDomains])

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
    apiError,
    fetched,
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
