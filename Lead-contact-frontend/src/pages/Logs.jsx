import { useState, useEffect } from 'react'
import { apiUrl } from '../utils/api'

function Logs() {
    const [logs, setLogs] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [userId, setUserId] = useState(null)
    const [page, setPage] = useState(1)
    const [total, setTotal] = useState(0)
    const pageSize = 50

    useEffect(() => {
        const savedUser = localStorage.getItem('user')
        if (savedUser) {
            const user = JSON.parse(savedUser)
            setUserId(user.id)
            loadLogs(user.id, page)
        } else {
            setLoading(false)
        }
    }, [page])

    const loadLogs = async (uid, currentPage) => {
        setLoading(true)
        setError(null)

        try {
            const response = await fetch(apiUrl(`/api/campaigns/logs?page=${currentPage}&page_size=${pageSize}`), {
                headers: { 'X-User-Id': uid }
            })

            if (response.ok) {
                const data = await response.json()
                console.log('Logs loaded:', data)
                setLogs(data.logs || [])
                setTotal(data.total || 0)
            } else {
                const errorData = await response.json().catch(() => ({ detail: 'Failed to load logs' }))
                console.error('Failed to load logs:', errorData)
                setError(errorData.detail || 'Failed to load logs')
            }
        } catch (err) {
            console.error('Error loading logs:', err)
            setError('Failed to load logs')
        } finally {
            setLoading(false)
        }
    }

    const formatDate = (dateString) => {
        const date = new Date(dateString)
        const now = new Date()
        const diffMs = now - date
        const diffMins = Math.floor(diffMs / 60000)
        const diffHours = Math.floor(diffMs / 3600000)
        const diffDays = Math.floor(diffMs / 86400000)

        if (diffMins < 1) return 'Just now'
        if (diffMins < 60) return `${diffMins} min${diffMins > 1 ? 's' : ''} ago`
        if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
        if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
        return date.toLocaleDateString()
    }

    const getStatusBadge = (status) => {
        const styles = {
            sent: { background: 'rgba(22, 163, 74, 0.1)', color: 'var(--color-semantic-success)', border: '1px solid rgba(22, 163, 74, 0.2)' },
            failed: { background: 'rgba(220, 38, 38, 0.1)', color: 'var(--color-semantic-error)', border: '1px solid rgba(220, 38, 38, 0.2)' },
            pending: { background: 'var(--color-neutral-background)', color: 'var(--color-neutral-text-secondary)', border: '1px solid var(--color-neutral-border)' }
        }
        const style = styles[status] || styles.pending
        return (
            <span style={{
                ...style,
                padding: 'var(--spacing-xs) var(--spacing-sm)',
                borderRadius: '12px',
                fontSize: 'var(--font-size-small)',
                fontWeight: 'var(--font-weight-medium)'
            }}>
                {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
        )
    }

    if (loading && logs.length === 0) {
        return (
            <div className="logs-page">
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <div className="loading-spinner"></div>
                    <p style={{ color: 'var(--color-text-secondary)', marginTop: '16px' }}>Loading logs...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="logs-page">
            <div className="page-header">
                <h1 className="page-title">Email Logs</h1>
                <p className="page-subtitle">Track sent emails and delivery status</p>
            </div>

            {error && (
                <div style={{ padding: 'var(--spacing-sm)', background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', marginBottom: 'var(--spacing-md)', color: 'var(--color-semantic-error)' }}>
                    {error}
                </div>
            )}

            <div className="card">
                {logs.length === 0 ? (
                    <p style={{ color: 'var(--color-neutral-text-secondary)', fontStyle: 'italic', textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                        No email logs yet. Send your first campaign to see logs here.
                    </p>
                ) : (
                    <>
                        <div className="contacts-table-container">
                            <table className="contacts-table">
                                <thead>
                                    <tr>
                                        <th>Recipient</th>
                                        <th>Subject</th>
                                        <th>Status</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {logs.map((log) => (
                                        <tr key={log.id}>
                                            <td className="email-cell">{log.to_email}</td>
                                            <td>{log.subject}</td>
                                            <td>{getStatusBadge(log.status)}</td>
                                            <td className="date-cell">
                                                {log.sent_at ? formatDate(log.sent_at) : formatDate(log.created_at)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        {/* Pagination */}
                        {total > pageSize && (
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'var(--spacing-lg)', paddingTop: 'var(--spacing-lg)', borderTop: '1px solid var(--color-neutral-border)' }}>
                                <div style={{ fontSize: 'var(--font-size-body)', color: 'var(--color-neutral-text-secondary)' }}>
                                    Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, total)} of {total}
                                </div>
                                <div style={{ display: 'flex', gap: '12px' }}>
                                    <button
                                        onClick={() => setPage(page - 1)}
                                        disabled={page === 1}
                                        className="btn-secondary"
                                        style={{ padding: '8px 16px' }}
                                    >
                                        Previous
                                    </button>
                                    <button
                                        onClick={() => setPage(page + 1)}
                                        disabled={page * pageSize >= total}
                                        className="pagination-btn"
                                        style={{ padding: '8px 16px' }}
                                    >
                                        Next
                                    </button>
                                </div>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    )
}

export default Logs
