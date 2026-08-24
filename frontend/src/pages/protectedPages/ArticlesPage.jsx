import { useState } from 'react'
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
    statusData,
    artLoading,
  } = useAppData()

  const [typeFilter, setTypeFilter] = useState('All')

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
