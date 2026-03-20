import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiUrl } from '../utils/api'
import './Settings.css'

function Settings() {
  const navigate = useNavigate()
  const location = useLocation()
  const [userId, setUserId] = useState(null)
  const [calendarStatus, setCalendarStatus] = useState(null)
  const [eventTypes, setEventTypes] = useState([])
  const [apiKey, setApiKey] = useState('')
  const [selectedEventType, setSelectedEventType] = useState(null)
  const [calToolsEnabled, setCalToolsEnabled] = useState(true)
  const [loading, setLoading] = useState(false)
  const [testing, setTesting] = useState(false)
  const [togglingTools, setTogglingTools] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  useEffect(() => {
    const userData = location.state?.userData
    const savedUser = localStorage.getItem('user')

    if (userData?.id) {
      setUserId(userData.id)
      loadCalendarStatus(userData.id)
    } else if (savedUser) {
      const user = JSON.parse(savedUser)
      setUserId(user.id)
      loadCalendarStatus(user.id)
    } else {
      navigate('/')
    }
  }, [navigate, location])

  const loadCalendarStatus = async (uid) => {
    try {
      const response = await fetch(apiUrl('/api/calendar/status'), {
        headers: { 'X-User-Id': uid }
      })
      if (response.ok) {
        const data = await response.json()
        setCalendarStatus(data)
        if (data.connected) {
          setCalToolsEnabled(data.cal_tools_enabled !== false)
          loadEventTypes(uid)
        }
      }
    } catch (err) {
      console.error('Error loading calendar status:', err)
    }
  }

  const loadEventTypes = async (uid) => {
    try {
      const response = await fetch(apiUrl('/api/calendar/event-types'), {
        headers: { 'X-User-Id': uid }
      })
      if (response.ok) {
        const data = await response.json()
        setEventTypes(data.event_types)
        // Select current event type if available
        if (calendarStatus?.event_type_id) {
          const current = data.event_types.find(et => et.id === calendarStatus.event_type_id)
          if (current) {
            setSelectedEventType(current.id)
          }
        }
      }
    } catch (err) {
      console.error('Error loading event types:', err)
    }
  }

  const handleTestConnection = async () => {
    if (!apiKey.trim()) {
      setError('Please enter an API key')
      return
    }

    setTesting(true)
    setError(null)
    setSuccess(null)

    try {
      // Test by trying to connect (we'll disconnect if it works)
      const response = await fetch(apiUrl('/api/calendar/connect'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({ api_key: apiKey })
      })

      if (response.ok) {
        setSuccess('Connection successful! API key is valid.')
        // Load event types
        await loadEventTypes(userId)
      } else {
        const data = await response.json()
        setError(data.detail || 'Connection failed')
      }
    } catch (err) {
      setError('Failed to test connection')
    } finally {
      setTesting(false)
    }
  }

  const handleConnect = async () => {
    if (!apiKey.trim()) {
      setError('Please enter an API key')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(apiUrl('/api/calendar/connect'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({
          api_key: apiKey,
          event_type_id: selectedEventType || null
        })
      })

      if (response.ok) {
        const data = await response.json()
        setCalendarStatus(data)
        setSuccess('Calendar connected successfully!')
        setApiKey('') // Clear API key field
        await loadEventTypes(userId)
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to connect calendar')
      }
    } catch (err) {
      setError('Failed to connect calendar')
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateEventType = async () => {
    if (!selectedEventType) {
      setError('Please select an event type')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const eventType = eventTypes.find(et => et.id === selectedEventType)
      const response = await fetch(apiUrl('/api/calendar/event-type'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({
          event_type_id: eventType.id,
          event_type_slug: eventType.slug,
          event_type_name: eventType.title
        })
      })

      if (response.ok) {
        const data = await response.json()
        setCalendarStatus(data)
        setSuccess('Event type updated successfully!')
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to update event type')
      }
    } catch (err) {
      setError('Failed to update event type')
    } finally {
      setLoading(false)
    }
  }

  const handleDisconnect = async () => {
    if (!window.confirm('Are you sure you want to disconnect your calendar?')) {
      return
    }

    setLoading(true)
    try {
      const response = await fetch(apiUrl('/api/calendar/disconnect'), {
        method: 'DELETE',
        headers: { 'X-User-Id': userId }
      })

      if (response.ok) {
        setCalendarStatus({ connected: false })
        setEventTypes([])
        setSelectedEventType(null)
        setSuccess('Calendar disconnected successfully')
      } else {
        setError('Failed to disconnect calendar')
      }
    } catch (err) {
      setError('Failed to disconnect calendar')
    } finally {
      setLoading(false)
    }
  }

  const handleToggleCalTools = async () => {
    const newValue = !calToolsEnabled
    setTogglingTools(true)
    setError(null)

    try {
      const response = await fetch(apiUrl('/api/calendar/toggle-tools'), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({ enabled: newValue })
      })

      if (response.ok) {
        const data = await response.json()
        setCalToolsEnabled(data.cal_tools_enabled)
        setSuccess(`AI calendar tools ${newValue ? 'enabled' : 'disabled'}`)
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to toggle calendar tools')
      }
    } catch (err) {
      setError('Failed to toggle calendar tools')
    } finally {
      setTogglingTools(false)
    }
  }

  return (
    <div className="settings-page">
      <div className="page-header">
        <h1 className="page-title">Settings</h1>
        <p className="page-subtitle">Manage your account preferences and integrations</p>
      </div>

      {/* Calendar Integration Section */}
      <div className="card">
        <div className="settings-section-header">
          <h3>Calendar Integration (Cal.com)</h3>
          {calendarStatus?.connected && (
            <span className="status-badge connected">Connected</span>
          )}
        </div>

        <p style={{ color: '#737373', fontSize: '14px', marginTop: '8px', marginBottom: '24px' }}>
          Connect your Cal.com calendar to enable AI to suggest meeting times and book meetings directly.
        </p>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}

        {!calendarStatus?.connected ? (
          <div className="calendar-connect-form">
            <div className="form-group">
              <label htmlFor="api-key">Cal.com API Key</label>
              <input
                id="api-key"
                type="password"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your Cal.com API key"
                style={{
                  width: '100%',
                  padding: '10px 14px',
                  border: '1px solid #e5e5e5',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              <p className="form-hint">
                Get your API key from{' '}
                <a href="https://cal.com/settings/developer/api-keys" target="_blank" rel="noopener noreferrer">
                  cal.com/settings/developer/api-keys
                </a>
              </p>
            </div>

            <div className="form-actions">
              <button
                className="btn-secondary"
                onClick={handleTestConnection}
                disabled={testing || !apiKey.trim()}
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </button>
              <button
                className="btn-primary"
                onClick={handleConnect}
                disabled={loading || !apiKey.trim()}
              >
                {loading ? 'Connecting...' : 'Connect Calendar'}
              </button>
            </div>
          </div>
        ) : (
          <div className="calendar-connected">
            <div className="connected-info">
              <p><strong>Username:</strong> {calendarStatus.username}</p>
              <p><strong>Event Type:</strong> {calendarStatus.event_type_name || 'Not selected'}</p>
            </div>

            {/* AI Calendar Tools Toggle */}
            <div className="toggle-section" style={{ marginTop: '24px' }}>
              <div className="toggle-row">
                <div className="toggle-info">
                  <label className="toggle-label">AI Calendar Tools</label>
                  <p className="toggle-description">
                    When enabled, the AI can check your availability and book meetings on your behalf during email conversations.
                  </p>
                </div>
                <label className="toggle-switch">
                  <input
                    type="checkbox"
                    checked={calToolsEnabled}
                    onChange={handleToggleCalTools}
                    disabled={togglingTools}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            {eventTypes.length > 0 && (
              <div className="form-group" style={{ marginTop: '24px' }}>
                <label htmlFor="event-type">Select Event Type</label>
                <select
                  id="event-type"
                  value={selectedEventType || calendarStatus.event_type_id || ''}
                  onChange={(e) => setSelectedEventType(parseInt(e.target.value))}
                  style={{
                    width: '100%',
                    padding: '10px 14px',
                    border: '1px solid #e5e5e5',
                    borderRadius: '6px',
                    fontSize: '14px',
                    background: '#ffffff'
                  }}
                >
                  {eventTypes.map((et) => (
                    <option key={et.id} value={et.id}>
                      {et.title} ({et.length} min)
                    </option>
                  ))}
                </select>
                <button
                  className="btn-primary"
                  onClick={handleUpdateEventType}
                  disabled={loading || !selectedEventType}
                  style={{ marginTop: '12px' }}
                >
                  {loading ? 'Updating...' : 'Update Event Type'}
                </button>
              </div>
            )}

            <button
              className="btn-danger"
              onClick={handleDisconnect}
              disabled={loading}
              style={{ marginTop: '24px' }}
            >
              {loading ? 'Disconnecting...' : 'Disconnect Calendar'}
            </button>
          </div>
        )}
      </div>

      {/* Email Provider Section */}
      <div className="card">
        <h3>Email Provider Integration</h3>
        <p style={{ color: '#737373', fontSize: '14px', marginTop: '12px' }}>
          Currently connected via OAuth. Your Gmail account is linked for sending emails.
        </p>
      </div>
    </div>
  )
}

export default Settings
