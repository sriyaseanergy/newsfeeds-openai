export function normalizeTechnologyDomain(name) {
  return name || ''
}

export function technologyDomainNames(domains) {
  return (domains || []).map(d => d.name).filter(Boolean)
}

export function getTechnologyDomain(domains, categoryName) {
  return (domains || []).find(d => d.name === categoryName) || null
}

export function articleTechnologyDomain(article, feeds, domains) {
  const feed = feeds.find(f => f.id === article.feed_id)
  if (!feed) return ''
  const domain = domains.find(d => d.id === feed.technology_domain_id)
  return domain ? domain.name : ''
}

export function catCount(articles, cat, feeds, domains) {
  if (!articles?.length || !cat) return 0
  return articles.filter(a => articleTechnologyDomain(a, feeds, domains) === cat).length
}

export function filterArticles(articles, selectedCat, feeds, domains) {
  if (!selectedCat) return []
  return (articles || []).filter(
    a => articleTechnologyDomain(a, feeds, domains) === selectedCat,
  )
}

export function getCategoryStats(articles, selectedCat, feeds, domains) {
  const items = filterArticles(articles, selectedCat, feeds, domains)
  const categoryFeeds = (feeds || []).filter(f => {
    const domain = domains.find(d => d.id === f.technology_domain_id)
    return domain?.name === selectedCat
  })
  const activeFeeds = categoryFeeds.filter(f => f.is_enabled).length

  return {
    total: items.length,
    pendingSec: items.filter(a => a.type === 'Security').length,
    feedsActive: activeFeeds,
    feedsTotal: categoryFeeds.length,
  }
}
