import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import PromptModal from '../components/PromptModal'
import { apiUrl } from '../utils/api'
import './Prompts.css'

function Prompts() {
  const navigate = useNavigate()
  const location = useLocation()
  const [prompts, setPrompts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userId, setUserId] = useState(null)
  const [showModal, setShowModal] = useState(false)
  const [editingPrompt, setEditingPrompt] = useState(null)
  const [systemDefault, setSystemDefault] = useState(null)

  useEffect(() => {
    const userData = location.state?.userData
    const savedUser = localStorage.getItem('user')

    if (userData?.id) {
      setUserId(userData.id)
      loadPrompts(userData.id)
      loadSystemDefault()
    } else if (savedUser) {
      const user = JSON.parse(savedUser)
      setUserId(user.id)
      loadPrompts(user.id)
      loadSystemDefault()
    } else {
      navigate('/')
    }
  }, [navigate, location])

  const loadPrompts = async (uid) => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(apiUrl('/api/prompts'), {
        headers: { 'X-User-Id': uid }
      })

      if (response.ok) {
        const data = await response.json()
        setPrompts(data.prompts)
      } else {
        setError('Failed to load prompts')
      }
    } catch (err) {
      console.error('Error loading prompts:', err)
      setError('Failed to load prompts')
    } finally {
      setLoading(false)
    }
  }

  const loadSystemDefault = async () => {
    try {
      const response = await fetch(apiUrl('/api/prompts/system-default'))
      if (response.ok) {
        const data = await response.json()
        setSystemDefault(data)
      }
    } catch (err) {
      console.error('Error loading system default:', err)
    }
  }

  const handleCreate = () => {
    setEditingPrompt(null)
    setShowModal(true)
  }

  const handleEdit = (prompt) => {
    setEditingPrompt(prompt)
    setShowModal(true)
  }

  const handleDelete = async (promptId) => {
    if (!window.confirm('Are you sure you want to delete this prompt?')) {
      return
    }

    try {
      const response = await fetch(apiUrl(`/api/prompts/${promptId}`), {
        method: 'DELETE',
        headers: { 'X-User-Id': userId }
      })

      if (response.ok) {
        loadPrompts(userId)
      } else {
        alert('Failed to delete prompt')
      }
    } catch (err) {
      console.error('Error deleting prompt:', err)
      alert('Failed to delete prompt')
    }
  }

  const handleSetDefault = async (promptId) => {
    try {
      const response = await fetch(apiUrl(`/api/prompts/${promptId}/set-default`), {
        method: 'POST',
        headers: { 'X-User-Id': userId }
      })

      if (response.ok) {
        loadPrompts(userId)
      } else {
        alert('Failed to set default prompt')
      }
    } catch (err) {
      console.error('Error setting default:', err)
      alert('Failed to set default prompt')
    }
  }

  const handleModalClose = () => {
    setShowModal(false)
    setEditingPrompt(null)
  }

  const handleModalSave = () => {
    setShowModal(false)
    setEditingPrompt(null)
    loadPrompts(userId)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const truncateText = (text, maxLength = 100) => {
    if (!text) return ''
    if (text.length <= maxLength) return text
    return text.substring(0, maxLength) + '...'
  }

  return (
    <div className="prompts-page">
      <div className="page-header">
        <h1 className="page-title">AI Prompts</h1>
        <p className="page-subtitle">Manage your AI reply prompts for campaigns</p>
      </div>

      <div className="prompts-toolbar">
        <button className="create-button" onClick={handleCreate}>
          + Create Prompt
        </button>
      </div>

      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading prompts...</p>
        </div>
      )}

      {error && (
        <div className="error-container">
          <span className="error-icon">!</span>
          {error}
        </div>
      )}

      {!loading && !error && prompts.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📝</div>
          <h3>No prompts yet</h3>
          <p>Create your first AI prompt to customize how auto-replies are generated</p>
          <button className="empty-action-button" onClick={handleCreate}>
            Create Prompt
          </button>
        </div>
      )}

      {!loading && !error && prompts.length > 0 && (
        <div className="prompts-grid">
          {prompts.map((prompt) => (
            <div key={prompt.id} className={`prompt-card ${prompt.is_default ? 'is-default' : ''}`}>
              <div className="prompt-card-header">
                <h3 className="prompt-name">{prompt.name}</h3>
                {prompt.is_default && (
                  <span className="default-badge">Default</span>
                )}
              </div>
              
              {prompt.description && (
                <p className="prompt-description">{prompt.description}</p>
              )}
              
              <div className="prompt-preview">
                <code>{truncateText(prompt.prompt_text, 150)}</code>
              </div>
              
              <div className="prompt-meta">
                <span className="prompt-date">Created {formatDate(prompt.created_at)}</span>
              </div>
              
              <div className="prompt-actions">
                {!prompt.is_default && (
                  <button 
                    className="action-btn set-default-btn"
                    onClick={() => handleSetDefault(prompt.id)}
                    title="Set as default"
                  >
                    Set Default
                  </button>
                )}
                <button 
                  className="action-btn edit-btn"
                  onClick={() => handleEdit(prompt)}
                  title="Edit prompt"
                >
                  Edit
                </button>
                <button 
                  className="action-btn delete-btn"
                  onClick={() => handleDelete(prompt.id)}
                  title="Delete prompt"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* System Default Info */}
      {systemDefault && (
        <div className="system-default-section">
          <h3>System Default Prompt</h3>
          <p className="system-default-note">
            This is used when no custom prompt is selected for a campaign.
          </p>
          <div className="system-default-preview">
            <code>{systemDefault.prompt_text}</code>
          </div>
        </div>
      )}

      {/* Test Prompts Link */}
      <div className="test-prompts-cta">
        <div className="cta-content">
          <span className="cta-icon">🧪</span>
          <div>
            <h4>Test Your Prompts</h4>
            <p>Use the AI Playground to test how your prompts respond to different messages</p>
          </div>
        </div>
        <Link to="/playground" className="cta-button">
          Open AI Playground →
        </Link>
      </div>

      {/* Modal */}
      {showModal && (
        <PromptModal
          prompt={editingPrompt}
          userId={userId}
          onClose={handleModalClose}
          onSave={handleModalSave}
        />
      )}
    </div>
  )
}

export default Prompts

