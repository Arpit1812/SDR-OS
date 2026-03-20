import { useState, useEffect } from 'react'
import { useNavigate, useLocation, useParams } from 'react-router-dom'
import { apiUrl } from '../utils/api'
import './CampaignDetail.css'

function CampaignDetail() {
  const navigate = useNavigate()
  const location = useLocation()
  const { campaignId } = useParams()
  const [campaign, setCampaign] = useState(null)
  const [emails, setEmails] = useState([])
  const [conversations, setConversations] = useState([])
  const [selectedConversation, setSelectedConversation] = useState(null)
  const [conversationMessages, setConversationMessages] = useState([])
  const [loading, setLoading] = useState(true)
  const [emailsLoading, setEmailsLoading] = useState(false)
  const [conversationsLoading, setConversationsLoading] = useState(false)
  const [messagesLoading, setMessagesLoading] = useState(false)
  const [error, setError] = useState(null)
  const [userId, setUserId] = useState(null)
  const [page, setPage] = useState(1)
  const [totalEmails, setTotalEmails] = useState(0)
  const [filter, setFilter] = useState('all')
  const [activeTab, setActiveTab] = useState('emails') // 'emails' | 'conversations' | 'settings'
  const [autoReplySettings, setAutoReplySettings] = useState({
    enabled: true,
    subject: 'Re: {{original_subject}}',
    body: 'Thank you for your reply!',
    maxReplies: 5,
    promptId: null
  })
  const [prompts, setPrompts] = useState([])
  const [savingSettings, setSavingSettings] = useState(false)
  const pageSize = 25

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

  useEffect(() => {
    if (userId && campaignId) {
      loadCampaign()
      loadEmails()
      loadConversations()
      loadPrompts()
    }
  }, [userId, campaignId])

  const loadPrompts = async () => {
    try {
      const response = await fetch(apiUrl('/api/prompts'), {
        headers: { 'X-User-Id': userId }
      })
      if (response.ok) {
        const data = await response.json()
        setPrompts(data.prompts)
      }
    } catch (err) {
      console.error('Error loading prompts:', err)
    }
  }

  useEffect(() => {
    if (userId && campaignId) {
      loadEmails()
    }
  }, [page, filter])

  const loadCampaign = async () => {
    try {
      const response = await fetch(apiUrl(`/api/campaigns/${campaignId}`), {
        headers: { 'X-User-Id': userId }
      })

      if (response.ok) {
        const data = await response.json()
        setCampaign(data.campaign)
        // Set auto-reply settings from campaign
        setAutoReplySettings({
          enabled: data.campaign.auto_reply_enabled ?? true,
          subject: data.campaign.auto_reply_subject || 'Re: {{original_subject}}',
          body: data.campaign.auto_reply_body || 'Thank you for your reply!',
          maxReplies: data.campaign.max_replies_per_thread || 3,
          promptId: data.campaign.prompt_id || ''
        })
      } else {
        setError('Campaign not found')
      }
    } catch (err) {
      console.error('Error loading campaign:', err)
      setError('Failed to load campaign')
    } finally {
      setLoading(false)
    }
  }

  const loadEmails = async () => {
    setEmailsLoading(true)
    try {
      const response = await fetch(
        apiUrl(`/api/campaigns/${campaignId}/emails?page=${page}&page_size=${pageSize}`),
        { headers: { 'X-User-Id': userId } }
      )

      if (response.ok) {
        const data = await response.json()
        let filteredLogs = data.logs

        if (filter !== 'all') {
          filteredLogs = data.logs.filter(log => log.status === filter)
        }

        setEmails(filteredLogs)
        setTotalEmails(data.total)
      }
    } catch (err) {
      console.error('Error loading emails:', err)
    } finally {
      setEmailsLoading(false)
    }
  }

  const loadConversations = async () => {
    setConversationsLoading(true)
    try {
      const response = await fetch(
        apiUrl(`/api/campaigns/${campaignId}/conversations`),
        { headers: { 'X-User-Id': userId } }
      )

      if (response.ok) {
        const data = await response.json()
        setConversations(data.conversations || [])
      }
    } catch (err) {
      console.error('Error loading conversations:', err)
    } finally {
      setConversationsLoading(false)
    }
  }

  const loadConversationMessages = async (conversationId) => {
    setMessagesLoading(true)
    try {
      const response = await fetch(
        apiUrl(`/api/campaigns/${campaignId}/conversations/${conversationId}`),
        { headers: { 'X-User-Id': userId } }
      )

      if (response.ok) {
        const data = await response.json()
        setConversationMessages(data.messages || [])
      }
    } catch (err) {
      console.error('Error loading messages:', err)
    } finally {
      setMessagesLoading(false)
    }
  }

  const openConversation = (conversation) => {
    setSelectedConversation(conversation)
    loadConversationMessages(conversation.id)
  }

  const closeConversation = () => {
    setSelectedConversation(null)
    setConversationMessages([])
  }

  const saveAutoReplySettings = async () => {
    setSavingSettings(true)
    try {
      const response = await fetch(`/api/campaigns/${campaignId}/auto-reply`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({
          enabled: autoReplySettings.enabled,
          subject: autoReplySettings.subject,
          body: autoReplySettings.body,
          max_replies: autoReplySettings.maxReplies,
          prompt_id: autoReplySettings.promptId || null
        })
      })

      if (response.ok) {
        // Reload campaign to get updated settings
        loadCampaign()
      }
    } catch (err) {
      console.error('Error saving settings:', err)
    } finally {
      setSavingSettings(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusClasses = {
      'queued': 'status-badge status-queued',
      'running': 'status-badge status-running',
      'completed': 'status-badge status-completed',
      'failed': 'status-badge status-failed',
      'sent': 'status-badge status-sent',
      'pending': 'status-badge status-pending'
    }
    return statusClasses[status] || 'status-badge'
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const totalPages = Math.ceil(totalEmails / pageSize)

  if (loading) {
    return (
      <div className="campaign-detail-page">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading campaign...</p>
        </div>
      </div>
    )
  }

  if (error || !campaign) {
    return (
      <div className="campaign-detail-page">
        <div className="error-container">
          <span className="error-icon">!</span>
          {error || 'Campaign not found'}
        </div>
        <button className="back-button" onClick={() => navigate('/campaigns')}>
          ← Back to Campaigns
        </button>
      </div>
    )
  }

  return (
    <div className="campaign-detail-page">
      <button className="back-button" onClick={() => navigate('/campaigns')}>
        ← Back to Campaigns
      </button>

      <div className="campaign-header">
        <div className="campaign-info">
          <h1 className="campaign-title">{campaign.name}</h1>
          <p className="campaign-meta">
            Source: {campaign.csv_source} • Created: {formatDate(campaign.created_at)}
          </p>
        </div>
        <span className={getStatusBadge(campaign.status)}>
          {campaign.status}
        </span>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{campaign.total_contacts}</div>
          <div className="stat-label">Total Contacts</div>
        </div>
        <div className="stat-card">
          <div className="stat-value success">{campaign.sent}</div>
          <div className="stat-label">Sent</div>
        </div>
        <div className="stat-card">
          <div className="stat-value error">{campaign.failed}</div>
          <div className="stat-label">Failed</div>
        </div>
        <div className="stat-card">
          <div className="stat-value replies">{campaign.replies_count || 0}</div>
          <div className="stat-label">Replies</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">
            {campaign.total_contacts > 0
              ? Math.round((campaign.sent / campaign.total_contacts) * 100)
              : 0}%
          </div>
          <div className="stat-label">Success Rate</div>
        </div>
      </div>

      {campaign.error_message && (
        <div className="error-banner">
          <strong>Error:</strong> {campaign.error_message}
        </div>
      )}

      {/* Tabs */}
      <div className="tabs-container">
        <div className="tabs">
          <button
            className={`tab ${activeTab === 'emails' ? 'active' : ''}`}
            onClick={() => setActiveTab('emails')}
          >
            📧 Email Logs
          </button>
          <button
            className={`tab ${activeTab === 'conversations' ? 'active' : ''}`}
            onClick={() => setActiveTab('conversations')}
          >
            💬 Conversations {conversations.length > 0 && <span className="tab-badge">{conversations.length}</span>}
          </button>
          <button
            className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => setActiveTab('settings')}
          >
            ⚙️ Auto-Reply Settings
          </button>
        </div>
      </div>

      {/* Email Logs Tab */}
      {activeTab === 'emails' && (
        <div className="emails-section">
          <div className="section-header">
            <h2>Email Logs</h2>
            <div className="filter-buttons">
              <button
                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                onClick={() => { setFilter('all'); setPage(1); }}
              >
                All
              </button>
              <button
                className={`filter-btn ${filter === 'sent' ? 'active' : ''}`}
                onClick={() => { setFilter('sent'); setPage(1); }}
              >
                Sent
              </button>
              <button
                className={`filter-btn ${filter === 'failed' ? 'active' : ''}`}
                onClick={() => { setFilter('failed'); setPage(1); }}
              >
                Failed
              </button>
            </div>
          </div>

          {emailsLoading ? (
            <div className="loading-container small">
              <div className="loading-spinner"></div>
            </div>
          ) : emails.length === 0 ? (
            <div className="empty-emails">
              <p>No email logs found</p>
            </div>
          ) : (
            <>
              <div className="table-container">
                <table className="emails-table">
                  <thead>
                    <tr>
                      <th>Recipient</th>
                      <th>Subject</th>
                      <th>Status</th>
                      <th>Sent At</th>
                      <th>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {emails.map((email) => (
                      <tr key={email.id}>
                        <td className="email-cell">{email.to_email}</td>
                        <td className="subject-cell">{email.subject}</td>
                        <td>
                          <span className={getStatusBadge(email.status)}>
                            {email.status}
                          </span>
                        </td>
                        <td className="date-cell">{formatDate(email.sent_at)}</td>
                        <td className="error-cell">
                          {email.error_message || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="page-btn"
                    disabled={page === 1}
                    onClick={() => setPage(p => p - 1)}
                  >
                    Previous
                  </button>
                  <span className="page-info">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    className="page-btn"
                    disabled={page === totalPages}
                    onClick={() => setPage(p => p + 1)}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {/* Conversations Tab */}
      {activeTab === 'conversations' && (
        <div className="conversations-section">
          <div className="section-header">
            <h2>Conversations</h2>
            <button className="refresh-btn" onClick={loadConversations}>
              🔄 Refresh
            </button>
          </div>

          {conversationsLoading ? (
            <div className="loading-container small">
              <div className="loading-spinner"></div>
            </div>
          ) : conversations.length === 0 ? (
            <div className="empty-conversations">
              <div className="empty-icon">💬</div>
              <h3>No replies yet</h3>
              <p>When contacts reply to your campaign emails, their conversations will appear here.</p>
            </div>
          ) : (
            <div className="conversations-list">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className="conversation-card"
                  onClick={() => openConversation(conv)}
                >
                  <div className="conversation-header">
                    <span className="conversation-email">{conv.contact_email}</span>
                    <span className="conversation-count">
                      {conv.message_count} messages
                    </span>
                  </div>
                  <div className="conversation-meta">
                    <span className="conversation-status">
                      {conv.status === 'active' ? '🟢 Active' : '⚫ Closed'}
                    </span>
                    <span className="conversation-replies">
                      {conv.auto_replies_sent} auto-replies sent
                    </span>
                    <span className="conversation-date">
                      Last: {formatDate(conv.last_message_at)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Auto-Reply Settings Tab */}
      {activeTab === 'settings' && (
        <div className="settings-section">
          <div className="section-header">
            <h2>Auto-Reply Settings</h2>
          </div>

          <div className="settings-form">
            <div className="setting-row">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={autoReplySettings.enabled}
                  onChange={(e) => setAutoReplySettings(prev => ({
                    ...prev,
                    enabled: e.target.checked
                  }))}
                />
                <span className="toggle-slider"></span>
                <span className="toggle-text">Enable Auto-Reply</span>
              </label>
              <p className="setting-description">
                Automatically reply to contacts when they respond to campaign emails
              </p>
            </div>

            <div className="setting-row">
              <label className="setting-label">Reply Subject</label>
              <input
                type="text"
                className="setting-input"
                value={autoReplySettings.subject}
                onChange={(e) => setAutoReplySettings(prev => ({
                  ...prev,
                  subject: e.target.value
                }))}
                placeholder="Re: {{original_subject}}"
              />
              <p className="setting-description">
                Use {'{{original_subject}}'} to include the original subject
              </p>
            </div>

            <div className="setting-row">
              <label className="setting-label">Reply Message</label>
              <textarea
                className="setting-textarea"
                value={autoReplySettings.body}
                onChange={(e) => setAutoReplySettings(prev => ({
                  ...prev,
                  body: e.target.value
                }))}
                placeholder="Thank you for your reply!"
                rows={4}
              />
            </div>

            <div className="setting-row">
              <label className="setting-label">Max Auto-Replies per Thread</label>
              <input
                type="number"
                className="setting-input small"
                value={autoReplySettings.maxReplies}
                onChange={(e) => setAutoReplySettings(prev => ({
                  ...prev,
                  maxReplies: parseInt(e.target.value) || 1
                }))}
                min={1}
                max={10}
              />
              <p className="setting-description">
                Stop auto-replying after this many responses to prevent spam
              </p>
            </div>

            <div className="setting-row">
              <label className="setting-label">AI Prompt</label>
              <select
                className="setting-input"
                value={autoReplySettings.promptId}
                onChange={(e) => setAutoReplySettings(prev => ({
                  ...prev,
                  promptId: e.target.value
                }))}
              >
                <option value="">System Default</option>
                {prompts.map((prompt) => (
                  <option key={prompt.id} value={prompt.id}>
                    {prompt.name} {prompt.is_default ? '(Your Default)' : ''}
                  </option>
                ))}
              </select>
              <p className="setting-description">
                Select the AI prompt to use for generating auto-replies.
                <a href="/prompts" style={{ marginLeft: '8px', color: 'var(--color-text-neutral)' }}>Manage prompts →</a>
              </p>
            </div>

            <div className="setting-actions">
              <button
                className="save-btn"
                onClick={saveAutoReplySettings}
                disabled={savingSettings}
              >
                {savingSettings ? 'Saving...' : 'Save Settings'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Conversation Modal */}
      {selectedConversation && (
        <div className="modal-overlay" onClick={closeConversation}>
          <div className="conversation-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title">
                <h3>Conversation with {selectedConversation.contact_email}</h3>
                <span className="modal-status">
                  {selectedConversation.status === 'active' ? '🟢 Active' : '⚫ Closed'}
                </span>
              </div>
              <button className="modal-close" onClick={closeConversation}>×</button>
            </div>

            <div className="messages-container">
              {messagesLoading ? (
                <div className="loading-container small">
                  <div className="loading-spinner"></div>
                </div>
              ) : conversationMessages.length === 0 ? (
                <div className="empty-messages">
                  <p>No messages in this conversation</p>
                </div>
              ) : (
                <div className="messages-list">
                  {conversationMessages.map((msg, index) => (
                    <div
                      key={index}
                      className={`message ${msg.direction === 'outbound' ? 'outbound' : 'inbound'}`}
                    >
                      <div className="message-header">
                        <span className="message-from">
                          {msg.direction === 'outbound'
                            ? (msg.is_auto_reply ? '🤖 Auto-Reply' : '📤 You')
                            : `📥 ${msg.from_email}`}
                        </span>
                        <span className="message-time">{formatDate(msg.sent_at)}</span>
                      </div>
                      <div className="message-subject">
                        <strong>Subject:</strong> {msg.subject}
                      </div>
                      <div
                        className="message-body"
                        dangerouslySetInnerHTML={{ __html: msg.body }}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CampaignDetail
