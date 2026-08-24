import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import CircularProgress from '@mui/material/CircularProgress'
import { useTheme } from '@mui/material/styles'
import { catColor } from '../../config/theme.js'
import { htmlToText, trunc, relativeTime } from '../../utils/format.js'
import { filterArticles, articleTechnologyDomain } from '../../utils/articles.js'

function formatPublishedDate(dateStr) {
  if (!dateStr) return ''
  let d = String(dateStr)
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(d)) d = d.replace(' ', 'T') + 'Z'
  const parsed = new Date(d)
  if (Number.isNaN(parsed.getTime())) return ''
  return parsed.toISOString().slice(0, 10)
}

export default function ArticleList({ articles, selectedCat, typeFilter, loading, feeds, technologyDomains }) {
  const theme = useTheme()
  const items = filterArticles(articles || [], selectedCat, typeFilter, feeds, technologyDomains)

  if (loading) {
    return (
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <CircularProgress size={20} />
      </Box>
    )
  }

  if (!items.length) {
    return (
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1,
          color: 'text.secondary',
        }}
      >
        <Typography sx={{ fontSize: 28, opacity: 0.2 }}>○</Typography>
        <Typography variant="body2">No articles match these filters</Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ flex: 1, overflowY: 'auto' }}>
      {items.slice(0, 80).map(a => {
        const categoryName = articleTechnologyDomain(a, feeds, technologyDomains)
        const color = catColor(categoryName || '')
        const accBar = a.type === 'Security' ? theme.palette.error.main : color
        const link = a.url && String(a.url).trim()
        const desc = trunc(htmlToText(a.summary || ''), 200)
        const sourceName = feeds.find(f => f.id === a.feed_id)?.name || ''
        const imageUrl = a.image_url && String(a.image_url).trim()
        const publishedDate = formatPublishedDate(a.published_at)

        return (
          <Box
            key={a.id || a.url || a.title}
            onClick={() => link && window.open(link, '_blank', 'noopener')}
            sx={{
              display: 'flex',
              cursor: link ? 'pointer' : 'default',
              borderBottom: 1,
              borderColor: 'divider',
              transition: 'background 150ms ease',
              '&:hover': {
                bgcolor: theme.palette.mode === 'dark' ? 'rgba(49,133,36,0.08)' : 'rgba(49,133,36,0.05)',
              },
            }}
          >
            <Box sx={{ width: 3, bgcolor: accBar, flexShrink: 0 }} />
            <Box
              sx={{
                flex: 1,
                p: '10px 14px',
                minWidth: 0,
                display: 'flex',
                alignItems: 'flex-start',
                gap: 1.25,
              }}
            >
              {imageUrl && (
                <Box
                  component="img"
                  src={imageUrl}
                  alt=""
                  sx={{
                    width: 76,
                    height: 76,
                    flexShrink: 0,
                    objectFit: 'cover',
                    borderRadius: 1,
                    bgcolor: 'action.hover',
                  }}
                  onError={event => {
                    event.currentTarget.style.display = 'none'
                  }}
                />
              )}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 0.625, mb: 0.5 }}>
                  {sourceName && (
                    <Typography variant="caption" color="text.secondary" fontWeight={500}>
                      {trunc(sourceName, 24)}
                    </Typography>
                  )}
                  {publishedDate && (
                    <>
                      {sourceName && (
                        <Typography variant="caption" color="text.disabled">·</Typography>
                      )}
                      <Typography variant="caption" color="text.disabled">
                        {publishedDate}
                      </Typography>
                    </>
                  )}
                  {categoryName && (
                    <>
                      {(sourceName || publishedDate) && (
                        <Typography variant="caption" color="text.disabled">·</Typography>
                      )}
                      <Typography variant="caption" color="text.disabled" sx={{ textTransform: 'uppercase' }}>
                        {categoryName}
                      </Typography>
                    </>
                  )}
                  {!publishedDate && a.published_at && (
                    <>
                      {sourceName && (
                        <Typography variant="caption" color="text.disabled">·</Typography>
                      )}
                      <Typography variant="caption" color="text.disabled">
                        {relativeTime(a.published_at)}
                      </Typography>
                    </>
                  )}
                </Box>
                <Typography
                  variant="body2"
                  sx={{
                    lineHeight: 1.45,
                    mb: desc ? 0.5 : 0,
                    overflow: 'hidden',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                  }}
                >
                  {a.title || 'Untitled'}
                </Typography>
                {desc && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      lineHeight: 1.5,
                      overflow: 'hidden',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical',
                    }}
                  >
                    {desc}
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>
        )
      })}
    </Box>
  )
}
