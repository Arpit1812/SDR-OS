import { Link, Outlet, useLocation } from 'react-router-dom'
import './Layout.css'

function Layout() {
    const location = useLocation()

    const isActive = (path) => {
        return location.pathname === path ? 'active' : ''
    }

    return (
        <div className="layout">
            <aside className="sidebar">
                <div className="sidebar-header">
                    <h2>Lead Contact</h2>
                </div>
                <nav className="sidebar-nav">
                    <Link to="/dashboard" className={`nav-item ${isActive('/dashboard')}`}>
                        Dashboard
                    </Link>
                    <Link to="/contacts" className={`nav-item ${isActive('/contacts')}`}>
                        Contacts
                    </Link>
                    <Link to="/templates" className={`nav-item ${isActive('/templates')}`}>
                        Templates
                    </Link>
                    <Link to="/prompts" className={`nav-item ${isActive('/prompts')}`}>
                        AI Prompts
                    </Link>
                    <Link to="/playground" className={`nav-item ${isActive('/playground')}`}>
                        AI Playground
                    </Link>
                    <Link to="/send" className={`nav-item ${isActive('/send')}`}>
                        Send Emails
                    </Link>
                    <Link to="/campaigns" className={`nav-item ${location.pathname.startsWith('/campaigns') ? 'active' : ''}`}>
                        Campaigns
                    </Link>
                    <Link to="/logs" className={`nav-item ${isActive('/logs')}`}>
                        Logs
                    </Link>
                    <Link to="/settings" className={`nav-item ${isActive('/settings')}`}>
                        Settings
                    </Link>
                    <Link to="/design-system" className={`nav-item ${isActive('/design-system')}`}>
                        Design System
                    </Link>
                </nav>
                <div className="sidebar-footer">
                    <Link to="/" className="nav-item logout">
                        Logout
                    </Link>
                </div>
            </aside>
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    )
}

export default Layout
