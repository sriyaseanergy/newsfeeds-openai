export function htmlToText(html) {
  if (!html) return ''
  try {
    const doc = new DOMParser().parseFromString(html, 'text/html')
    return (doc.body?.textContent ?? '').replace(/\s+/g, ' ').trim()
  } catch {
    return String(html).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
  }
}

export function trunc(str, max) {
  if (!str || str.length <= max) return str
  return str.slice(0, max).trim() + '…'
}

export function relativeTime(dateStr) {
  if (!dateStr) return ''
  let d = String(dateStr)
  if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(d)) d = d.replace(' ', 'T') + 'Z'
  const diff = Math.floor((Date.now() - new Date(d).getTime()) / 1000)
  if (isNaN(diff) || diff < 0) return ''
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
