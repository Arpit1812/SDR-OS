import { useState, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiUrl } from '../utils/api'
import './AIPlayground.css'

function AIPlayground() {
  const navigate = useNavigate()
  const location = useLocation()
  const [userId, setUserId] = useState(null)
  
  // Prompts
  const [prompts, setPrompts] = useState([])
  const [selectedPrompt, setSelectedPrompt] = useState(null)
  const [systemDefault, setSystemDefault] = useState(null)
  const [loadingPrompts, setLoadingPrompts] = useState(true)
  
  // Calendar
  const [calendarStatus, setCalendarStatus] = useState(null)
  const [calToolsEnabled, setCalToolsEnabled] = useState(false)
  const [togglingTools, setTogglingTools] = useState(false)
  
  // Chat
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  
  // Initial template
  const [showTemplateModal, setShowTemplateModal] = useState(false)
  const [initialTemplate, setInitialTemplate] = useState('')
  
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    const userData = location.state?.userData
    const savedUser = localStorage.getItem('user')

    if (userData?.id) {
      setUserId(userData.id)
      loadData(userData.id)
    } else if (savedUser) {
      const user = JSON.parse(savedUser)
      setUserId(user.id)
      loadData(user.id)
    } else {
      navigate('/')
    }
  }, [navigate, location])

  const loadData = async (uid) => {
    await Promise.all([
      loadPrompts(uid),
      loadCalendarStatus(uid),
      loadSystemDefault()
    ])
  }

  const loadPrompts = async (uid) => {
    setLoadingPrompts(true)
    try {
      const response = await fetch(apiUrl('/api/prompts'), {
        headers: { 'X-User-Id': uid }
      })
      if (response.ok) {
        const data = await response.json()
        setPrompts(data.prompts)
      }
    } catch (err) {
      console.error('Error loading prompts:', err)
    } finally {
      setLoadingPrompts(false)
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
        }
      }
    } catch (err) {
      console.error('Error loading calendar status:', err)
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

  const getCurrentPromptText = () => {
    if (selectedPrompt === 'system-default') {
      return systemDefault?.prompt_text || ''
    }
    if (selectedPrompt) {
      const prompt = prompts.find(p => p.id === selectedPrompt)
      return prompt?.prompt_text || ''
    }
    return systemDefault?.prompt_text || ''
  }

  const handleStartConversation = () => {
    setShowTemplateModal(true)
  }

  const handleSetTemplate = () => {
    if (!initialTemplate.trim()) return
    
    // Add the initial template as AI's first message (outbound email)
    setMessages([{
      role: 'assistant',
      content: initialTemplate.trim(),
      isInitial: true
    }])
    setShowTemplateModal(false)
    setInitialTemplate('')
  }

  const handleSend = async () => {
    if (!inputValue.trim() || sending) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setError(null)

    const newMessages = [
      ...messages,
      { role: 'user', content: userMessage }
    ]
    setMessages(newMessages)

    setSending(true)

    try {
      const response = await fetch(apiUrl('/api/prompts/test'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Id': userId
        },
        body: JSON.stringify({
          prompt_text: getCurrentPromptText(),
          user_message: userMessage,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: m.content
          })),
          cal_tools_enabled: calendarStatus?.connected && calToolsEnabled
        })
      })

      const data = await response.json()

      if (data.success && data.ai_response) {
        setMessages([
          ...newMessages,
          { 
            role: 'assistant', 
            content: data.ai_response,
            booking_url: data.booking_url,
            booking_id: data.booking_id
          }
        ])
      } else {
        setError(data.error || 'Failed to get AI response')
      }
    } catch (err) {
      console.error('Error testing prompt:', err)
      setError('Failed to connect to AI service')
    } finally {
      setSending(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleClear = () => {
    setMessages([])
    setError(null)
  }

  const getPromptDisplayName = () => {
    if (selectedPrompt === 'system-default') return 'System Default'
    if (selectedPrompt) {
      const prompt = prompts.find(p => p.id === selectedPrompt)
      return prompt?.name || 'Unknown Prompt'
    }
    return 'System Default'
  }

  return (
    <div className="ai-playground-page">
      <div className="page-header">
        <h1 className="page-title">AI Playground</h1>
        <p className="page-subtitle">Test your prompts by chatting with the AI as a contact would</p>
      </div>

      <div className="playground-layout">
        {/* Left Panel - Settings */}
        <div className="playground-settings">
          <div className="settings-card">
            <h3>Select Prompt</h3>
            <select 
              value={selectedPrompt || 'system-default'}
              onChange={(e) => setSelectedPrompt(e.target.value === 'system-default' ? 'system-default' : e.target.value)}
              disabled={loadingPrompts}
            >
              <option value="system-default">System Default</option>
              {prompts.map(p => (
                <option key={p.id} value={p.id}>
                  {p.name} {p.is_default ? '(Default)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div className="settings-card">
            <h3>Cal.com Integration</h3>
            {calendarStatus?.connected ? (
              <>
                <div className="calendar-status connected">
                  <span className="status-dot"></span>
                  Connected ({calendarStatus.username})
                </div>
                <div className="toggle-row">
                  <span className="toggle-label">AI Calendar Tools</span>
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
                <p className="toggle-hint">
                  {calToolsEnabled 
                    ? 'AI can check availability and book meetings' 
                    : 'Calendar tools disabled for AI'}
                </p>
              </>
            ) : (
              <div className="calendar-status disconnected">
                <span className="status-dot"></span>
                Not Connected
                <a href="/settings" className="connect-link">Connect in Settings →</a>
              </div>
            )}
          </div>

          <div className="settings-card">
            <h3>Current Prompt</h3>
            <div className="prompt-preview-box">
              <pre>{getCurrentPromptText()}</pre>
            </div>
          </div>
        </div>

        {/* Right Panel - Chat */}
        <div className="playground-chat">
          <div className="chat-header">
            <div className="chat-header-info">
              <h3>Test Conversation</h3>
              <p>Using: {getPromptDisplayName()}</p>
            </div>
            <div className="chat-header-actions">
              {messages.length === 0 && (
                <button className="start-btn" onClick={handleStartConversation}>
                  + Start with Template
                </button>
              )}
              <button 
                className="clear-btn" 
                onClick={handleClear} 
                disabled={messages.length === 0}
              >
                Clear
              </button>
            </div>
          </div>

          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <div className="chat-empty-icon">💬</div>
                <h4>Start Testing Your Prompt</h4>
                <p>Type a message as a contact would, or click "Start with Template" to begin with an initial outreach email.</p>
                {calendarStatus?.connected && calToolsEnabled && (
                  <div className="tools-enabled-badge">
                    📅 Calendar tools enabled - try asking about availability!
                  </div>
                )}
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`chat-message ${msg.role}`}>
                <div className="message-label">
                  {msg.role === 'user' ? '👤 Contact (You)' : '🤖 AI Reply'}
                  {msg.isInitial && <span className="initial-badge">Initial Email</span>}
                </div>
                <div className="message-content">
                  {msg.content}
                  {msg.booking_url && (
                    <div className="booking-info">
                      📅 Meeting booked! <a href={msg.booking_url} target="_blank" rel="noopener noreferrer">{msg.booking_url}</a>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {sending && (
              <div className="chat-message assistant typing">
                <div className="message-label">🤖 AI Reply</div>
                <div className="message-content">
                  <span className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {error && (
            <div className="chat-error">{error}</div>
          )}

          <div className="chat-input-container">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type a reply as a contact would..."
              rows={2}
              disabled={sending}
            />
            <button 
              className="send-btn" 
              onClick={handleSend}
              disabled={!inputValue.trim() || sending}
            >
              {sending ? '...' : 'Send'}
            </button>
          </div>
        </div>
      </div>

      {/* Template Modal */}
      {showTemplateModal && (
        <div className="modal-overlay" onClick={() => setShowTemplateModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Initial Outreach Email</h3>
              <button className="modal-close" onClick={() => setShowTemplateModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p className="modal-hint">
                Enter the initial email that would be sent to the contact. The AI will respond as if this was received first.
              </p>
              <textarea
                value={initialTemplate}
                onChange={(e) => setInitialTemplate(e.target.value)}
                placeholder="Hi {{name}},

I noticed your company is doing great work in [industry]. I'd love to connect and discuss how we might help...

Best regards,
[Your Name]"
                rows={10}
              />
            </div>
            <div className="modal-actions">
              <button className="cancel-btn" onClick={() => setShowTemplateModal(false)}>
                Cancel
              </button>
              <button 
                className="confirm-btn" 
                onClick={handleSetTemplate}
                disabled={!initialTemplate.trim()}
              >
                Start Conversation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AIPlayground

