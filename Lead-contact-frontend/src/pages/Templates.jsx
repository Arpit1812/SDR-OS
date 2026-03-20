import { useState, useEffect } from 'react'
import { Button, Card, Input, Textarea } from '../components/common'
import { apiUrl } from '../utils/api'

function Templates() {
    const [templates, setTemplates] = useState([])
    const [isEditing, setIsEditing] = useState(false)
    const [currentTemplate, setCurrentTemplate] = useState({ id: null, name: '', subject: '', body: '' })
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [userId, setUserId] = useState(null)

    useEffect(() => {
        // Get user from localStorage
        const savedUser = localStorage.getItem('user')
        if (savedUser) {
            const user = JSON.parse(savedUser)
            setUserId(user.id)
            loadTemplates(user.id)
        } else {
            setLoading(false)
        }
    }, [])

    const loadTemplates = async (uid) => {
        setLoading(true)
        setError(null)
        
        try {
            const response = await fetch(apiUrl('/api/templates'), {
                headers: { 'X-User-Id': uid }
            })
            
            if (response.ok) {
                const data = await response.json()
                setTemplates(data.templates)
            } else {
                setError('Failed to load templates')
            }
        } catch (err) {
            console.error('Error loading templates:', err)
            setError('Failed to load templates')
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        if (!userId) return
        
        try {
            const url = currentTemplate.id 
                ? apiUrl(`/api/templates/${currentTemplate.id}`)
                : apiUrl('/api/templates')
            
            const method = currentTemplate.id ? 'PUT' : 'POST'
            
            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Id': userId
                },
                body: JSON.stringify({
                    name: currentTemplate.name,
                    subject: currentTemplate.subject,
                    body: currentTemplate.body
                })
            })
            
            if (response.ok) {
                await loadTemplates(userId)
                setIsEditing(false)
                setCurrentTemplate({ id: null, name: '', subject: '', body: '' })
            } else {
                const data = await response.json()
                alert(data.detail || 'Failed to save template')
            }
        } catch (err) {
            console.error('Error saving template:', err)
            alert('Failed to save template')
        }
    }

    const handleEdit = (template) => {
        setCurrentTemplate({
            id: template.id,
            name: template.name,
            subject: template.subject,
            body: template.body
        })
        setIsEditing(true)
    }

    const handleDelete = async (templateId) => {
        if (!confirm('Are you sure you want to delete this template?')) return
        
        try {
            const response = await fetch(apiUrl(`/api/templates/${templateId}`), {
                method: 'DELETE',
                headers: { 'X-User-Id': userId }
            })
            
            if (response.ok) {
                await loadTemplates(userId)
            } else {
                alert('Failed to delete template')
            }
        } catch (err) {
            console.error('Error deleting template:', err)
            alert('Failed to delete template')
        }
    }

    const handleCancel = () => {
        setIsEditing(false)
        setCurrentTemplate({ id: null, name: '', subject: '', body: '' })
    }

    if (loading) {
        return (
            <div className="templates-page">
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <div className="loading-spinner"></div>
                    <p style={{ color: 'var(--color-text-secondary)', marginTop: '16px' }}>Loading templates...</p>
                </div>
            </div>
        )
    }

    return (
        <div className="templates-page">
            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="page-title">Templates</h1>
                    <p className="page-subtitle">Create and manage email templates</p>
                </div>
                {!isEditing && (
                    <Button onClick={() => setIsEditing(true)}>
                        Create Template
                    </Button>
                )}
            </div>

            {error && (
                <div style={{ padding: 'var(--spacing-sm)', background: 'rgba(220, 38, 38, 0.1)', border: '1px solid rgba(220, 38, 38, 0.2)', borderRadius: '8px', marginBottom: 'var(--spacing-md)', color: 'var(--color-semantic-error)' }}>
                    {error}
                </div>
            )}

            {isEditing ? (
                <Card>
                    <h3 className="text-h3 mb-lg">{currentTemplate.id ? 'Edit Template' : 'New Template'}</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)', marginTop: 'var(--spacing-lg)' }}>
                        <Input
                            label="Template Name"
                            value={currentTemplate.name}
                            onChange={(e) => setCurrentTemplate({ ...currentTemplate, name: e.target.value })}
                            placeholder="e.g., Welcome Email"
                        />
                        <Input
                            label="Subject Line"
                            value={currentTemplate.subject}
                            onChange={(e) => setCurrentTemplate({ ...currentTemplate, subject: e.target.value })}
                            placeholder="e.g., Welcome to our service!"
                        />
                        <Textarea
                            label="Email Body"
                            value={currentTemplate.body}
                            onChange={(e) => setCurrentTemplate({ ...currentTemplate, body: e.target.value })}
                            rows={8}
                            placeholder="Hello {{name}}, ..."
                        />
                        <p style={{ fontSize: 'var(--font-size-small)', color: 'var(--color-neutral-text-secondary)', marginTop: 'var(--spacing-xs)' }}>
                            Use <code style={{ background: 'var(--color-neutral-background)', padding: '2px 6px', borderRadius: '3px' }}>{`{{variable}}`}</code> to insert dynamic content.
                        </p>
                        <div style={{ display: 'flex', gap: 'var(--spacing-sm)', marginTop: 'var(--spacing-sm)', paddingTop: 'var(--spacing-lg)', borderTop: '1px solid var(--color-neutral-border)' }}>
                            <Button
                                onClick={handleSave}
                                disabled={!currentTemplate.name || !currentTemplate.subject || !currentTemplate.body}
                            >
                                {currentTemplate.id ? 'Update Template' : 'Save Template'}
                            </Button>
                            <Button
                                variant="secondary"
                                onClick={handleCancel}
                            >
                                Cancel
                            </Button>
                        </div>
                    </div>
                </Card>
            ) : (
                <Card>
                    {templates.length === 0 ? (
                        <p style={{ color: 'var(--color-neutral-text-secondary)', fontStyle: 'italic', textAlign: 'center', padding: 'var(--spacing-xl)' }}>
                            No templates created yet. Click "Create Template" to get started.
                        </p>
                    ) : (
                        <div className="contacts-table-container">
                            <table className="contacts-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Created At</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {templates.map((t) => (
                                        <tr key={t.id}>
                                            <td>{t.name}</td>
                                            <td className="date-cell">{new Date(t.created_at).toLocaleDateString()}</td>
                                            <td>
                                                <div style={{ display: 'flex', gap: 'var(--spacing-sm)' }}>
                                                    <Button
                                                        variant="secondary"
                                                        size="sm"
                                                        onClick={() => handleEdit(t)}
                                                    >
                                                        Edit
                                                    </Button>
                                                    <Button
                                                        variant="error"
                                                        size="sm"
                                                        onClick={() => handleDelete(t.id)}
                                                    >
                                                        Delete
                                                    </Button>
                                                </div>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </Card>
            )}
        </div>
    )
}

export default Templates
