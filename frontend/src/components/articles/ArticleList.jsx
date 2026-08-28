import { useEffect, useMemo, useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { htmlToText, trunc } from '../../utils/format.js'
import { filterArticles } from '../../utils/articles.js'
import CustomLoader from '../CustomLoader.jsx'

function getHostname(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}

function getFaviconUrl(url) {
  const host = getHostname(url)
  return host ? `https://www.google.com/s2/favicons?domain=${host}&sz=32` : ''
}

function formatPublishedDate(dateStr) {
  if (!dateStr) return ''
  const parsed = new Date(dateStr)
  if (Number.isNaN(parsed.getTime())) return ''
  return parsed.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

function SourceBadge({ name, url }) {
  const [failed, setFailed] = useState(false)
  const favicon = getFaviconUrl(url)

  return (
    <Box className="article-feed-source">
      {favicon && !failed ? (
        <Box
          component="img"
          src={favicon}
          alt=""
          className="article-feed-favicon"
          loading="lazy"
          onError={() => setFailed(true)}
        />
      ) : (
        <Box className="article-feed-favicon article-feed-favicon--fallback">
          {(name || '?').charAt(0).toUpperCase()}
        </Box>
      )}
      <Typography className="article-feed-source-name">{name}</Typography>
    </Box>
  )
}

function ArticleThumb({ imageUrl }) {
  const [failed, setFailed] = useState(false)
  if (!imageUrl || failed) return null

  return (
    <Box
      component="img"
      src={imageUrl}
      alt=""
      className="article-feed-thumb"
      loading="lazy"
      onError={() => setFailed(true)}
    />
  )
}

function ArticleRow({ article, feed }) {
  const link = article.url && String(article.url).trim()
  const sourceName = feed?.name || getHostname(article.url) || 'Source'
  const sourceUrl = feed?.url || article.url || ''
  const imageUrl = article.image_url && String(article.image_url).trim()
  const publishedDate = formatPublishedDate(article.published_at)
  const author = article.author && String(article.author).trim()
  const summary = trunc(htmlToText(article.summary || ''), 120)

  const metaParts = []
  if (author) metaParts.push(`By ${author}`)
  if (publishedDate) metaParts.push(publishedDate)

  return (
    <Box
      className="article-feed-row"
      onClick={() => link && window.open(link, '_blank', 'noopener')}
      sx={{ cursor: link ? 'pointer' : 'default' }}
    >
      <Box className="article-feed-content">
        <SourceBadge name={sourceName} url={sourceUrl} />
        <Typography className="article-feed-title">
          {article.title || 'Untitled'}
        </Typography>
        {metaParts.length > 0 && (
          <Typography className="article-feed-meta">
            {metaParts.join(' · ')}
          </Typography>
        )}
        {summary && (
          <Typography className="article-feed-summary">
            {summary}
          </Typography>
        )}
      </Box>
      <ArticleThumb imageUrl={imageUrl} />
    </Box>
  )
}

function ArticleColumn({ items, feeds }) {
  return (
    <Box className="articles-feed-column">
      {items.map(article => (
        <ArticleRow
          key={article.id || article.url || article.title}
          article={article}
          feed={feeds.find(f => f.id === article.feed_id)}
        />
      ))}
    </Box>
  )
}

export default function ArticleList({
  articles,
  selectedCat,
  loading,
  feeds,
  technologyDomains,
}) {
  const items = useMemo(
    () => filterArticles(articles || [], selectedCat, feeds, technologyDomains),
    [articles, selectedCat, feeds, technologyDomains],
  )

  const [renderReady, setRenderReady] = useState(false)

  useEffect(() => {
    if (loading) {
      setRenderReady(false)
      return undefined
    }

    if (!items.length) {
      setRenderReady(true)
      return undefined
    }

    setRenderReady(false)
    let cancelled = false
    const frame = requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        if (!cancelled) setRenderReady(true)
      })
    })

    return () => {
      cancelled = true
      cancelAnimationFrame(frame)
    }
  }, [loading, selectedCat, items])

  const showLoader = loading || !renderReady
  const visible = items.slice(0, 80)
  const splitAt = Math.ceil(visible.length / 2)
  const leftItems = visible.slice(0, splitAt)
  const rightItems = visible.slice(splitAt)

  return (
    <Box className="articles-page-body articles-page-body--relative">
      {showLoader && <CustomLoader />}
      {!loading && !items.length ? (
        <Box className="articles-page-empty">
          <Typography className="articles-muted-text">No articles in this category</Typography>
        </Box>
      ) : (
        <Box className="articles-feed-grid">
          <ArticleColumn items={leftItems} feeds={feeds} />
          {rightItems.length > 0 && (
            <ArticleColumn items={rightItems} feeds={feeds} />
          )}
        </Box>
      )}
    </Box>
  )
}
