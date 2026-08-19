import { DEFAULT_TECHNOLOGY_DOMAINS } from '../constants/categories.js'

export function normalizeTechnologyDomain(name) {
  return name || 'AI'
}

export function technologyDomainNames(domains) {
  const names = (domains || []).map(d => d.name).filter(Boolean)
  return names.length ? names : DEFAULT_TECHNOLOGY_DOMAINS
}

export function articleTechnologyDomain(article, feeds, domains) {
  const feed = feeds.find(f => f.id === article.feed_id)
  if (!feed) return 'AI'
  const domain = domains.find(d => d.id === feed.technology_domain_id)
  return domain ? domain.name : 'AI'
}

export function catCount(articles, cat, feeds, domains) {
  if (!articles?.length) return 0
  return articles.filter(a => articleTechnologyDomain(a, feeds, domains) === cat).length
}

export function filterArticles(articles, selectedCat, typeFilter, feeds, domains) {
  let base = (articles || []).filter(a => articleTechnologyDomain(a, feeds, domains) === selectedCat)
  if (typeFilter === 'Security') base = base.filter(a => a.type === 'Security')
  else if (typeFilter === 'Dev') base = base.filter(a => a.type === 'Dev')
  return base
}
