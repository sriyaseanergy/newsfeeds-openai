import { useState, useEffect, useCallback, useRef } from 'react'
import seanergyLogo from './assets/seanergy-logo.png'
import seanergyIcon from './assets/seanergy-icon.png'
import { BRAND, LAYOUT, THEME_STORAGE_KEY } from './theme/appTheme.js'
import {
    IconNotes, IconSearch, IconDarkMode, IconLightMode, IconNotifications,
    IconFeedHealth, IconSettings, IconPerson, IconLogout,
    IconChevronRight, IconChevronLeft, IconSecurity, IconEngineering, IconPsychology, IconLightbulb, IconArticle, IconHome,
} from './components/layout/LayoutIcons.jsx'
// Login page flow is temporarily disabled to unblock other screen changes.
// import LoginPage, { clearStoredEmployee, readStoredEmployee } from './LoginPage.jsx'
// import { getMsalInstance, getMsalRedirectUri } from './msalInstance.js'

// ─── API ──────────────────────────────────────────────────────────────────────

const API_BASE = (() => {
    const explicit = import.meta.env.VITE_API_BASE
    if (explicit) return String(explicit).replace(/\/+$/, '')
    const fromBackend = import.meta.env.VITE_API_BASE_PATH
    if (fromBackend) return String(fromBackend).replace(/\/+$/, '')
    return (import.meta.env.BASE_URL || '/').replace(/\/+$/, '')
})()

const API = {
    articles:    `${API_BASE}/api/articles`,
    emails:      `${API_BASE}/api/email/recipients`,
    feeds:       `${API_BASE}/api/feeds`,
    quadrants:   `${API_BASE}/api/quadrants`,
    status:      `${API_BASE}/api/status`,
    feedsHealth: `${API_BASE}/api/feeds/health`,
}

async function apiFetch(url, opts = {}) {
    const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts })
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function htmlToText(html) {
    if (!html) return ''
    try {
        const doc = new DOMParser().parseFromString(html, 'text/html')
        return (doc.body?.textContent ?? '').replace(/\s+/g, ' ').trim()
    } catch {
        return String(html).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim()
    }
}

function trunc(str, max) {
    if (!str || str.length <= max) return str
    return str.slice(0, max).trim() + '…'
}

function relativeTime(dateStr) {
    if (!dateStr) return ''
    let d = String(dateStr)
    // "YYYY-MM-DD HH:MM:SS" stored as UTC — add T and Z
    if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(d)) d = d.replace(' ', 'T') + 'Z'
    const diff = Math.floor((Date.now() - new Date(d).getTime()) / 1000)
    if (isNaN(diff) || diff < 0) return ''
    if (diff < 60)    return `${diff}s ago`
    if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
    return `${Math.floor(diff / 86400)}d ago`
}

// ─── Right panel auto-close ───────────────────────────────────────────────────

const RIGHT_PANEL_INITIAL_MS = 5_000
const RIGHT_PANEL_MAX_MS = 5 * 60_000

// ─── Design tokens ────────────────────────────────────────────────────────────

const C = {
    pageBg:     'var(--page-bg)',
    panelBg:    'var(--panel-bg)',
    border:     'var(--border)',
    text:       'var(--text)',
    muted:      'var(--text-secondary)',
    faint:      'var(--text-faint)',
    accent:     BRAND.main,
    accentBg:   'var(--accent-bg)',
    accentText: 'var(--accent-text)',
    green:      BRAND.main,
    amber:      '#fbbf24',
    red:        '#f87171',
    // category palette
    'Risks & Threats':       '#f87171',
    Engineering:             '#2563eb',
    'AI & Machine Learning': '#a78bfa',
    'Expert Context':        '#fb923c',
    Security:   '#f87171',
    AI:         '#a78bfa',
    ML:         '#818cf8',
    Frontend:   '#60a5fa',
    Backend:    '#2563eb',
    BI:         '#fb923c',
    Dev:        '#4f5fff',
}

// Layout dimensions (app shell)
const DRAWER_WIDTH = LAYOUT.drawerWidth
const HEADER_HEIGHT = LAYOUT.headerHeight
const FOOTER_HEIGHT = LAYOUT.footerHeight

// ─── Category config ──────────────────────────────────────────────────────────

const DEFAULT_QUADRANTS = ['Risks & Threats', 'Engineering', 'AI & Machine Learning', 'Expert Context']
const DEV_BYPASS_SESSION = {
    name: 'Frontend Dev User',
    email: 'frontend.dev@local',
    designation: 'super admin',
}

const CAT_DESC = {
    'Risks & Threats':       'CVEs, advisories, exploits',
    'AI & Machine Learning': 'Model releases, research, agents',
    Engineering:             'Engineering updates and tooling',
    'Expert Context':        'Analyst and industry context',
}

function catColor(cat) { return C[cat] || 'rgba(15,23,42,0.4)' }

function normalizeQuadrant(name) {
    return name === 'Frontier AI' ? 'AI & Machine Learning' : (name || 'Engineering')
}

function quadrantNames(quadrants) {
    const names = (quadrants || []).map(q => q.name).filter(Boolean)
    return names.length ? names : DEFAULT_QUADRANTS
}

function articleQuadrant(article) {
    return normalizeQuadrant(article.category || article.quadrant || (article.type === 'Security' ? 'Risks & Threats' : 'Engineering'))
}

function catCount(articles, cat) {
    if (!articles?.length) return 0
    return articles.filter(a => articleQuadrant(a) === cat).length
}

function filterArticles(articles, selectedCat, typeFilter) {
    let base = (articles || []).filter(a => articleQuadrant(a) === selectedCat)
    if (typeFilter === 'Security')      base = base.filter(a => a.type === 'Security')
    else if (typeFilter === 'Dev')      base = base.filter(a => a.type === 'Dev')
    return base
}

// ─── Micro-components ─────────────────────────────────────────────────────────

function Dot({ color, size = 6 }) {
    return (
        <div style={{
            width: size, height: size, borderRadius: '50%',
            background: color, flexShrink: 0,
        }} />
    )
}

function Spinner({ size = 12 }) {
    return (
        <span style={{
            display: 'inline-block', width: size, height: size,
            border: `1.5px solid ${C.faint}`, borderTopColor: C.accent,
            borderRadius: '50%', animation: 'spin 0.7s linear infinite', flexShrink: 0,
        }} />
    )
}

function Btn({ children, onClick, variant = 'ghost', size = 'md', disabled, loading, style: s = {} }) {
    const pad = size === 'sm' ? '4px 10px' : '6px 14px'
    const fs  = size === 'sm' ? 11 : 12
    const variants = {
        ghost:   { background: C.faint,    color: C.muted,      border: `0.5px solid ${C.border}` },
        primary: { background: C.accentBg, color: C.accentText, border: `0.5px solid ${C.accent}` },
        danger:  { background: 'rgba(248,113,113,0.1)', color: C.red, border: `0.5px solid rgba(248,113,113,0.3)` },
    }
    return (
        <button onClick={onClick} disabled={disabled || loading} style={{
            display: 'inline-flex', alignItems: 'center', gap: 5,
            padding: pad, fontSize: fs, fontWeight: 500, borderRadius: 6,
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.4 : 1, transition: 'opacity 150ms ease',
            fontFamily: 'inherit', lineHeight: 1.4,
            ...(variants[variant] || variants.ghost), ...s,
        }}>
            {loading ? <Spinner size={10} /> : null}{children}
        </button>
    )
}

function Toggle({ checked, onChange, disabled }) {
    return (
        <div
            role="switch" aria-checked={checked}
            onClick={() => !disabled && onChange(!checked)}
            style={{
                width: 30, height: 17, borderRadius: 9,
                cursor: disabled ? 'not-allowed' : 'pointer',
                background: checked ? C.accent : C.faint,
                border: `0.5px solid ${checked ? C.accent : C.border}`,
                position: 'relative', transition: 'all 150ms ease', flexShrink: 0,
            }}
        >
            <div style={{
                position: 'absolute', top: 2, left: checked ? 14 : 2,
                width: 11, height: 11, borderRadius: '50%',
                background: checked ? '#fff' : 'var(--toggle-knob-off)',
                transition: 'left 150ms ease',
            }} />
        </div>
    )
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function quadrantIcon(cat) {
    const icons = {
        'Risks & Threats':       IconSecurity,
        'Engineering':             IconEngineering,
        'AI & Machine Learning': IconPsychology,
        'Expert Context':        IconLightbulb,
        'Frontier AI':           IconPsychology,
    }
    return icons[cat] || IconArticle
}

function SidebarMenuButton({ active, onClick, Icon, label, badge }) {
    return (
        <button
            type="button"
            className={`fa-menu-link${active ? ' active' : ''}`}
            onClick={onClick}
        >
            <span className="fa-menu-icon"><Icon /></span>
            <span className="fa-menu-text">{label}</span>
            {badge > 0 && <span className="fa-menu-badge">{badge}</span>}
        </button>
    )
}

function SidebarMenuItem(props) {
    return (
        <li className="fa-menu-item">
            <SidebarMenuButton {...props} />
        </li>
    )
}

function Sidebar({ articles, quadrants, selectedCat, onSelectCat, activeView, onView, collapsed }) {
    const categories = quadrantNames(quadrants)
    const bottomItems = [
        { id: 'feedhealth', Icon: IconFeedHealth, label: 'Feed Health' },
        { id: 'settings',   Icon: IconSettings,   label: 'Settings'   },
    ]

    return (
        <aside className={`fa-drawer${collapsed ? ' collapsed' : ''}`}>
            <div className="fa-drawer-inner">
                <ul className="fa-menu-list">
                    {categories.map(cat => {
                        const active = activeView === 'articles' && selectedCat === cat
                        const count  = catCount(articles, cat)
                        const Icon   = quadrantIcon(cat)
                        return (
                            <SidebarMenuItem
                                key={cat}
                                active={active}
                                Icon={Icon}
                                label={cat}
                                badge={count}
                                onClick={() => { onSelectCat(cat); onView('articles') }}
                            />
                        )
                    })}
                </ul>

                <div className="fa-drawer-bottom">
                    {bottomItems.map(({ id, Icon, label }) => (
                        <div key={id} className="fa-menu-item">
                            <SidebarMenuButton
                                active={activeView === id}
                                Icon={Icon}
                                label={label}
                                onClick={() => onView(id)}
                            />
                        </div>
                    ))}
                </div>
            </div>
        </aside>
    )
}

function UserProfileMenu({ sessionEmployee, onLogout }) {
    const [open, setOpen] = useState(false)
    const wrapRef = useRef(null)
    const avatarLetter = (sessionEmployee?.name || 'U').charAt(0).toUpperCase()

    useEffect(() => {
        if (!open) return
        const handleClickOutside = e => {
            if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false)
        }
        document.addEventListener('mousedown', handleClickOutside)
        return () => document.removeEventListener('mousedown', handleClickOutside)
    }, [open])

    const handleLogout = () => {
        setOpen(false)
        onLogout()
    }

    return (
        <div className="fa-profile-wrap" ref={wrapRef}>
            <button
                type="button"
                className="fa-avatar"
                title="Account"
                onClick={() => setOpen(prev => !prev)}
                aria-expanded={open}
                aria-haspopup="true"
            >
                {avatarLetter}
            </button>

            {open && sessionEmployee && (
                <ul className="fa-profile-menu" role="menu" tabIndex={-1}>
                    <li className="fa-profile-menu-user" role="none">
                        <h6 className="fa-profile-menu-name">{sessionEmployee.name || '—'}</h6>
                        <p className="fa-profile-menu-email">{sessionEmployee.email || ''}</p>
                    </li>
                    <li className="fa-profile-menu-divider-wrap" role="separator">
                        <hr className="fa-profile-menu-divider" />
                    </li>
                    <li role="none">
                        <button
                            type="button"
                            className="fa-profile-menu-item"
                            role="menuitem"
                            onClick={() => setOpen(false)}
                        >
                            <span className="fa-profile-menu-item-icon"><IconPerson /></span>
                            Profile
                        </button>
                    </li>
                    <li role="none">
                        <button
                            type="button"
                            className="fa-profile-menu-item fa-profile-menu-item--logout"
                            role="menuitem"
                            onClick={handleLogout}
                        >
                            <span className="fa-profile-menu-item-icon"><IconLogout /></span>
                            Logout
                        </button>
                    </li>
                </ul>
            )}
        </div>
    )
}

function LayoutHeader({ sessionEmployee, onLogout, collapsed, onToggleDrawer, darkMode, onToggleDarkMode }) {
    return (
        <header className="fa-header">
            <div className={`fa-header-brand-col${collapsed ? ' collapsed' : ''}`}>
                {collapsed ? (
                    <div className="fa-header-logo-icon-wrap">
                        <img
                            src={seanergyIcon}
                            alt="seanergy.ai"
                            className="fa-header-logo-icon"
                        />
                    </div>
                ) : (
                    <img
                        src={seanergyLogo}
                        alt="seanergy.ai"
                        className="fa-header-logo-full"
                    />
                )}
            </div>
            <div className="fa-header-nav">
                <button
                    type="button"
                    className="fa-menu-toggle"
                    onClick={onToggleDrawer}
                    title={collapsed ? 'Expand menu' : 'Collapse menu'}
                    aria-label={collapsed ? 'Expand menu' : 'Collapse menu'}
                >
                    <span className={`fa-toggle-icon${collapsed ? '' : ' fa-toggle-icon-menu'}`}>
                        {collapsed ? <IconChevronRight size={25} /> : <IconNotes size={30} color={BRAND.main} />}
                    </span>
                </button>
                <span className="fa-header-subtitle">Feed Alerts Engine</span>
            </div>
            <div className="fa-header-spacer" />
            <div className="fa-header-right">
                <div className="fa-search-wrap">
                    <input type="text" placeholder="Search articles, feeds..." readOnly />
                    <span className="fa-search-icon"><IconSearch /></span>
                </div>
                <button
                    type="button"
                    className={`fa-icon-btn${darkMode ? ' active' : ''}`}
                    title={darkMode ? 'Light mode' : 'Dark mode'}
                    aria-pressed={darkMode}
                    onClick={onToggleDarkMode}
                >
                    {darkMode ? <IconLightMode /> : <IconDarkMode />}
                </button>
                <button type="button" className="fa-icon-btn" title="Notifications"><IconNotifications /></button>
                <UserProfileMenu sessionEmployee={sessionEmployee} onLogout={onLogout} />
            </div>
        </header>
    )
}

function LayoutFooter() {
    return (
        <footer className="fa-footer">
            <p className="fa-footer-copy">© seanergy.ai group. All rights reserved</p>
        </footer>
    )
}

function LayoutBreadcrumb({ activeView, selectedCat }) {
    const pageLabel = activeView === 'articles'
        ? selectedCat
        : activeView === 'feedhealth'
            ? 'Feed Health'
            : 'Settings'

    return (
        <div className="fa-top-bar">
            <nav className="fa-breadcrumb">
                <a href="#" className="fa-breadcrumb-home">
                    <span className="fa-breadcrumb-home-icon"><IconHome /></span>
                    <span>Home</span>
                </a>
                <span className="fa-breadcrumb-sep">/</span>
                <span className="fa-breadcrumb-current">{pageLabel}</span>
            </nav>
        </div>
    )
}

// ─── Topbar ───────────────────────────────────────────────────────────────────

function Topbar({ selectedCat, typeFilter, onTypeFilter, statusData }) {
    const counts  = statusData?.articles
    const feeds   = statusData?.feeds
    const total   = counts?.total                            ?? '—'
    const pendSec = counts?.pending_security_notification   ?? '—'
    const healthy = feeds ? `${feeds.healthy}/${feeds.total}` : '—'
    const feedColor = (feeds?.disabled ?? 0) > 0 ? C.amber : C.accent

    return (
        <div style={{
            padding: '16px 20px 0',
            background: C.panelBg,
            borderBottom: `0.5px solid ${C.border}`,
            flexShrink: 0,
        }}>
            {/* Title + filter pills */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Dot color={catColor(selectedCat)} size={7} />
                    <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: C.text, letterSpacing: '-0.01em' }}>
                            {selectedCat}
                        </div>
                        <div style={{ fontSize: 10, color: C.muted, marginTop: 1 }}>
                            {CAT_DESC[selectedCat] || ''}
                        </div>
                    </div>
                </div>
                <div style={{ display: 'flex', gap: 4 }}>
                    {[['All', 'All'], ['SEC', 'Security'], ['DEV', 'Dev']].map(([label, val]) => {
                        const active = typeFilter === val
                        return (
                            <button key={val} onClick={() => onTypeFilter(val)} style={{
                                padding: '3px 10px', borderRadius: 6, fontSize: 11,
                                cursor: 'pointer', lineHeight: 1.5,
                                background: active ? C.accentBg : 'transparent',
                                border: `0.5px solid ${active ? C.accent : C.border}`,
                                color: active ? C.accentText : C.muted,
                                transition: 'all 150ms ease', fontFamily: 'inherit',
                            }}>{label}</button>
                        )
                    })}
                </div>
            </div>

            {/* Stat cells */}
            <div style={{ display: 'flex' }}>
                {[
                    { label: 'Total',       value: total,   color: C.text     },
                    { label: 'Pending SEC', value: pendSec, color: C.red      },
                    { label: 'Feeds',       value: healthy, color: feedColor  },
                ].map(({ label, value, color }, i) => (
                    <div key={label} style={{
                        flex: 1, padding: '9px 0',
                        paddingLeft: i > 0 ? 14 : 0,
                        borderLeft: i > 0 ? `0.5px solid ${C.border}` : 'none',
                        marginLeft: i > 0 ? 14 : 0,
                    }}>
                        <div style={{
                            fontSize: 10, color: C.muted,
                            letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: 2,
                        }}>{label}</div>
                        <div style={{ fontSize: 15, fontWeight: 600, color, fontFamily: 'monospace' }}>
                            {value}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    )
}

// ─── Article list ─────────────────────────────────────────────────────────────

function ArticleList({ articles, selectedCat, typeFilter, loading }) {
    const items = filterArticles(articles || [], selectedCat, typeFilter)

    if (loading) {
        return (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Spinner size={20} />
            </div>
        )
    }

    if (!items.length) {
        return (
            <div style={{
                flex: 1, display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center',
                gap: 8, color: C.muted, fontSize: 12,
            }}>
                <span style={{ fontSize: 28, opacity: 0.2 }}>○</span>
                No articles match these filters
            </div>
        )
    }

    return (
        <div style={{ flex: 1, overflowY: 'auto' }}>
            {items.slice(0, 80).map(a => {
                const color  = catColor(a.category || '')
                const accBar = a.type === 'Security' ? C.red : color
                const link   = a.link && String(a.link).trim()
                const desc   = trunc(htmlToText(a.summary || ''), 200)

                return (
                    <div
                        key={a.unique_id || a.link || a.title}
                        onClick={() => link && window.open(link, '_blank', 'noopener')}
                        style={{
                            display: 'flex', cursor: link ? 'pointer' : 'default',
                            borderBottom: `0.5px solid ${C.border}`,
                            transition: 'background 150ms ease, border-color 150ms ease',
                        }}
                        onMouseEnter={e => {
                            e.currentTarget.style.background    = 'var(--article-hover-bg)'
                            e.currentTarget.style.borderColor   = 'var(--article-hover-border)'
                        }}
                        onMouseLeave={e => {
                            e.currentTarget.style.background    = 'transparent'
                            e.currentTarget.style.borderColor   = C.border
                        }}
                    >
                        {/* 3px accent bar */}
                        <div style={{ width: 3, background: accBar, flexShrink: 0 }} />

                        <div style={{ flex: 1, padding: '10px 14px', minWidth: 0 }}>
                            {/* Source + time */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 5, marginBottom: 4 }}>
                                <span style={{ fontSize: 11, color: C.muted, fontWeight: 500 }}>
                                    {trunc(a.source || '', 24)}
                                </span>
                                {a.published_date && <>
                                    <span style={{ fontSize: 9, color: C.faint }}>·</span>
                                    <span style={{ fontSize: 10, color: C.faint }}>
                                        {relativeTime(a.published_date)}
                                    </span>
                                </>}
                            </div>

                            {/* Title */}
                            <div style={{
                                fontSize: 12, color: C.text, lineHeight: 1.45,
                                marginBottom: desc ? 4 : 0,
                                overflow: 'hidden', display: '-webkit-box',
                                WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                            }}>
                                {a.title || 'Untitled'}
                            </div>

                            {/* Description */}
                            {desc && (
                                <div style={{
                                    fontSize: 11, color: C.muted,
                                    lineHeight: 1.5,
                                    overflow: 'hidden', display: '-webkit-box',
                                    WebkitLineClamp: 2, WebkitBoxOrient: 'vertical',
                                }}>
                                    {desc}
                                </div>
                            )}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

// ─── Feed Health view ─────────────────────────────────────────────────────────

function FeedHealthView({ feedHealth, loading, onRefresh }) {
    const [showAll, setShowAll] = useState(false)

    const disabled = feedHealth.filter(f => f.disabled)
    const failing  = feedHealth.filter(f => !f.disabled && f.consecutive_failures > 0)
    const healthy  = feedHealth.filter(f => !f.disabled && !f.consecutive_failures && f.last_success)
    const never    = feedHealth.filter(f => !f.last_success && !f.disabled)
    const issues   = [...disabled, ...failing, ...never]
    const visible  = showAll ? feedHealth : issues

    return (
        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 16 }}>
                <div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: C.text }}>Feed Health</div>
                    <div style={{ fontSize: 11, color: C.muted, marginTop: 2 }}>
                        {healthy.length} healthy · {failing.length} failing · {disabled.length} disabled
                    </div>
                </div>
                <div style={{ display: 'flex', gap: 6 }}>
                    {feedHealth.length > 0 && (
                        <Btn size="sm" onClick={() => setShowAll(p => !p)}>
                            {showAll ? 'Issues only' : `Show all (${feedHealth.length})`}
                        </Btn>
                    )}
                    <Btn size="sm" loading={loading} onClick={onRefresh}>Refresh</Btn>
                </div>
            </div>

            {feedHealth.length === 0 && !loading && (
                <div style={{
                    textAlign: 'center', padding: '40px 0', fontSize: 12, color: C.muted,
                    border: `0.5px dashed ${C.border}`, borderRadius: 8,
                }}>
                    No feed health data — start worker.py to begin ingestion
                </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                {visible.map(f => {
                    const isDisabled = f.disabled
                    const isFailing  = !isDisabled && f.consecutive_failures > 0
                    const isHealthy  = !isDisabled && !isFailing && f.last_success
                    const dot        = isDisabled ? C.red : isFailing ? C.amber : isHealthy ? C.green : C.muted
                    const is404      = f.last_error?.includes('404')

                    return (
                        <div key={f.url} style={{
                            display: 'flex', alignItems: 'center', gap: 10,
                            padding: '9px 12px', borderRadius: 8,
                            background: C.panelBg, border: `0.5px solid ${C.border}`,
                        }}>
                            <Dot color={dot} size={7} />
                            <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                    fontSize: 12, color: C.text, fontWeight: 500,
                                    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                }}>{f.name}</div>
                                {f.last_error && !is404 && (
                                    <div style={{
                                        fontSize: 10, color: C.red, marginTop: 2,
                                        whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                    }}>{f.last_error}</div>
                                )}
                            </div>
                            {is404 && <Badge color={C.red}>404</Badge>}
                            {isFailing && !is404 && <Badge color={C.amber}>{f.consecutive_failures}×</Badge>}
                            {isDisabled && <Badge color={C.red}>OFF</Badge>}
                            {f.last_success && (
                                <span style={{ fontSize: 10, color: C.faint, flexShrink: 0 }}>
                                    {relativeTime(f.last_success)}
                                </span>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

function Badge({ children, color }) {
    return (
        <span style={{
            fontSize: 9, padding: '1px 5px', borderRadius: 4, flexShrink: 0,
            background: color + '18', color,
            border: `0.5px solid ${color}40`,
            fontFamily: 'monospace', fontWeight: 700,
        }}>{children}</span>
    )
}

// ─── Settings: Add Feed Form ───────────────────────────────────────────────────

const FETCH_KINDS = ['rss', 'smart_scrape', 'nvd_cve_api', 'github_global_advisories']

/** Who may add feeds and delete feeds (case-insensitive match on designation from Employee). */
function canManageFeedSources(employee) {
    const raw = String(employee?.designation ?? '').trim().toLowerCase()
    return raw === 'super admin' || raw === 'delivery manager'
}

function AddFeedForm({ quadrants, onAdd, canManage }) {
    const quadrantOptions = quadrantNames(quadrants)
    const empty = () => ({ name: '', url: '', quadrant: quadrantOptions[0], fetch_kind: 'rss', priority: 5 })
    const [form,    setForm]    = useState(empty)
    const [saving,  setSaving]  = useState(false)
    const [error,   setError]   = useState('')
    const [open,    setOpen]    = useState(false)

    const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

    useEffect(() => {
        if (!quadrantOptions.includes(form.quadrant)) {
            setForm(f => ({ ...f, quadrant: quadrantOptions[0] }))
        }
    }, [form.quadrant, quadrants])

    const handleSubmit = async () => {
        if (!form.name.trim()) { setError('Name is required'); return }
        if (!form.url.trim())  { setError('URL is required');  return }
        const p = parseInt(form.priority, 10)
        if (isNaN(p) || p < 1 || p > 10) { setError('Priority must be 1–10'); return }
        setError(''); setSaving(true)
        try {
            await apiFetch(API.feeds, {
                method: 'POST',
                body: JSON.stringify({ ...form, url: form.url.trim(), name: form.name.trim(), priority: p }),
            })
            setForm(empty())
            setOpen(false)
            onAdd()
        } catch (e) {
            setError(e.message.includes('409') ? 'A feed with this URL already exists' : `Error: ${e.message}`)
        } finally { setSaving(false) }
    }

    const inputStyle = {
        background: 'var(--input-bg)', border: `0.5px solid ${C.border}`,
        borderRadius: 6, padding: '6px 10px', color: C.text,
        fontFamily: 'inherit', fontSize: 11, outline: 'none', width: '100%',
    }
    const selectStyle = { ...inputStyle, cursor: 'pointer' }

    if (!canManage) return null

    return (
        <div style={{ marginBottom: 16 }}>
            {!open ? (
                <Btn variant="primary" onClick={() => setOpen(true)}>+ Add Feed</Btn>
            ) : (
                <div style={{
                    background: C.panelBg, border: `0.5px solid ${C.accent}`,
                    borderRadius: 8, padding: 14,
                }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: C.accentText, marginBottom: 12, letterSpacing: '0.06em', textTransform: 'uppercase' }}>New Feed</div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 }}>
                        <div>
                            <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>Name</div>
                            <input value={form.name} onChange={e => set('name', e.target.value)} placeholder="OpenAI Blog" style={inputStyle} />
                        </div>
                        <div>
                            <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>URL</div>
                            <input value={form.url} onChange={e => set('url', e.target.value)} placeholder="https://…/feed.xml" style={inputStyle} />
                        </div>
                        <div>
                            <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>Quadrant</div>
                            <select value={form.quadrant} onChange={e => set('quadrant', e.target.value)} style={selectStyle}>
                                {quadrantOptions.map(q => <option key={q} value={q}>{q}</option>)}
                            </select>
                        </div>
                        <div>
                            <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>Fetch Kind</div>
                            <select value={form.fetch_kind} onChange={e => set('fetch_kind', e.target.value)} style={selectStyle}>
                                {FETCH_KINDS.map(k => <option key={k} value={k}>{k}</option>)}
                            </select>
                        </div>
                        <div>
                            <div style={{ fontSize: 10, color: C.muted, marginBottom: 4 }}>Priority (1–10)</div>
                            <input type="number" min={1} max={10} value={form.priority}
                                onChange={e => set('priority', e.target.value)} style={inputStyle} />
                        </div>
                    </div>
                    {error && <div style={{ fontSize: 11, color: C.red, marginBottom: 8 }}>{error}</div>}
                    <div style={{ display: 'flex', gap: 6 }}>
                        <Btn variant="primary" onClick={handleSubmit} loading={saving}>Save Feed</Btn>
                        <Btn variant="ghost" onClick={() => { setOpen(false); setError(''); setForm(empty()) }}>Cancel</Btn>
                    </div>
                </div>
            )}
        </div>
    )
}

// ─── Settings: Feed Manager table ─────────────────────────────────────────────

const QUADRANT_COLORS = {
    'Risks & Threats':       '#f87171',
    Engineering:             '#2563eb',
    'AI & Machine Learning': '#a78bfa',
    'Expert Context':        '#fb923c',
    'Frontier AI':           '#a78bfa',
}

function FeedManager({ feeds, quadrants, onFeedsChange, canManage }) {
    const [toggling,  setToggling]  = useState(null)
    const [deleting,  setDeleting]  = useState(null)
    const orderedQuadrants = quadrantNames(quadrants)

    const handleToggle = async (feed) => {
        setToggling(feed.id)
        try {
            await apiFetch(`${API.feeds}/${feed.id}`, {
                method: 'PATCH',
                body: JSON.stringify({ is_active: !feed.is_active }),
            })
            onFeedsChange()
        } catch (e) { console.error(e) }
        finally { setToggling(null) }
    }

    const handleDelete = async (feed) => {
        if (!confirm(`Delete "${feed.name}"? This cannot be undone.`)) return
        setDeleting(feed.id)
        try {
            await fetch(`${API.feeds}/${feed.id}`, { method: 'DELETE' })
            onFeedsChange()
        } catch (e) { console.error(e) }
        finally { setDeleting(null) }
    }

    if (!feeds.length) {
        return (
            <div style={{ textAlign: 'center', padding: '24px 0', color: C.muted, fontSize: 12 }}>
                {canManage ? 'No feeds configured. Add one above.' : 'No feeds configured.'}
            </div>
        )
    }

    const grouped = orderedQuadrants.reduce((acc, q) => {
        acc[q] = feeds.filter(f => normalizeQuadrant(f.quadrant) === q)
        return acc
    }, {})

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {orderedQuadrants.map(q => {
                const group = grouped[q]
                if (!group.length) return null
                const color = QUADRANT_COLORS[q] || C.muted
                return (
                    <div key={q}>
                        <div style={{
                            display: 'flex', alignItems: 'center', gap: 8,
                            marginBottom: 6, paddingBottom: 6,
                            borderBottom: `0.5px solid ${C.border}`,
                        }}>
                            <div style={{ width: 3, height: 14, borderRadius: 2, background: color, flexShrink: 0 }} />
                            <span style={{ fontSize: 10, fontWeight: 700, color, letterSpacing: '0.07em', textTransform: 'uppercase' }}>{q}</span>
                            <span style={{ fontSize: 10, color: C.faint }}>{group.length} feed{group.length !== 1 ? 's' : ''}</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                            {group.map(feed => (
                                <div key={feed.id} style={{
                                    display: 'flex', alignItems: 'center', gap: 10,
                                    padding: '8px 12px', borderRadius: 6,
                                    background: C.panelBg,
                                    border: `0.5px solid ${feed.is_active ? C.border : 'var(--feed-inactive-border)'}`,
                                    opacity: feed.is_active ? 1 : 0.45,
                                    transition: 'opacity 200ms ease',
                                }}>
                                    {/* Priority dot */}
                                    <div style={{
                                        width: 6, height: 6, borderRadius: '50%', flexShrink: 0,
                                        background: feed.priority >= 9 ? C.red : feed.priority >= 7 ? C.amber : C.muted,
                                    }} title={`Priority ${feed.priority}`} />

                                    {/* Name + URL */}
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{
                                            fontSize: 12, color: C.text, fontWeight: 500,
                                            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                        }}>{feed.name}</div>
                                        <div style={{
                                            fontSize: 10, color: C.faint, marginTop: 1,
                                            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                        }}>{feed.url}</div>
                                    </div>

                                    {/* Fetch kind badge */}
                                    <Badge color={C.muted}>{feed.fetch_kind}</Badge>

                                    {/* Priority */}
                                    <span style={{ fontSize: 10, color: C.muted, fontFamily: 'monospace', width: 14, textAlign: 'right', flexShrink: 0 }}>
                                        {feed.priority}
                                    </span>

                                    {/* Active toggle */}
                                    <Toggle
                                        checked={!!feed.is_active}
                                        onChange={() => handleToggle(feed)}
                                        disabled={toggling === feed.id}
                                    />

                                    {canManage && (
                                        <button
                                            onClick={() => handleDelete(feed)}
                                            disabled={deleting === feed.id}
                                            title="Delete feed"
                                            style={{
                                                background: 'none', border: 'none', cursor: 'pointer',
                                                color: C.muted, fontSize: 14, lineHeight: 1,
                                                padding: '0 2px', transition: 'color 150ms', flexShrink: 0,
                                            }}
                                            onMouseEnter={e => e.currentTarget.style.color = C.red}
                                            onMouseLeave={e => e.currentTarget.style.color = C.muted}
                                        >
                                            {deleting === feed.id ? <Spinner size={10} /> : '×'}
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                )
            })}
        </div>
    )
}

function ManageQuadrants({ quadrants, feeds, onQuadrantsChange, onFeedsChange, canManageFeeds }) {
    const [name, setName] = useState('')
    const [saving, setSaving] = useState(false)
    const [deleting, setDeleting] = useState(null)
    const [error, setError] = useState('')

    const handleAdd = async () => {
        const trimmed = name.trim()
        if (!trimmed) { setError('Name is required'); return }
        setError(''); setSaving(true)
        try {
            await apiFetch(API.quadrants, {
                method: 'POST',
                body: JSON.stringify({ name: trimmed }),
            })
            setName('')
            onQuadrantsChange()
        } catch (e) {
            setError(e.message.includes('409') ? 'A quadrant with this name already exists' : `Error: ${e.message}`)
        } finally { setSaving(false) }
    }

    const handleDelete = async quadrant => {
        const inUse = feeds.some(f => normalizeQuadrant(f.quadrant) === quadrant.name)
        if (inUse) { setError('Move or delete feeds assigned to this quadrant first'); return }
        if (!confirm(`Delete "${quadrant.name}"?`)) return
        setError(''); setDeleting(quadrant.id)
        try {
            const r = await fetch(`${API.quadrants}/${quadrant.id}`, { method: 'DELETE' })
            if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
            onQuadrantsChange()
            onFeedsChange()
        } catch (e) {
            setError(e.message.includes('409') ? 'Move or delete feeds assigned to this quadrant first' : `Error: ${e.message}`)
        } finally { setDeleting(null) }
    }

    return (
        <div style={{ marginBottom: 32 }}>
            <SectionTitle>Manage Quadrants</SectionTitle>
            {!canManageFeeds && (
                <div style={{ fontSize: 10, color: C.faint, marginBottom: 10, lineHeight: 1.45 }}>
                    Adding or removing quadrants is limited to Super Admin or Delivery Manager.
                </div>
            )}
            {canManageFeeds && (
                <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                    <input
                        value={name}
                        onChange={e => { setName(e.target.value); setError('') }}
                        onKeyDown={e => e.key === 'Enter' && handleAdd()}
                        placeholder="New quadrant name"
                        style={{
                            flex: 1, background: C.panelBg,
                            border: `0.5px solid ${error ? C.red : C.border}`,
                            borderRadius: 6, padding: '7px 11px', color: C.text,
                            fontFamily: 'inherit', fontSize: 12, outline: 'none',
                        }}
                    />
                    <Btn onClick={handleAdd} variant="primary" loading={saving}>Add</Btn>
                </div>
            )}
            {error && <div style={{ fontSize: 11, color: C.red, marginBottom: 8 }}>{error}</div>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {quadrants.map(q => {
                    const count = feeds.filter(f => normalizeQuadrant(f.quadrant) === q.name).length
                    const color = QUADRANT_COLORS[q.name] || catColor(q.name)
                    return (
                        <div key={q.id || q.name} style={{
                            display: 'flex', alignItems: 'center', gap: 10,
                            background: C.panelBg, border: `0.5px solid ${C.border}`,
                            borderRadius: 6, padding: '7px 11px',
                        }}>
                            <Dot color={color} size={6} />
                            <span style={{ flex: 1, fontSize: 12, color: C.text }}>{q.name}</span>
                            <span style={{ fontSize: 10, color: C.faint }}>{count} feed{count !== 1 ? 's' : ''}</span>
                            {canManageFeeds && (
                                <button
                                    onClick={() => handleDelete(q)}
                                    disabled={deleting === q.id || count > 0}
                                    title={count > 0 ? 'Remove assigned feeds before deleting' : 'Delete quadrant'}
                                    style={{
                                        background: 'none', border: 'none',
                                        cursor: count > 0 ? 'not-allowed' : 'pointer',
                                        color: count > 0 ? C.faint : C.muted,
                                        fontSize: 14, lineHeight: 1, padding: '0 2px',
                                    }}
                                    onMouseEnter={e => { if (!count) e.currentTarget.style.color = C.red }}
                                    onMouseLeave={e => { e.currentTarget.style.color = count > 0 ? C.faint : C.muted }}
                                >
                                    {deleting === q.id ? <Spinner size={10} /> : '×'}
                                </button>
                            )}
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

// ─── Settings view ────────────────────────────────────────────────────────────

function SettingsView({ feeds, quadrants, onFeedsChange, onQuadrantsChange, recipients, onUpdateRecipients, sessionEmployee }) {
    const canManageFeeds = canManageFeedSources(sessionEmployee)
    const [input,    setInput]    = useState('')
    const [adding,   setAdding]   = useState(false)
    const [removing, setRemoving] = useState(null)
    const [recError, setRecError] = useState('')

    const validEmail = e => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e)

    const handleAddRecipient = async () => {
        const email = input.trim()
        if (!validEmail(email)) { setRecError('Invalid email address'); return }
        setRecError(''); setAdding(true)
        try {
            const data = await apiFetch(API.emails, { method: 'POST', body: JSON.stringify({ email }) })
            onUpdateRecipients(data.recipients || [])
            setInput('')
        } catch { setRecError('Failed to add recipient') }
        finally { setAdding(false) }
    }

    const handleRemoveRecipient = async email => {
        setRemoving(email)
        try {
            const data = await apiFetch(API.emails, { method: 'DELETE', body: JSON.stringify({ email }) })
            onUpdateRecipients(data.recipients || [])
        } catch (e) { console.error(e) }
        finally { setRemoving(null) }
    }

    return (
        <div style={{ flex: 1, overflowY: 'auto', padding: 20 }}>
            <ManageQuadrants
                quadrants={quadrants}
                feeds={feeds}
                onQuadrantsChange={onQuadrantsChange}
                onFeedsChange={onFeedsChange}
                canManageFeeds={canManageFeeds}
            />

            {/* ── Feed Manager ─────────────────────────────────────────────── */}
            <SectionTitle>Feed Sources</SectionTitle>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 14 }}>
                {feeds.length} feed{feeds.length !== 1 ? 's' : ''} configured ·
                {' '}{feeds.filter(f => f.is_active).length} active
            </div>
            {!canManageFeeds && (
                <div style={{ fontSize: 10, color: C.faint, marginBottom: 12, lineHeight: 1.45 }}>
                    Adding or deleting feeds is limited to Super Admin or Delivery Manager.
                </div>
            )}

            <AddFeedForm quadrants={quadrants} onAdd={onFeedsChange} canManage={canManageFeeds} />

            <div style={{ marginBottom: 32 }}>
                <FeedManager feeds={feeds} quadrants={quadrants} onFeedsChange={onFeedsChange} canManage={canManageFeeds} />
            </div>

            {/* ── Email Recipients ─────────────────────────────────────────── */}
            <SectionTitle>Email Recipients</SectionTitle>
            <div style={{ fontSize: 11, color: C.muted, marginBottom: 12 }}>
                {recipients.length} address{recipients.length !== 1 ? 'es' : ''} configured
            </div>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
                <input
                    value={input}
                    onChange={e => { setInput(e.target.value); setRecError('') }}
                    onKeyDown={e => e.key === 'Enter' && handleAddRecipient()}
                    placeholder="name@company.com"
                    style={{
                        flex: 1, background: C.panelBg,
                        border: `0.5px solid ${recError ? C.red : C.border}`,
                        borderRadius: 6, padding: '7px 11px', color: C.text,
                        fontFamily: 'inherit', fontSize: 12, outline: 'none',
                    }}
                />
                <Btn onClick={handleAddRecipient} variant="primary" loading={adding}>Add</Btn>
            </div>
            {recError && <div style={{ fontSize: 11, color: C.red, marginBottom: 8 }}>{recError}</div>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
                {recipients.length === 0 && (
                    <div style={{ padding: '12px 0', textAlign: 'center', fontSize: 12, color: C.muted }}>
                        No recipients configured
                    </div>
                )}
                {recipients.map(email => (
                    <div key={email} style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        background: C.panelBg, border: `0.5px solid ${C.border}`,
                        borderRadius: 6, padding: '7px 11px',
                    }}>
                        <span style={{
                            fontSize: 12, color: C.muted,
                            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '85%',
                        }}>{email}</span>
                        <button
                            onClick={() => handleRemoveRecipient(email)}
                            disabled={removing === email}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: C.muted, fontSize: 16, lineHeight: 1, padding: '0 2px', transition: 'color 150ms' }}
                            onMouseEnter={e => e.currentTarget.style.color = C.red}
                            onMouseLeave={e => e.currentTarget.style.color = C.muted}
                        >
                            {removing === email ? <Spinner size={10} /> : '×'}
                        </button>
                    </div>
                ))}
            </div>
        </div>
    )
}

function SectionTitle({ children }) {
    return (
        <div style={{
            fontSize: 10, fontWeight: 700, color: C.muted,
            letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 10,
        }}>{children}</div>
    )
}

// ─── Right panel ──────────────────────────────────────────────────────────────

function RightPanel({ statusData, feedHealth, recipients, apiError, fetched, onClose }) {
    const counts  = statusData?.articles
    const feeds   = statusData?.feeds
    const ingest  = statusData?.ingestion
    const healthy = feeds?.healthy ?? 0
    const total   = feeds?.total   ?? 0
    const pct     = total > 0 ? (healthy / total) * 100 : 0
    const feedOk  = (feeds?.disabled ?? 0) === 0

    const statusRows = [
        { label: 'Ingestion',  value: 'every 30 min',  color: '#60a5fa' },
        { label: 'SEC digest', value: '9am & 6pm IST', color: C.red     },
        { label: 'DEV digest', value: '8am IST',       color: C.green   },
        { label: 'Last run',   value: ingest?.last_run ? relativeTime(ingest.last_run) : '—', color: C.muted },
    ]

    // Mini feed health: issues first, then healthy, max 5
    const miniFeeds = [
        ...feedHealth.filter(f => f.disabled || f.consecutive_failures > 0),
        ...feedHealth.filter(f => !f.disabled && !f.consecutive_failures && f.last_success),
    ].slice(0, 6)

    return (
        <aside className="fa-right-panel">
            <div className="fa-right-panel-header">
                <button
                    type="button"
                    className="fa-right-panel-close"
                    onClick={onClose}
                    title="Close panel"
                    aria-label="Close panel"
                >
                    <IconChevronRight size={18} />
                </button>
            </div>

            {/* System Status */}
            <div style={{ padding: '0 12px 14px', borderBottom: `0.5px solid ${C.border}` }}>
                <SectionTitle>System Status</SectionTitle>

                {!fetched && <div style={{ color: C.muted }}>Loading…</div>}
                {fetched && apiError && !statusData && (
                    <div style={{ color: C.amber }}>API unreachable</div>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                    {statusRows.map(({ label, value, color }) => (
                        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 4 }}>
                            <span style={{ color: C.muted, flexShrink: 0 }}>{label}</span>
                            <span style={{ color, fontWeight: 600, fontSize: 10, textAlign: 'right' }}>{value}</span>
                        </div>
                    ))}
                </div>

                {/* Feeds healthy progress bar */}
                {feeds && (
                    <div style={{ marginTop: 12 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                            <span style={{ color: C.muted }}>Feeds healthy</span>
                            <span style={{ color: feedOk ? C.green : C.amber, fontWeight: 600 }}>
                                {healthy}/{total}
                            </span>
                        </div>
                        <div style={{ height: 3, background: C.faint, borderRadius: 2 }}>
                            <div style={{
                                height: '100%', borderRadius: 2,
                                background: feedOk ? C.green : C.amber,
                                width: `${pct}%`,
                                transition: 'width 400ms ease',
                            }} />
                        </div>
                    </div>
                )}
            </div>

            {/* Recipients */}
            {recipients.length > 0 && (
                <div style={{ padding: '12px', borderBottom: `0.5px solid ${C.border}` }}>
                    <SectionTitle>Recipients</SectionTitle>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {recipients.slice(0, 5).map(email => (
                            <div key={email} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                                <div style={{
                                    width: 22, height: 22, borderRadius: '50%',
                                    background: 'rgba(79,95,255,0.2)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    fontSize: 8, fontWeight: 700, color: C.accentText,
                                    letterSpacing: '0.03em', flexShrink: 0,
                                }}>
                                    {email.slice(0, 2).toUpperCase()}
                                </div>
                                <span style={{
                                    fontSize: 10, color: C.muted,
                                    overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                }}>{trunc(email, 18)}</span>
                            </div>
                        ))}
                        {recipients.length > 5 && (
                            <span style={{ fontSize: 10, color: C.faint }}>
                                +{recipients.length - 5} more
                            </span>
                        )}
                    </div>
                </div>
            )}

            {/* Feed Health mini-list */}
            {miniFeeds.length > 0 && (
                <div style={{ padding: '12px' }}>
                    <SectionTitle>Feed Health</SectionTitle>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {miniFeeds.map(f => {
                            const isDisabled = f.disabled
                            const isFailing  = !isDisabled && f.consecutive_failures > 0
                            const isHealthy  = !isDisabled && !isFailing && f.last_success
                            const dot        = isDisabled ? C.red : isFailing ? C.amber : isHealthy ? C.green : C.muted
                            const is404      = f.last_error?.includes('404')
                            return (
                                <div key={f.url} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                                    <Dot color={dot} size={5} />
                                    <span style={{
                                        flex: 1, fontSize: 10, color: C.muted,
                                        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                                    }}>{trunc(f.name, 17)}</span>
                                    {is404 && <Badge color={C.red}>404</Badge>}
                                    {isFailing && !is404 && <Badge color={C.amber}>{f.consecutive_failures}×</Badge>}
                                    {isDisabled && <Badge color={C.red}>OFF</Badge>}
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}
        </aside>
    )
}

// ─── Root app ─────────────────────────────────────────────────────────────────

export default function App() {
    // const [sessionEmployee, setSessionEmployee] = useState(() => readStoredEmployee())
    const [sessionEmployee] = useState(() => DEV_BYPASS_SESSION)
    const [statusData,    setStatusData]    = useState(null)
    const [feeds,         setFeeds]         = useState([])
    const [quadrants,     setQuadrants]     = useState([])
    const [recipients,    setRecipients]    = useState([])
    const [articles,      setArticles]      = useState([])
    const [feedHealth,    setFeedHealth]    = useState([])
    const [artLoading,    setArtLoading]    = useState(false)
    const [healthLoading, setHealthLoading] = useState(false)
    const [apiError,      setApiError]      = useState(null)
    const [fetched,       setFetched]       = useState(false)
    const [selectedCat,   setSelectedCat]   = useState(DEFAULT_QUADRANTS[0])
    const [typeFilter,    setTypeFilter]    = useState('All')
    const [activeView,    setActiveView]    = useState('articles')
    const [drawerCollapsed, setDrawerCollapsed] = useState(false)
    const [darkMode, setDarkMode] = useState(() => {
        if (typeof window === 'undefined') return false
        return localStorage.getItem(THEME_STORAGE_KEY) === 'dark'
    })
    const [rightPanelOpen, setRightPanelOpen] = useState(true)
    const rightPanelTimersRef = useRef({ short: null, max: null })
    const rightPanelManualOpenRef = useRef(false)

    const clearRightPanelTimers = useCallback(() => {
        const { short, max } = rightPanelTimersRef.current
        if (short) clearTimeout(short)
        if (max) clearTimeout(max)
        rightPanelTimersRef.current = { short: null, max: null }
    }, [])

    const closeRightPanel = useCallback(() => {
        clearRightPanelTimers()
        setRightPanelOpen(false)
    }, [clearRightPanelTimers])

    const scheduleRightPanelAutoClose = useCallback(({ shortDelay = false } = {}) => {
        clearRightPanelTimers()
        if (shortDelay) {
            rightPanelTimersRef.current.short = setTimeout(() => {
                setRightPanelOpen(false)
                clearRightPanelTimers()
            }, RIGHT_PANEL_INITIAL_MS)
        }
        rightPanelTimersRef.current.max = setTimeout(() => {
            setRightPanelOpen(false)
            clearRightPanelTimers()
        }, RIGHT_PANEL_MAX_MS)
    }, [clearRightPanelTimers])

    const openRightPanel = useCallback(() => {
        setRightPanelOpen(true)
        const isFirstManual = !rightPanelManualOpenRef.current
        rightPanelManualOpenRef.current = true
        scheduleRightPanelAutoClose({ shortDelay: isFirstManual })
    }, [scheduleRightPanelAutoClose])

    useEffect(() => {
        const theme = darkMode ? 'dark' : 'light'
        document.documentElement.setAttribute('data-theme', theme)
        localStorage.setItem(THEME_STORAGE_KEY, theme)
    }, [darkMode])

    useEffect(() => {
        scheduleRightPanelAutoClose({ shortDelay: true })
        return clearRightPanelTimers
    }, [scheduleRightPanelAutoClose, clearRightPanelTimers])

    // const handleLogout = useCallback(async () => {
    //     clearStoredEmployee()
    //     setSessionEmployee(null)
    //     try {
    //         const msal = getMsalInstance()
    //         await msal.initialize()
    //         await msal.logoutPopup({ postLogoutRedirectUri: getMsalRedirectUri() })
    //     } catch {
    //         /* ignore */
    //     }
    // }, [])
    const handleLogout = useCallback(() => {}, [])

    const fetchStatus = useCallback(async () => {
        try { setStatusData(await apiFetch(API.status)); setApiError(null) }
        catch (e) { setApiError(`${e.message}`) }
        finally { setFetched(true) }
    }, [])

    const fetchRecipients = useCallback(async () => {
        try { const d = await apiFetch(API.emails); setRecipients(d.recipients || []) }
        catch (e) { console.error(e) }
    }, [])

    const fetchFeeds = useCallback(async () => {
        try { const d = await apiFetch(API.feeds); setFeeds(Array.isArray(d) ? d : []) }
        catch (e) { console.error(e) }
    }, [])

    const fetchQuadrants = useCallback(async () => {
        try { const d = await apiFetch(API.quadrants); setQuadrants(Array.isArray(d) ? d : []) }
        catch (e) { console.error(e); setQuadrants(DEFAULT_QUADRANTS.map((name, idx) => ({ id: idx + 1, name, display_order: idx + 1 }))) }
    }, [])

    const fetchArticles = useCallback(async () => {
        setArtLoading(true)
        try { const d = await apiFetch(API.articles); setArticles(Array.isArray(d) ? d : []) }
        catch (e) { console.error(e) }
        finally { setArtLoading(false) }
    }, [])

    const fetchFeedHealth = useCallback(async () => {
        setHealthLoading(true)
        try { setFeedHealth(await apiFetch(API.feedsHealth)) }
        catch (e) { console.error(e) }
        finally { setHealthLoading(false) }
    }, [])

    useEffect(() => {
        if (!sessionEmployee) return
        fetchStatus(); fetchRecipients(); fetchArticles(); fetchFeedHealth(); fetchQuadrants()
        const t = setInterval(fetchStatus, 30_000)
        return () => clearInterval(t)
    }, [sessionEmployee, fetchStatus, fetchRecipients, fetchArticles, fetchFeedHealth, fetchQuadrants])

    useEffect(() => {
        const available = quadrantNames(quadrants)
        if (!available.includes(selectedCat)) setSelectedCat(available[0])
    }, [quadrants, selectedCat])

    const handleView = view => {
        setActiveView(view)
        if (view === 'feedhealth') fetchFeedHealth()
        if (view === 'settings')  { fetchFeeds(); fetchQuadrants(); fetchRecipients() }
    }

    // if (!sessionEmployee) {
    //     return <LoginPage onSignedIn={setSessionEmployee} />
    // }

    return (
        <div className="fa-app" data-theme={darkMode ? 'dark' : 'light'}>
            <style>{`
                * { box-sizing: border-box; margin: 0; padding: 0; }
                @keyframes spin { to { transform: rotate(360deg) } }
                body { background: var(--page-bg); color: var(--text); -webkit-font-smoothing: antialiased; }
                input { font-family: inherit; }
                select, option { background: var(--input-bg); color: var(--input-text); }
                button { font-family: inherit; }
                ::-webkit-scrollbar { width: 4px; height: 4px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: var(--scrollbar-thumb); border-radius: 2px; }
                ::-webkit-scrollbar-thumb:hover { background: var(--scrollbar-thumb-hover); }
            `}</style>

            <LayoutHeader
                sessionEmployee={sessionEmployee}
                onLogout={handleLogout}
                collapsed={drawerCollapsed}
                onToggleDrawer={() => setDrawerCollapsed(c => !c)}
                darkMode={darkMode}
                onToggleDarkMode={() => setDarkMode(d => !d)}
            />
            <div className="fa-body-row">
                <Sidebar
                    articles={articles}
                    quadrants={quadrants}
                    selectedCat={selectedCat}
                    onSelectCat={setSelectedCat}
                    activeView={activeView}
                    onView={handleView}
                    collapsed={drawerCollapsed}
                />

                <div className="fa-main">
                    <LayoutBreadcrumb activeView={activeView} selectedCat={selectedCat} />
                    <div className="fa-content-card">
                        {activeView === 'articles' && (
                            <>
                                <Topbar
                                    selectedCat={selectedCat}
                                    typeFilter={typeFilter}
                                    onTypeFilter={setTypeFilter}
                                    statusData={statusData}
                                />
                                <ArticleList
                                    articles={articles}
                                    selectedCat={selectedCat}
                                    typeFilter={typeFilter}
                                    loading={artLoading}
                                />
                            </>
                        )}

                        {activeView === 'feedhealth' && (
                            <FeedHealthView
                                feedHealth={feedHealth}
                                loading={healthLoading}
                                onRefresh={fetchFeedHealth}
                            />
                        )}

                        {activeView === 'settings' && (
                            <SettingsView
                                feeds={feeds}
                                quadrants={quadrants}
                                onFeedsChange={fetchFeeds}
                                onQuadrantsChange={fetchQuadrants}
                                recipients={recipients}
                                onUpdateRecipients={setRecipients}
                                sessionEmployee={sessionEmployee}
                            />
                        )}
                    </div>
                    <LayoutFooter />
                </div>

                <div className="fa-right-panel-wrap">
                    {rightPanelOpen && (
                        <RightPanel
                            statusData={statusData}
                            feedHealth={feedHealth}
                            recipients={recipients}
                            apiError={apiError}
                            fetched={fetched}
                            onClose={closeRightPanel}
                        />
                    )}
                    {!rightPanelOpen && (
                        <button
                            type="button"
                            className="fa-right-panel-open"
                            onClick={openRightPanel}
                            title="Open status panel"
                            aria-label="Open status panel"
                        >
                            <IconChevronLeft size={18} />
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}
