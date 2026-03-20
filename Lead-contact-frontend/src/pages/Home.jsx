import { useState, useEffect } from 'react'
import ProviderList from '../components/ProviderList'
import { Button, Card } from '../components/common'
import { apiUrl } from '../utils/api'
import '../App.css'

function Home() {
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchProviders()
  }, [])

  const fetchProviders = async () => {
    try {
      const response = await fetch(apiUrl('/api/providers'))
      const data = await response.json()
      setProviders(data)
    } catch (err) {
      console.error('Error fetching providers:', err)
      setError('Failed to fetch providers')
    }
  }

  const handleConnect = async (provider) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await fetch(apiUrl(`/api/auth/${provider}/url?state=${provider}`))
      const data = await response.json()
      
      if (response.ok) {
        window.location.href = data.auth_url
      } else {
        setError(data.detail || 'Failed to generate auth URL')
      }
    } catch (err) {
      console.error('Error connecting:', err)
      setError('Failed to initiate authentication')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1 className="text-h1">Lead Contact</h1>
        <p className="text-body-secondary">Email Campaign Management Platform</p>
      </header>

      <main className="app-content">
        <Card className="connect-container">
          <h2 className="text-h2 mb-lg">Connect Your Account</h2>
          <p className="text-body-secondary mb-xl">
            Choose a provider below to connect your account and start managing your email campaigns
          </p>

          {error && (
            <div className="alert mb-lg">
              <span>{error}</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => setError(null)}
                style={{ marginLeft: 'auto' }}
              >
                ✕
              </Button>
            </div>
          )}

          <ProviderList
            providers={providers}
            onConnect={handleConnect}
            loading={loading}
          />
        </Card>
      </main>
    </div>
  )
}

export default Home

