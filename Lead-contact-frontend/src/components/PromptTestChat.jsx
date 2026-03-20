import { useState, useRef, useEffect } from 'react'
import { apiUrl } from '../utils/api'
import './PromptTestChat.css'

function PromptTestChat({ promptText, userId, onClose }) {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!inputValue.trim() || sending) return

    const userMessage = inputValue.trim()
    setInputValue('')
    setError(null)

    // Add user message to chat
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
          prompt_text: promptText,
          user_message: userMessage,
          conversation_history: messages.map(m => ({
            role: m.role,
            content: m.content
          }))
        })
      })

      const data = await response.json()

      if (data.success && data.ai_response) {
        setMessages([
          ...newMessages,
          { role: 'assistant', content: data.ai_response }
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

  return (
    <div className="prompt-test-chat">
      <div className="chat-header">
        <div className="chat-header-info">
          <h3>Test Prompt</h3>
          <p>Chat as a contact would to test how the AI responds</p>
        </div>
        <div className="chat-header-actions">
          <button className="clear-btn" onClick={handleClear} disabled={messages.length === 0}>
            Clear Chat
          </button>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <p>Start a conversation to test your prompt</p>
            <p className="chat-hint">Type a message as if you were a contact replying to a sales email</p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`chat-message ${msg.role}`}>
            <div className="message-label">
              {msg.role === 'user' ? '👤 Contact (You)' : '🤖 AI Reply'}
            </div>
            <div className="message-content">
              {msg.content}
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
        <div className="chat-error">
          {error}
        </div>
      )}

      <div className="chat-input-container">
        <textarea
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message as a contact would..."
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

      <div className="prompt-preview-section">
        <details>
          <summary>View Current Prompt</summary>
          <pre>{promptText}</pre>
        </details>
      </div>
    </div>
  )
}

export default PromptTestChat

