import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiUrl } from '../utils/api'
import '../App.css'

function Callback() {
  const navigate = useNavigate()
  const [error, setError] = useState(null)
  const hasCalledCallback = useRef(false)
  const hasNavigated = useRef(false)

  useEffect(() => {
    // Prevent double calls (React Strict Mode in dev)
    if (hasCalledCallback.current) {
      console.log('Callback already called, skipping...')
      return
    }
    hasCalledCallback.current = true
    console.log('First callback call, proceeding...')

    handleCallback()
  }, [])

  const handleCallback = async () => {
    const params = new URLSearchParams(window.location.search)
    const code = params.get('code')
    const provider = params.get('state')

    if (!code || !provider) {
      setError('Invalid callback parameters')
      setTimeout(() => navigate('/'), 3000)
      return
    }

    try {
      console.log('Calling backend callback API...')
      const response = await fetch(apiUrl(`/api/oauth/callback/${provider}?code=${code}`))
      const data = await response.json()

      console.log('Response status:', response.status)
      console.log('Response data:', data)

      if (response.ok) {
        // Store connection data and redirect to success page
        if (hasNavigated.current) {
          console.log('Already navigated, skipping...')
          return
        }
        hasNavigated.current = true

        console.log('Connection successful! Data:', data)
        console.log('Navigating to /success with state')

        // Pass data via router state (more reliable than sessionStorage)
        navigate('/dashboard', {
          replace: true,
          state: { connectionData: data }
        })
      } else {
        console.error('Authentication failed:', data)
        setError(data.detail || 'Authentication failed')
        setTimeout(() => navigate('/'), 3000)
      }
    } catch (err) {
      console.error('Error handling callback:', err)
      setError('Failed to complete authentication')
      setTimeout(() => navigate('/'), 3000)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>Lead Contact</h1>
        <p>Email Campaign Management Platform</p>
      </header>

      <main className="app-content">
        <div className="connect-container">
          {error ? (
            <>
              <div className="error-icon">✕</div>
              <h2 className="connect-title">Authentication Failed</h2>
              <p className="connect-subtitle">{error}</p>
              <p className="connect-subtitle">Redirecting to home...</p>
            </>
          ) : (
            <>
              <div className="loading-spinner"></div>
              <h2 className="connect-title">Authenticating...</h2>
              <p className="connect-subtitle">Please wait while we complete your connection</p>
            </>
          )}
        </div>
      </main>
    </div>
  )
}

export default Callback

