import { useState, useEffect } from 'react'
import { apiUrl } from '../utils/api'
import './PromptModal.css'

function PromptModal({ prompt, userId, onClose, onSave }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [promptText, setPromptText] = useState('')
  const [isDefault, setIsDefault] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)

  const isEditing = !!prompt

  useEffect(() => {
    if (prompt) {
      setName(prompt.name || '')
      setDescription(prompt.description || '')
      setPromptText(prompt.prompt_text || '')
      setIsDefault(prompt.is_default || false)
    } else {
      // Load system default as template for new prompts
      loadSystemDefault()
    }
  }, [prompt])

  const loadSystemDefault = async () => {
    try {
      const response = await fetch(apiUrl('/api/prompts/system-default'))
      if (response.ok) {
        const data = await response.json()
        setPromptText(data.prompt_text)
      }
    } catch (err) {
      console.error('Error loading system default:', err)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    if (!promptText.trim()) {
      setError('Prompt text is required')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const url = isEditing 
        ? apiUrl(`/api/prompts/${prompt.id}`)
        : apiUrl('/api/prompts')
      
      const method = isEditing ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          prompt_text: promptText.trim(),
          is_default: isDefault
        })
      })

      if (response.ok) {
        onSave()
      } else {
        const data = await response.json()
        setError(data.detail || 'Failed to save prompt')
      }
    } catch (err) {
      console.error('Error saving prompt:', err)
      setError('Failed to save prompt')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="prompt-modal-overlay" onClick={onClose}>
      <div className="prompt-modal" onClick={(e) => e.stopPropagation()}>
        <div className="prompt-modal-header">
          <h2>{isEditing ? 'Edit Prompt' : 'Create Prompt'}</h2>
          <button className="prompt-modal-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <form onSubmit={handleSubmit} className="prompt-modal-form">
          <div className="form-group">
            <label htmlFor="name">Name *</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g., Sales - Aggressive"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="description">Description</label>
            <input
              id="description"
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="e.g., Best for cold outreach campaigns"
            />
          </div>

          <div className="form-group">
            <label htmlFor="promptText">Prompt Text *</label>
            <textarea
              id="promptText"
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
              placeholder="Enter your AI prompt..."
              rows={12}
              required
            />
            <p className="form-hint">
              The AI will receive this prompt along with the conversation context. 
              Include instructions for how the AI should respond to emails.
            </p>
          </div>

          <div className="form-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={isDefault}
                onChange={(e) => setIsDefault(e.target.checked)}
              />
              <span>Set as default prompt</span>
            </label>
          </div>

          {error && (
            <div className="form-error">
              {error}
            </div>
          )}

          <div className="prompt-modal-actions">
            <button 
              type="button" 
              className="cancel-btn"
              onClick={onClose}
              disabled={saving}
            >
              Cancel
            </button>
            <button 
              type="submit" 
              className="save-btn"
              disabled={saving}
            >
              {saving ? 'Saving...' : (isEditing ? 'Update Prompt' : 'Create Prompt')}
            </button>
          </div>
        </form>

        <div className="prompt-tips">
          <h4>Tips for Writing Prompts</h4>
          <ul>
            <li>Define the AI's role and personality</li>
            <li>Specify the goal (e.g., schedule meetings, provide support)</li>
            <li>Include instructions for handling negative responses</li>
            <li>Use "SHOULD_NOT_REPLY" to tell AI not to respond to unsubscribes</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

export default PromptModal

