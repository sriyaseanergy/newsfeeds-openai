import { useOutletContext } from 'react-router-dom'
import Paper from '@mui/material/Paper'
import { useAppData } from '../../context/AppDataContext.jsx'
import ArticleList from '../../components/articles/ArticleList.jsx'

export default function ArticlesPage() {
  const { selectedCat } = useOutletContext()
  const {
    articles,
    feeds,
    technologyDomains,
    artLoading,
    feedsLoading,
  } = useAppData()

  return (
    <Paper elevation={0} className="articles-page-panel">
      <ArticleList
        articles={articles}
        feeds={feeds}
        technologyDomains={technologyDomains}
        selectedCat={selectedCat}
        loading={artLoading || feedsLoading}
      />
    </Paper>
  )
}
