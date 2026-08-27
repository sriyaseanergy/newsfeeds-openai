import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import { catColor } from '../../config/theme.js'
import { getTechnologyDomain, getCategoryStats } from '../../utils/articles.js'

export default function Topbar({
  selectedCat,
  technologyDomains,
  articles,
  feeds,
}) {
  const domain = getTechnologyDomain(technologyDomains, selectedCat)
  const stats = getCategoryStats(articles, selectedCat, feeds, technologyDomains)
  const accent = catColor(selectedCat)
  const feedValue = stats.feedsTotal
    ? `${stats.feedsActive}/${stats.feedsTotal}`
    : '0/0'

  const statItems = [
    { label: 'Total', value: stats.total, tone: 'default' },
    { label: 'Pending SEC', value: stats.pendingSec, tone: 'danger' },
    { label: 'Feeds', value: feedValue, tone: 'accent' },
  ]

  return (
    <Box className="articles-page-header">
      <Box className="articles-page-heading">
        <Box
          className="articles-page-accent"
          sx={{ bgcolor: accent }}
        />
        <Box sx={{ minWidth: 0 }}>
          <Typography component="h2" className="articles-page-title">
            {selectedCat || 'Articles'}
          </Typography>
          {domain?.description && (
            <Typography className="articles-page-subtitle">
              {domain.description}
            </Typography>
          )}
        </Box>
      </Box>

      <Box className="articles-stat-row">
        {statItems.map(item => (
          <Paper
            key={item.label}
            variant="outlined"
            className={`articles-stat-card articles-stat-card--${item.tone}`}
          >
            <Typography className="articles-stat-label">{item.label}</Typography>
            <Typography className="articles-stat-value">{item.value}</Typography>
          </Paper>
        ))}
      </Box>
    </Box>
  )
}
