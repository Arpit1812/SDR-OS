import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiUrl } from '../utils/api'
import './LinkedInScraper.css'

function LinkedInScraper() {
  const navigate = useNavigate()
  const location = useLocation()
  const [userId, setUserId] = useState(null)

  // Scraper status
  const [scraperStatus, setScraperStatus] = useState({ running: false })
  const [launching, setLaunching] = useState(false)

  // ICP Config
  const [config, setConfig] = useState(null)
  const [configLoading, setConfigLoading] = useState(true)
  const [configEditing, setConfigEditing] = useState(false)
  const [configDraft, setConfigDraft] = useState(null)
  const [savingConfig, setSavingConfig] = useState(false)

  // Leads
  const [leads, setLeads] = useState([])
  const [leadsLoading, setLeadsLoading] = useState(false)
  const [leadFiles, setLeadFiles] = useState([])
  const [selectedFile, setSelectedFile] = useState('leads.json')
  const [selectedLeads, setSelectedLeads] = useState(new Set())
  const [importing, setImporting] = useState(false)
  const [ingesting, setIngesting] = useState(false)

  // Stored leads from MongoDB
  const [storedLeads, setStoredLeads] = useState([])
  const [storedTotal, setStoredTotal] = useState(0)
  const [storedPage, setStoredPage] = useState(1)
  const [storedLoading, setStoredLoading] = useState(false)

  // Tab state
  const [activeTab, setActiveTab] = useState('scraped') // 'scraped' | 'stored'

  // Logs
  const [logs, setLogs] = useState([])
  const [showLogs, setShowLogs] = useState(false)

  // Run Stats
  const [runStats, setRunStats] = useState(null)

  // Message
  const [message, setMessage] = useState(null)

  useEffect(() => {
    const userData = location.state?.userData
    const savedUser = localStorage.getItem('user')
    if (userData?.id) {
      setUserId(userData.id)
    } else if (savedUser) {
      const user = JSON.parse(savedUser)
      setUserId(user.id)
    } else {
      navigate('/')
    }
  }, [navigate, location])

  const showMessage = (text, type = 'success') => {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 4000)
  }

  // ── Load data ───────────────────────────────────────────────

  const loadStatus = useCallback(async () => {
    try {
      const res = await fetch(apiUrl('/api/scraper/status'))
      if (res.ok) setScraperStatus(await res.json())
    } catch (e) { console.error('Status error:', e) }
  }, [])

  const loadConfig = useCallback(async () => {
    setConfigLoading(true)
    try {
      const res = await fetch(apiUrl('/api/scraper/config'))
      if (res.ok) {
        const data = await res.json()
        setConfig(data)
        setConfigDraft(data)
      }
    } catch (e) { console.error('Config error:', e) }
    finally { setConfigLoading(false) }
  }, [])

  const loadLeads = useCallback(async (file) => {
    const source = file || selectedFile
    setLeadsLoading(true)
    try {
      const url = source && source !== 'leads.json'
        ? apiUrl(`/api/scraper/leads?source=${encodeURIComponent(source)}`)
        : apiUrl('/api/scraper/leads')
      const res = await fetch(url)
      if (res.ok) {
        const data = await res.json()
        setLeads(data.leads || [])
      }
    } catch (e) { console.error('Leads error:', e) }
    finally { setLeadsLoading(false) }
  }, [selectedFile])

  const loadLeadFiles = useCallback(async () => {
    try {
      const res = await fetch(apiUrl('/api/scraper/leads/files'))
      if (res.ok) {
        const data = await res.json()
        setLeadFiles(data.files || [])
      }
    } catch (e) { console.error('Files error:', e) }
  }, [])

  const loadStoredLeads = useCallback(async (page = 1) => {
    if (!userId) return
    setStoredLoading(true)
    try {
      const res = await fetch(apiUrl(`/api/scraper/leads/stored?page=${page}&page_size=50`), {
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        const data = await res.json()
        setStoredLeads(data.leads || [])
        setStoredTotal(data.total || 0)
        setStoredPage(page)
      }
    } catch (e) { console.error('Stored leads error:', e) }
    finally { setStoredLoading(false) }
  }, [userId])

  const loadLogs = useCallback(async () => {
    try {
      const res = await fetch(apiUrl('/api/scraper/logs?lines=80'))
      if (res.ok) {
        const data = await res.json()
        setLogs(data.lines || [])
      }
    } catch (e) { console.error('Logs error:', e) }
  }, [])

  const loadRunStats = useCallback(async () => {
    try {
      const res = await fetch(apiUrl('/api/scraper/run-stats'))
      if (res.ok) {
        const data = await res.json()
        setRunStats(data.stats)
      }
    } catch (e) { console.error('Run stats error:', e) }
  }, [])

  useEffect(() => {
    loadStatus()
    loadConfig()
    loadLeads()
    loadLeadFiles()
    loadRunStats()
  }, [loadStatus, loadConfig, loadLeads, loadLeadFiles, loadRunStats])

  // Reload leads when selected file changes
  useEffect(() => {
    loadLeads(selectedFile)
  }, [selectedFile])

  useEffect(() => {
    if (userId && activeTab === 'stored') loadStoredLeads(1)
  }, [userId, activeTab, loadStoredLeads])

  // Poll status while running, reload stats when scraper stops
  useEffect(() => {
    if (!scraperStatus.running) return
    const interval = setInterval(loadStatus, 5000)
    return () => {
      clearInterval(interval)
      // Reload stats + leads when scraper finishes
      loadRunStats()
      loadLeads(selectedFile)
      loadLeadFiles()
    }
  }, [scraperStatus.running, loadStatus, loadRunStats, loadLeads, loadLeadFiles, selectedFile])

  // ── Actions ─────────────────────────────────────────────────

  const handleLaunch = async (mode) => {
    setLaunching(true)
    try {
      const res = await fetch(apiUrl(`/api/scraper/run?mode=${mode}`), { method: 'POST' })
      const data = await res.json()
      if (res.ok) {
        showMessage(`Scraper launched (${mode} mode) — PID ${data.pid}`)
        loadStatus()
      } else {
        showMessage(data.detail || 'Failed to launch', 'error')
      }
    } catch (e) { showMessage('Network error', 'error') }
    finally { setLaunching(false) }
  }

  const handleStop = async () => {
    try {
      const res = await fetch(apiUrl('/api/scraper/stop'), { method: 'POST' })
      if (res.ok) {
        showMessage('Scraper stopped')
        loadStatus()
      }
    } catch (e) { showMessage('Failed to stop', 'error') }
  }

  const handleSaveConfig = async () => {
    setSavingConfig(true)
    try {
      const res = await fetch(apiUrl('/api/scraper/config'), {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(configDraft)
      })
      if (res.ok) {
        showMessage('Configuration saved')
        setConfig(configDraft)
        setConfigEditing(false)
        loadConfig()
      } else {
        showMessage('Failed to save config', 'error')
      }
    } catch (e) { showMessage('Network error saving config', 'error') }
    finally { setSavingConfig(false) }
  }

  const handleUploadResume = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setSavingConfig(true)
    const formData = new FormData()
    formData.append('file', file)
    try {
      const res = await fetch(apiUrl('/api/scraper/config/resume'), {
        method: 'POST',
        headers: userId ? { 'X-User-Id': userId } : {},
        body: formData
      })
      if (res.ok) {
        showMessage('Resume uploaded successfully')
        loadConfig()
      } else {
        showMessage('Failed to upload resume', 'error')
      }
    } catch (e) {
      showMessage('Network error uploading resume', 'error')
    } finally {
      setSavingConfig(false)
      // reset file input
      e.target.value = ''
    }
  }

  const toggleOnSite = (mode) => {
    setConfigDraft(prev => {
      const modes = prev.on_site || []
      if (modes.includes(mode)) return { ...prev, on_site: modes.filter(m => m !== mode) }
      return { ...prev, on_site: [...modes, mode] }
    })
  }

  const handleIngest = async () => {
    if (!userId) return
    setIngesting(true)
    try {
      const source = selectedFile || 'leads.json'
      const res = await fetch(apiUrl(`/api/scraper/leads/ingest?source=${encodeURIComponent(source)}`), {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })
      if (res.ok) {
        const data = await res.json()
        showMessage(`Ingested: ${data.imported} imported, ${data.skipped} skipped`)
        loadStoredLeads(1)
      } else {
        showMessage('Failed to ingest leads', 'error')
      }
    } catch (e) { showMessage('Network error', 'error') }
    finally { setIngesting(false) }
  }

  const handleImportToContacts = async () => {
    if (!userId || selectedLeads.size === 0) return
    setImporting(true)
    try {
      const res = await fetch(apiUrl('/api/scraper/leads/import-to-contacts'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify(Array.from(selectedLeads))
      })
      if (res.ok) {
        const data = await res.json()
        showMessage(`Imported ${data.imported} leads to contacts`)
        setSelectedLeads(new Set())
        loadStoredLeads(storedPage)
      } else {
        showMessage('Failed to import', 'error')
      }
    } catch (e) { showMessage('Network error', 'error') }
    finally { setImporting(false) }
  }

  const toggleLead = (id) => {
    setSelectedLeads(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const selectAllStored = () => {
    if (selectedLeads.size === storedLeads.length) {
      setSelectedLeads(new Set())
    } else {
      setSelectedLeads(new Set(storedLeads.map(l => l.id)))
    }
  }

  const updateConfigList = (key, value) => {
    setConfigDraft(prev => ({
      ...prev,
      [key]: value.split('\n').map(s => s.trim()).filter(Boolean)
    }))
  }

  return (
    <div className="scraper-page">
      {/* Message Banner */}
      {message && (
        <div className={`scraper-message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="page-header">
        <h1 className="page-title">LinkedIn Scraper</h1>
        <p className="page-subtitle">Scrape LinkedIn for ICP leads and import them into your contacts</p>
      </div>

      {/* ── Control Panel ──────────────────────────────── */}
      <section className="scraper-section">
        <div className="section-header">
          <h2>Scraper Control</h2>
          <div className={`status-badge ${scraperStatus.running ? 'running' : 'stopped'}`}>
            <span className="status-dot"></span>
            {scraperStatus.running ? `Running (PID ${scraperStatus.pid})` : 'Stopped'}
          </div>
        </div>
        <div className="control-actions">
          {!scraperStatus.running ? (
            <>
              <button
                className="btn btn-primary"
                onClick={() => handleLaunch('jobs')}
                disabled={launching}
              >
                {launching ? 'Launching...' : '🔍 Launch Job Scraper'}
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => handleLaunch('posts')}
                disabled={launching}
              >
                {launching ? 'Launching...' : '📝 Launch Posts Scraper'}
              </button>
            </>
          ) : (
            <button className="btn btn-danger" onClick={handleStop}>
              ⏹ Stop Scraper
            </button>
          )}
          <button
            className="btn btn-outline"
            onClick={() => { setShowLogs(!showLogs); if (!showLogs) loadLogs() }}
          >
            📋 {showLogs ? 'Hide' : 'Show'} Logs
          </button>
          <button className="btn btn-outline" onClick={() => { loadLeads(); loadStatus(); loadLeadFiles() }}>
            🔄 Refresh
          </button>
        </div>

        {showLogs && (
          <div className="logs-container">
            <pre className="logs-content">
              {logs.length > 0 ? logs.join('\n') : 'No logs available'}
            </pre>
          </div>
        )}
      </section>

      {/* ── Run Statistics ────────────────────────────── */}
      <section className="scraper-section">
        <div className="section-header">
          <h2>Last Run Statistics</h2>
          {runStats?.timestamp && <span className="muted">{new Date(runStats.timestamp).toLocaleString()}</span>}
        </div>
        
        {!runStats ? (
          <div className="empty-state" style={{ padding: '2rem 0', margin: 0 }}>
            <p className="muted">No statistics available yet. Run the scraper to generate stats.</p>
          </div>
        ) : (
          <div className="stats-grid">
            <div className="stat-card">
              <span className="stat-value">{runStats.jobs_scanned ?? 0}</span>
              <span className="stat-label">Jobs Scanned</span>
            </div>
            <div className="stat-card highlight">
              <span className="stat-value">{runStats.icp_leads_matched ?? 0}</span>
              <span className="stat-label">ICP Leads Matched</span>
            </div>
            <div className="stat-card highlight">
              <span className="stat-value">{runStats.icp_leads_saved ?? 0}</span>
              <span className="stat-label">ICP Leads Saved</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{runStats.easy_applied ?? 0}</span>
              <span className="stat-label">Easy Applied</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{runStats.external_jobs ?? 0}</span>
              <span className="stat-label">External Links</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{runStats.total_applied_or_collected ?? 0}</span>
              <span className="stat-label">Total Applied</span>
            </div>
            <div className="stat-card warn">
              <span className="stat-value">{runStats.failed_jobs ?? 0}</span>
              <span className="stat-label">Failed</span>
            </div>
            <div className="stat-card">
              <span className="stat-value">{runStats.irrelevant_skipped ?? 0}</span>
              <span className="stat-label">Skipped</span>
            </div>
          </div>
        )}
      </section>

      {/* ── ICP Configuration ────────────────────────── */}
      <section className="scraper-section">
        <div className="section-header">
          <h2>ICP Configuration</h2>
          {!configEditing ? (
            <button className="btn btn-outline btn-sm" onClick={() => setConfigEditing(true)}>
              ✏️ Edit
            </button>
          ) : (
            <div className="config-actions">
              <button className="btn btn-primary btn-sm" onClick={handleSaveConfig} disabled={savingConfig}>
                {savingConfig ? 'Saving...' : '💾 Save'}
              </button>
              <button className="btn btn-outline btn-sm" onClick={() => { setConfigEditing(false); setConfigDraft(config) }}>
                Cancel
              </button>
            </div>
          )}
        </div>

        {configLoading ? (
          <div className="loading-container"><div className="loading-spinner"></div></div>
        ) : config ? (
          <div className="config-grid">
            <div className="config-item">
              <label>Extraction Mode</label>
              {configEditing ? (
                <select value={configDraft.lead_extraction_mode || ''} onChange={e => setConfigDraft(p => ({ ...p, lead_extraction_mode: e.target.value }))}>
                  <option value="apply_only">Apply Only</option>
                  <option value="extractor_only">Extractor Only</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              ) : (
                <span className="config-value badge">{config.lead_extraction_mode}</span>
              )}
            </div>
            <div className="config-item">
              <label>Match Mode</label>
              {configEditing ? (
                <select value={configDraft.icp_match_mode || ''} onChange={e => setConfigDraft(p => ({ ...p, icp_match_mode: e.target.value }))}>
                  <option value="strict">Strict</option>
                  <option value="score">Score</option>
                </select>
              ) : (
                <span className="config-value badge">{config.icp_match_mode}</span>
              )}
            </div>
            <div className="config-item">
              <label>Search Location</label>
              {configEditing ? (
                <input type="text" value={configDraft.search_location || ''} onChange={e => setConfigDraft(p => ({ ...p, search_location: e.target.value }))} placeholder="e.g. India" />
              ) : (
                <span className="config-value">{config.search_location || 'Not set'}</span>
              )}
            </div>
            <div className="config-item">
              <label>Workplace Type</label>
              {configEditing ? (
                <div className="checkbox-group" style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {['Remote', 'Hybrid', 'On-site'].map(mode => (
                    <label key={mode} style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '13px' }}>
                      <input type="checkbox" checked={(configDraft.on_site || []).includes(mode)} onChange={() => toggleOnSite(mode)} />
                      {mode}
                    </label>
                  ))}
                </div>
              ) : (
                <div className="tag-list">{(config.on_site || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
              )}
            </div>
            <div className="config-item">
              <label>Score Threshold</label>
              {configEditing ? (
                <input type="number" min="0" max="100" value={configDraft.icp_score_threshold || 70} onChange={e => setConfigDraft(p => ({ ...p, icp_score_threshold: parseInt(e.target.value) }))} />
              ) : (
                <span className="config-value">{config.icp_score_threshold}</span>
              )}
            </div>
            <div className="config-item full-width">
              <label>Search Terms</label>
              {configEditing ? (
                <textarea rows={4} value={(configDraft.icp_search_terms || []).join('\n')} onChange={e => updateConfigList('icp_search_terms', e.target.value)} placeholder="One term per line" />
              ) : (
                <div className="tag-list">{(config.icp_search_terms || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
              )}
            </div>
            <div className="config-item full-width">
              <label>Resume (Used for Applications)</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginTop: '0.5rem' }}>
                <span className="config-value" style={{ flex: 1, wordBreak: 'break-all' }}>{config.default_resume_path || 'Not set'}</span>
                {!configEditing && (
                  <>
                    <input type="file" id="resumeUpload" style={{ display: 'none' }} accept=".pdf,.doc,.docx" onChange={handleUploadResume} />
                    <button className="btn btn-outline btn-sm" onClick={() => document.getElementById('resumeUpload').click()} disabled={savingConfig}>
                      {savingConfig ? 'Uploading...' : '📤 Upload New Resume'}
                    </button>
                  </>
                )}
              </div>
            </div>
            <div className="config-item full-width">
              <label>Role Keywords</label>
              {configEditing ? (
                <textarea rows={3} value={(configDraft.icp_role_keywords || []).join('\n')} onChange={e => updateConfigList('icp_role_keywords', e.target.value)} placeholder="One keyword per line" />
              ) : (
                <div className="tag-list">{(config.icp_role_keywords || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
              )}
            </div>
            <div className="config-item full-width">
              <label>Industry Keywords</label>
              {configEditing ? (
                <textarea rows={3} value={(configDraft.icp_industry_keywords || []).join('\n')} onChange={e => updateConfigList('icp_industry_keywords', e.target.value)} placeholder="One keyword per line" />
              ) : (
                <div className="tag-list">{(config.icp_industry_keywords || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
              )}
            </div>
            <div className="config-item">
              <label>Company Size Targets</label>
              {configEditing ? (
                <textarea rows={2} value={(configDraft.icp_company_size_targets || []).join('\n')} onChange={e => updateConfigList('icp_company_size_targets', e.target.value)} placeholder="e.g. 11-30" />
              ) : (
                <div className="tag-list">{(config.icp_company_size_targets || []).map((t, i) => <span key={i} className="tag">{t}</span>)}</div>
              )}
            </div>
          </div>
        ) : (
          <p className="muted">Config not available. Make sure the Scraper directory is accessible.</p>
        )}
      </section>

      {/* ── Leads Section ────────────────────────────── */}
      <section className="scraper-section">
        <div className="section-header">
          <h2>Scraped Leads</h2>
          <div className="tabs">
            <button className={`tab ${activeTab === 'scraped' ? 'active' : ''}`} onClick={() => setActiveTab('scraped')}>
              From Files ({leads.length})
            </button>
            <button className={`tab ${activeTab === 'stored' ? 'active' : ''}`} onClick={() => setActiveTab('stored')}>
              In Database ({storedTotal})
            </button>
          </div>
        </div>

        {activeTab === 'scraped' && (
          <>
            <div className="leads-toolbar">
              <div className="file-selector">
                <select value={selectedFile} onChange={e => setSelectedFile(e.target.value)}>
                  <option value="leads.json">leads.json (latest run)</option>
                  {leadFiles.map((f, i) => (
                    <option key={i} value={f.path}>{f.filename} ({(f.size_bytes / 1024).toFixed(1)} KB)</option>
                  ))}
                </select>
              </div>
              <button className="btn btn-primary" onClick={handleIngest} disabled={ingesting || !userId}>
                {ingesting ? 'Ingesting...' : '📥 Ingest to Database'}
              </button>
              <button className="btn btn-outline" onClick={() => loadLeads(selectedFile)}>🔄 Refresh</button>
            </div>

            {leadsLoading ? (
              <div className="loading-container"><div className="loading-spinner"></div></div>
            ) : leads.length === 0 ? (
              <div className="empty-state">
                <h3>No leads found</h3>
                <p>Run the scraper to generate leads, then refresh</p>
              </div>
            ) : (
              <div className="table-container lead-table-wrap">
                <table className="leads-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Job Title</th>
                      <th>Company</th>
                      <th>Location</th>
                      <th>Industry</th>
                      <th>Intent</th>
                      <th>Links</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leads.slice(0, 100).map((lead, i) => (
                      <tr key={i}>
                        <td className="name-cell">
                          {lead['Full Name'] || lead.full_name || '—'}
                        </td>
                        <td>{lead['Job Title'] || lead.job_title || '—'}</td>
                        <td className="company-cell">{lead['Company Name'] || lead.company_name || '—'}</td>
                        <td>{[lead['City'] || lead.city, lead['Country'] || lead.country].filter(Boolean).join(', ') || '—'}</td>
                        <td>{lead['Industry'] || lead.industry || '—'}</td>
                        <td>
                          <span className={`intent-badge ${(lead['Buying Intent'] || lead.buying_intent || '').toLowerCase().replace(' ', '-')}`}>
                            {lead['Buying Intent'] || lead.buying_intent || '—'}
                          </span>
                        </td>
                        <td className="links-cell">
                          {(lead['Linkedin Url'] || lead.linkedin_url) && (
                            <a href={lead['Linkedin Url'] || lead.linkedin_url} target="_blank" rel="noopener noreferrer" title="LinkedIn Profile">🔗</a>
                          )}
                          {(lead['Job Link'] || lead.job_link) && (
                            <a href={lead['Job Link'] || lead.job_link} target="_blank" rel="noopener noreferrer" title="Job Posting">💼</a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {leads.length > 100 && <p className="muted table-note">Showing first 100 of {leads.length} leads</p>}
              </div>
            )}
          </>
        )}

        {activeTab === 'stored' && (
          <>
            <div className="leads-toolbar">
              <button className="btn btn-outline btn-sm" onClick={selectAllStored}>
                {selectedLeads.size === storedLeads.length && storedLeads.length > 0 ? 'Deselect All' : 'Select All'}
              </button>
              <button
                className="btn btn-primary"
                onClick={handleImportToContacts}
                disabled={importing || selectedLeads.size === 0}
              >
                {importing ? 'Importing...' : `📤 Import ${selectedLeads.size} to Contacts`}
              </button>
              <button className="btn btn-outline" onClick={() => loadStoredLeads(storedPage)}>🔄 Refresh</button>
            </div>

            {storedLoading ? (
              <div className="loading-container"><div className="loading-spinner"></div></div>
            ) : storedLeads.length === 0 ? (
              <div className="empty-state">
                <h3>No stored leads</h3>
                <p>Ingest leads from the "From Files" tab first</p>
              </div>
            ) : (
              <>
                <div className="table-container lead-table-wrap">
                  <table className="leads-table">
                    <thead>
                      <tr>
                        <th className="checkbox-col">
                          <input type="checkbox" checked={selectedLeads.size === storedLeads.length && storedLeads.length > 0} onChange={selectAllStored} />
                        </th>
                        <th>Name</th>
                        <th>Job Title</th>
                        <th>Company</th>
                        <th>Location</th>
                        <th>Intent</th>
                        <th>Status</th>
                        <th>Links</th>
                      </tr>
                    </thead>
                    <tbody>
                      {storedLeads.map((lead) => (
                        <tr key={lead.id} className={selectedLeads.has(lead.id) ? 'selected' : ''}>
                          <td className="checkbox-col">
                            <input type="checkbox" checked={selectedLeads.has(lead.id)} onChange={() => toggleLead(lead.id)} />
                          </td>
                          <td className="name-cell">{lead.full_name || '—'}</td>
                          <td>{lead.job_title || '—'}</td>
                          <td className="company-cell">{lead.company_name || '—'}</td>
                          <td>{[lead.city, lead.country].filter(Boolean).join(', ') || '—'}</td>
                          <td>
                            <span className={`intent-badge ${(lead.buying_intent || '').toLowerCase().replace(' ', '-')}`}>
                              {lead.buying_intent || '—'}
                            </span>
                          </td>
                          <td>
                            <span className={`status-tag ${lead.imported_to_contacts ? 'imported' : 'pending'}`}>
                              {lead.imported_to_contacts ? 'Imported' : 'Pending'}
                            </span>
                          </td>
                          <td className="links-cell">
                            {lead.linkedin_url && <a href={lead.linkedin_url} target="_blank" rel="noopener noreferrer">🔗</a>}
                            {lead.job_link && <a href={lead.job_link} target="_blank" rel="noopener noreferrer">💼</a>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {storedTotal > 50 && (
                  <div className="pagination">
                    <button disabled={storedPage <= 1} onClick={() => loadStoredLeads(storedPage - 1)}>← Previous</button>
                    <span>Page {storedPage} of {Math.ceil(storedTotal / 50)}</span>
                    <button disabled={storedPage >= Math.ceil(storedTotal / 50)} onClick={() => loadStoredLeads(storedPage + 1)}>Next →</button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </section>
    </div>
  )
}

export default LinkedInScraper
