import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import { catColor } from '../../config/theme.js'
import { htmlToText, trunc } from '../../utils/format.js'
import { filterArticles } from '../../utils/articles.js'

function formatPublishedDate(dateStr) {
  if (!dateStr) return ''
  let d = String(dateStr)
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(d)) d = d.replace(' ', 'T') + 'Z'
  const parsed = new Date(d)
  if (Number.isNaN(parsed.getTime())) return ''
  return parsed.toISOString().slice(0, 10)
}

function ArticleCardMedia({ imageUrl, title, accent }) {
  const [failed, setFailed] = useState(false)
  const showImage = Boolean(imageUrl) && !failed

  return (
    <Box className="article-card-media">
      {showImage ? (
        <Box
          component="img"
          src={imageUrl}
          alt=""
          className="article-card-image"
          onError={() => setFailed(true)}
        />
      ) : (
        <Box
          className="article-card-placeholder"
          sx={{
            background: `linear-gradient(135deg, ${accent}33 0%, ${accent}14 100%)`,
          }}
        >
          <Typography className="article-card-placeholder-text">
            {(title || 'Article').charAt(0).toUpperCase()}
          </Typography>
        </Box>
      )}
    </Box>
  )
}

function ArticleCard({ article, feeds, technologyDomains, accent }) {
  const link = article.url && String(article.url).trim()
  const desc = trunc(htmlToText(article.summary || ''), 140)
  const sourceName = feeds.find(f => f.id === article.feed_id)?.name || ''
  const imageUrl = article.image_url && String(article.image_url).trim()
  const publishedDate = formatPublishedDate(article.published_at)

  return (
    <Paper
      variant="outlined"
      className="article-card"
      onClick={() => link && window.open(link, '_blank', 'noopener')}
      sx={{ cursor: link ? 'pointer' : 'default' }}
    >
      <ArticleCardMedia
        imageUrl={imageUrl}
        title={article.title}
        accent={accent}
      />
      <Box className="article-card-body">
        <Typography className="article-card-meta">
          {[sourceName, publishedDate].filter(Boolean).join(' · ')}
        </Typography>
        <Typography className="article-card-title">
          {article.title || 'Untitled'}
        </Typography>
        {desc && (
          <Typography className="article-card-summary">
            {desc}
          </Typography>
        )}
      </Box>
    </Paper>
  )
}

export default function ArticleList({
  articles,
  selectedCat,
  loading,
  feeds,
  technologyDomains,
}) {
  const items = filterArticles(articles || [], selectedCat, feeds, technologyDomains)
  const accent = catColor(selectedCat)

  if (loading) {
    return <Box className="articles-page-body" />
  }

  if (!items.length) {
    return (
      <Box className="articles-page-empty">
        <Typography className="articles-muted-text">No articles in this category</Typography>
      </Box>
    )
  }

  return (
    <Box className="articles-page-body">
      <Box className="articles-grid">
        {items.slice(0, 80).map(article => (
          <ArticleCard
            key={article.id || article.url || article.title}
            article={article}
            feeds={feeds}
            technologyDomains={technologyDomains}
            accent={accent}
          />
        ))}
      </Box>
    </Box>
  )
}
