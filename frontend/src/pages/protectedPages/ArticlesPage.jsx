import { useOutletContext } from 'react-router-dom'
import Paper from '@mui/material/Paper'
import { useAppData } from '../../context/AppDataContext.jsx'
import Topbar from '../../components/articles/Topbar.jsx'
import ArticleList from '../../components/articles/ArticleList.jsx'

export default function ArticlesPage() {
  const { selectedCat } = useOutletContext()
  const {
    articles,
    feeds,
    technologyDomains,
    artLoading,
  } = useAppData()

  return (
    <Paper elevation={0} className="articles-page-panel">
      <Topbar
        selectedCat={selectedCat}
        technologyDomains={technologyDomains}
        articles={articles}
        feeds={feeds}
      />
      <ArticleList
        articles={articles}
        feeds={feeds}
        technologyDomains={technologyDomains}
        selectedCat={selectedCat}
        loading={artLoading}
      />
    </Paper>
  )
}
