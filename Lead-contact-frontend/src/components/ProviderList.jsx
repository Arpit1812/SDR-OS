import { Button } from './common'
import './ProviderList.css'

const providerIcons = {
  gmail: 'G',
  outlook: 'O',
  yahoo: 'Y',
}

const providerNames = {
  gmail: 'Gmail',
  outlook: 'Outlook',
  yahoo: 'Yahoo Mail',
}

function ProviderList({ providers, onConnect, loading }) {
  if (providers.length === 0) {
    return (
      <div className="provider-empty">
        <p className="text-body-secondary">No providers available</p>
      </div>
    )
  }

  return (
    <div className="provider-list">
      {providers.map((provider) => (
        <div key={provider} className="provider-card">
          <div className="provider-icon">
            {providerIcons[provider] || provider.charAt(0).toUpperCase()}
          </div>
          <div className="provider-info">
            <h3 className="text-h3">{providerNames[provider] || provider.charAt(0).toUpperCase() + provider.slice(1)}</h3>
            <p className="text-body-secondary">Connect your {provider} account to continue</p>
          </div>
          <Button
            onClick={() => onConnect(provider)}
            disabled={loading}
            loading={loading}
          >
            {loading ? 'Connecting...' : 'Connect'}
          </Button>
        </div>
      ))}
    </div>
  )
}

export default ProviderList

