import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import Paper from '@mui/material/Paper'
import { useAppData } from '../../context/AppDataContext.jsx'
import { technologyDomainNames } from '../../utils/articles.js'
import { DEFAULT_TECHNOLOGY_DOMAINS } from '../../constants/categories.js'
import Topbar from '../../components/articles/Topbar.jsx'
import ArticleList from '../../components/articles/ArticleList.jsx'

export default function ArticlesPage() {
  const [searchParams] = useSearchParams()
  const {
    articles,
    feeds,
    technologyDomains,
    statusData,
    artLoading,
  } = useAppData()

  const [typeFilter, setTypeFilter] = useState('All')
  const categories = technologyDomainNames(technologyDomains)
  const catFromUrl = searchParams.get('cat')
  const [selectedCat, setSelectedCat] = useState(
    catFromUrl && categories.includes(catFromUrl) ? catFromUrl : categories[0] || DEFAULT_TECHNOLOGY_DOMAINS[0]
  )

  useEffect(() => {
    if (catFromUrl && categories.includes(catFromUrl)) {
      setSelectedCat(catFromUrl)
    } else if (!categories.includes(selectedCat)) {
      setSelectedCat(categories[0] || DEFAULT_TECHNOLOGY_DOMAINS[0])
    }
  }, [catFromUrl, categories, selectedCat])

  return (
    <Paper
      elevation={0}
      sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        borderRadius: 2,
        border: 1,
        borderColor: 'divider',
      }}
    >
      <Topbar
        selectedCat={selectedCat}
        typeFilter={typeFilter}
        onTypeFilter={setTypeFilter}
        statusData={statusData}
      />
      <ArticleList
        articles={articles}
        feeds={feeds}
        technologyDomains={technologyDomains}
        selectedCat={selectedCat}
        typeFilter={typeFilter}
        loading={artLoading}
      />
    </Paper>
  )
}
