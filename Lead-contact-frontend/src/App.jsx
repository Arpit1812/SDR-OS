import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Callback from './pages/Callback'
import Dashboard from './pages/Dashboard'
import Contacts from './pages/Contacts'
import Templates from './pages/Templates'
import Prompts from './pages/Prompts'
import AIPlayground from './pages/AIPlayground'
import SendEmails from './pages/SendEmails'
import Campaigns from './pages/Campaigns'
import CampaignDetail from './pages/CampaignDetail'
import Logs from './pages/Logs'
import Settings from './pages/Settings'
import DesignSystemDemo from './pages/DesignSystemDemo'
import './styles/design-system.css'
import './App.css'

function App() {
  return (
    <Router>
      <Routes>
        {/* Public Routes */}
        <Route path="/" element={<Home />} />
        <Route path="/callback" element={<Callback />} />

        {/* Protected Routes (Wrapped in Layout) */}
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/contacts" element={<Contacts />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/prompts" element={<Prompts />} />
          <Route path="/playground" element={<AIPlayground />} />
          <Route path="/send" element={<SendEmails />} />
          <Route path="/campaigns" element={<Campaigns />} />
          <Route path="/campaigns/:campaignId" element={<CampaignDetail />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/design-system" element={<DesignSystemDemo />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
