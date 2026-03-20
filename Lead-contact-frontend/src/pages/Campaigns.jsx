import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiUrl } from '../utils/api'
import './Campaigns.css'

function Campaigns() {
  const navigate = useNavigate()
  const location = useLocation()
  const [campaigns, setCampaigns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userId, setUserId] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredCampaigns, setFilteredCampaigns] = useState([])

  useEffect(() => {
    const userData = location.state?.userData
    const savedUser = localStorage.getItem('user')

    if (userData?.id) {
      setUserId(userData.id)
      loadCampaigns(userData.id)
    } else if (savedUser) {
      const user = JSON.parse(savedUser)
      setUserId(user.id)
      loadCampaigns(user.id)
    } else {
      navigate('/')
    }
  }, [navigate, location])

  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredCampaigns(campaigns)
    } else {
      const filtered = campaigns.filter(campaign =>
        campaign.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        campaign.csv_source.toLowerCase().includes(searchQuery.toLowerCase())
      )
      setFilteredCampaigns(filtered)
    }
  }, [searchQuery, campaigns])

  const loadCampaigns = async (uid) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(apiUrl('/api/campaigns'), {
        headers: {
          'X-User-Id': uid
        }
      })

      if (response.ok) {
        const data = await response.json()
        console.log('Campaigns loaded:', data)
        setCampaigns(data.campaigns || [])
        setFilteredCampaigns(data.campaigns || [])
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to load campaigns' }))
        console.error('Failed to load campaigns:', errorData)
        setError(errorData.detail || 'Failed to load campaigns')
      }
    } catch (err) {
      console.error('Error loading campaigns:', err)
      setError('Failed to load campaigns')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusClasses = {
      'queued': 'status-badge status-queued',
      'running': 'status-badge status-running',
      'completed': 'status-badge status-completed',
      'failed': 'status-badge status-failed'
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

  const getProgressPercent = (campaign) => {
    if (campaign.total_contacts === 0) return 0
    return Math.round(((campaign.sent + campaign.failed) / campaign.total_contacts) * 100)
  }

  return (
    <div className="campaigns-page">
      <div className="page-header">
        <h1 className="page-title">Campaigns</h1>
        <p className="page-subtitle">View your email campaign history and results</p>
      </div>

      <div className="campaigns-toolbar">
        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="Search campaigns..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
        <button className="new-campaign-button" onClick={() => navigate('/send')}>
          + New Campaign
        </button>
      </div>

      {loading ? (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading campaigns...</p>
        </div>
      ) : error ? (
        <div className="error-container">
          <span className="error-icon">!</span>
          {error}
        </div>
      ) : filteredCampaigns.length === 0 ? (
        <div className="empty-state">
          <h3>No campaigns yet</h3>
          <p>Create your first email campaign to get started</p>
          <button className="empty-action-button" onClick={() => navigate('/send')}>
            Create Campaign
          </button>
        </div>
      ) : (
        <div className="table-container">
          <table className="campaigns-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Status</th>
                <th>Progress</th>
                <th>Sent</th>
                <th>Replies</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCampaigns.map((campaign) => (
                <tr key={campaign.id}>
                  <td className="campaign-name-cell">
                    <div className="campaign-name">{campaign.name}</div>
                    <div className="campaign-source">{campaign.csv_source}</div>
                  </td>
                  <td>
                    <span className={getStatusBadge(campaign.status)}>
                      {campaign.status}
                    </span>
                  </td>
                  <td>
                    <div className="progress-container">
                      <div className="progress-bar">
                        <div 
                          className="progress-fill" 
                          style={{ width: `${getProgressPercent(campaign)}%` }}
                        ></div>
                      </div>
                      <span className="progress-text">
                        {campaign.sent + campaign.failed} / {campaign.total_contacts}
                      </span>
                    </div>
                  </td>
                  <td className="count-cell success">{campaign.sent}</td>
                  <td className="count-cell replies">
                    {campaign.replies_count > 0 ? (
                      <span className="replies-badge">
                        💬 {campaign.replies_count}
                      </span>
                    ) : (
                      <span className="no-replies">-</span>
                    )}
                  </td>
                  <td className="date-cell">{formatDate(campaign.created_at)}</td>
                  <td className="actions-cell">
                    <button 
                      className="view-button"
                      onClick={() => navigate(`/campaigns/${campaign.id}`)}
                      title="View Details"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Campaigns

