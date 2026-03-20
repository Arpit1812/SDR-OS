import { useState, useEffect } from 'react'
import { apiUrl } from '../utils/api'

function SendEmails() {
    const [step, setStep] = useState(1)
    const [selectedBatch, setSelectedBatch] = useState('')
    const [selectedTemplate, setSelectedTemplate] = useState('')
    const [selectedPrompt, setSelectedPrompt] = useState('')
    const [csvUploads, setCsvUploads] = useState([])
    const [templates, setTemplates] = useState([])
    const [prompts, setPrompts] = useState([])
    const [preview, setPreview] = useState(null)
    const [loading, setLoading] = useState(false)
    const [sending, setSending] = useState(false)
    const [result, setResult] = useState(null)
    const [userId, setUserId] = useState(null)

    useEffect(() => {
        const savedUser = localStorage.getItem('user')
        if (savedUser) {
            const user = JSON.parse(savedUser)
            setUserId(user.id)
            loadData(user.id)
        }
    }, [])

    const loadData = async (uid) => {
        try {
            // Load CSV uploads
            const csvResponse = await fetch(apiUrl('/api/contacts/uploads'), {
                headers: { 'X-User-Id': uid }
            })
            if (csvResponse.ok) {
                const csvData = await csvResponse.json()
                setCsvUploads(csvData.uploads)
            }

            // Load templates
            const templateResponse = await fetch(apiUrl('/api/templates'), {
                headers: { 'X-User-Id': uid }
            })
            if (templateResponse.ok) {
                const templateData = await templateResponse.json()
                setTemplates(templateData.templates)
            }

            // Load prompts
            const promptResponse = await fetch(apiUrl('/api/prompts'), {
                headers: { 'X-User-Id': uid }
            })
            if (promptResponse.ok) {
                const promptData = await promptResponse.json()
                setPrompts(promptData.prompts)
                // Auto-select default prompt if exists
                const defaultPrompt = promptData.prompts.find(p => p.is_default)
                if (defaultPrompt) {
                    setSelectedPrompt(defaultPrompt.id)
                }
            }
        } catch (err) {
            console.error('Error loading data:', err)
        }
    }

    const loadPreview = async () => {
        if (!selectedBatch || !selectedTemplate || !userId) return

        setLoading(true)
        try {
            const response = await fetch(apiUrl('/api/campaigns/preview'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Id': userId
                },
                body: JSON.stringify({
                    csv_source: selectedBatch,
                    template_id: selectedTemplate
                })
            })

            if (response.ok) {
                const data = await response.json()
                setPreview(data)
            } else {
                alert('Failed to load preview')
            }
        } catch (err) {
            console.error('Error loading preview:', err)
            alert('Failed to load preview')
        } finally {
            setLoading(false)
        }
    }

    const handleNext = () => {
        if (step === 3) {
            loadPreview()
        }
        setStep(step + 1)
    }

    const handleBack = () => setStep(step - 1)

    const handleSendCampaign = async () => {
        if (!userId || !selectedBatch || !selectedTemplate) return

        setSending(true)
        try {
            const response = await fetch(apiUrl('/api/campaigns/send'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Id': userId
                },
                body: JSON.stringify({
                    csv_source: selectedBatch,
                    template_id: selectedTemplate,
                    prompt_id: selectedPrompt || null  // Include selected prompt
                })
            })

            const data = await response.json()
            setResult(data)
        } catch (err) {
            console.error('Error sending campaign:', err)
            alert('Failed to send campaign')
        } finally {
            setSending(false)
        }
    }

    const stepLabels = ['Select Batch', 'Select Template', 'Select AI Prompt', 'Preview', 'Send']

    const selectedCsvName = csvUploads.find(c => c.source === selectedBatch)?.source || ''
    const selectedTemplateName = templates.find(t => t.id === selectedTemplate)?.name || ''
    const selectedPromptName = prompts.find(p => p.id === selectedPrompt)?.name || 'System Default'
    const contactCount = csvUploads.find(c => c.source === selectedBatch)?.contact_count || 0

    return (
        <div className="send-emails-page">
            <div className="page-header">
                <h1 className="page-title">Send Emails</h1>
                <p className="page-subtitle">Launch your email campaign</p>
            </div>

            {/* Progress Steps */}
            <div style={{ display: 'flex', marginBottom: '32px', gap: '8px', flexWrap: 'wrap' }}>
                {[1, 2, 3, 4, 5].map(s => (
                    <div key={s} style={{
                        flex: 1,
                        minWidth: '120px',
                        padding: '12px 8px',
                        background: step >= s ? 'var(--color-text-neutral)' : 'var(--color-white)',
                        color: step >= s ? 'var(--color-white)' : 'var(--color-text-secondary)',
                        border: `1px solid ${step >= s ? 'var(--color-text-neutral)' : 'var(--color-border)'}`,
                        borderRadius: '6px',
                        fontWeight: '500',
                        fontSize: '13px',
                        textAlign: 'center',
                        transition: 'all 0.2s'
                    }}>
                        {s}. {stepLabels[s - 1]}
                    </div>
                ))}
            </div>

            <div className="card">
                {step === 1 && (
                    <div>
                        <h3>Select Contact Batch</h3>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
                            Choose which contacts to send emails to
                        </p>
                        <div style={{ marginTop: '16px' }}>
                            <select
                                value={selectedBatch}
                                onChange={(e) => setSelectedBatch(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '12px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '14px',
                                    fontFamily: 'inherit',
                                    background: 'var(--color-white)'
                                }}
                            >
                                <option value="">-- Select a CSV Batch --</option>
                                {csvUploads.map((upload) => (
                                    <option key={upload.source} value={upload.source}>
                                        {upload.source} ({upload.contact_count} contacts)
                                    </option>
                                ))}
                            </select>
                            {csvUploads.length === 0 && (
                                <p style={{ marginTop: '12px', color: 'var(--color-text-secondary)', fontSize: '14px' }}>
                                    No CSV uploads found. Please upload contacts first.
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {step === 2 && (
                    <div>
                        <h3>Select Email Template</h3>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
                            Choose the email template to use
                        </p>
                        <div style={{ marginTop: '16px' }}>
                            <select
                                value={selectedTemplate}
                                onChange={(e) => setSelectedTemplate(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '12px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '14px',
                                    fontFamily: 'inherit',
                                    background: 'var(--color-white)'
                                }}
                            >
                                <option value="">-- Select a Template --</option>
                                {templates.map((template) => (
                                    <option key={template.id} value={template.id}>
                                        {template.name}
                                    </option>
                                ))}
                            </select>
                            {templates.length === 0 && (
                                <p style={{ marginTop: '12px', color: 'var(--color-text-secondary)', fontSize: '14px' }}>
                                    No templates found. Please create a template first.
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div>
                        <h3>Select AI Prompt</h3>
                        <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px', marginBottom: '16px' }}>
                            Choose how the AI should respond to replies (for auto-reply feature)
                        </p>
                        <div style={{ marginTop: '16px' }}>
                            <select
                                value={selectedPrompt}
                                onChange={(e) => setSelectedPrompt(e.target.value)}
                                style={{
                                    width: '100%',
                                    padding: '12px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border)',
                                    fontSize: '14px',
                                    fontFamily: 'inherit',
                                    background: 'var(--color-white)'
                                }}
                            >
                                <option value="">System Default (Built-in prompt)</option>
                                {prompts.map((prompt) => (
                                    <option key={prompt.id} value={prompt.id}>
                                        {prompt.name} {prompt.is_default ? '(Your Default)' : ''}
                                    </option>
                                ))}
                            </select>

                            {/* Show selected prompt preview */}
                            {selectedPrompt && (
                                <div style={{
                                    marginTop: '16px',
                                    padding: '16px',
                                    background: 'var(--color-bg-warm)',
                                    border: '1px solid var(--color-border)',
                                    borderRadius: '6px'
                                }}>
                                    <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                                        Prompt Preview:
                                    </p>
                                    <code style={{
                                        fontSize: '12px',
                                        color: 'var(--color-text-neutral)',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                    }}>
                                        {prompts.find(p => p.id === selectedPrompt)?.prompt_text?.substring(0, 200)}...
                                    </code>
                                </div>
                            )}

                            <p style={{ marginTop: '16px', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                                The AI prompt controls how auto-replies are generated when contacts respond to your emails.
                                <br />
                                <a href="/prompts" style={{ color: 'var(--color-text-neutral)' }}>Manage your prompts →</a>
                            </p>
                        </div>
                    </div>
                )}

                {step === 4 && (
                    <div>
                        <h3>Preview Campaign</h3>
                        {loading ? (
                            <div style={{ textAlign: 'center', padding: '40px' }}>
                                <div className="loading-spinner"></div>
                                <p style={{ color: 'var(--color-text-secondary)', marginTop: '16px' }}>Loading preview...</p>
                            </div>
                        ) : preview ? (
                            <div style={{
                                marginTop: '24px',
                                padding: '24px',
                                border: '1px solid var(--color-border)',
                                borderRadius: '6px',
                                background: 'var(--color-bg-warm)'
                            }}>
                                <p style={{ marginBottom: '12px' }}><strong>To:</strong> {preview.to}</p>
                                <p style={{ marginBottom: '12px' }}><strong>Subject:</strong> {preview.subject}</p>
                                <hr style={{ margin: '16px 0', border: 'none', borderTop: '1px solid var(--color-border)' }} />
                                <div style={{ minHeight: '100px', color: 'var(--color-text-neutral)', whiteSpace: 'pre-wrap' }}>
                                    {preview.body}
                                </div>
                                <p style={{ marginTop: '16px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>
                                    Preview shown with first contact from {selectedCsvName}
                                </p>
                            </div>
                        ) : (
                            <p style={{ marginTop: '24px', color: 'var(--color-text-secondary)' }}>No preview available</p>
                        )}
                    </div>
                )}

                {step === 5 && !result && (
                    <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <h3 style={{ marginBottom: '16px' }}>Ready to Launch?</h3>
                        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '8px' }}>
                            You are about to send emails to <strong>{contactCount} contacts</strong>.
                        </p>
                        <div style={{
                            color: 'var(--color-text-secondary)',
                            marginBottom: '32px',
                            fontSize: '14px',
                            background: 'var(--color-bg-warm)',
                            padding: '16px',
                            borderRadius: '6px',
                            display: 'inline-block',
                            textAlign: 'left'
                        }}>
                            <p><strong>CSV:</strong> {selectedCsvName}</p>
                            <p><strong>Template:</strong> {selectedTemplateName}</p>
                            <p><strong>AI Prompt:</strong> {selectedPromptName}</p>
                        </div>
                        <div>
                            <button
                                className="pagination-btn"
                                style={{ padding: '16px 48px', fontSize: '16px' }}
                                onClick={handleSendCampaign}
                                disabled={sending}
                            >
                                {sending ? 'Sending...' : 'Send Campaign'}
                            </button>
                        </div>
                    </div>
                )}

                {step === 5 && result && (
                    <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <div style={{ fontSize: '48px', marginBottom: '16px' }}>
                            {result.success ? '✓' : '✕'}
                        </div>
                        <h3 style={{ marginBottom: '16px' }}>
                            {result.success ? 'Campaign Queued!' : 'Campaign Failed'}
                        </h3>
                        <p style={{ color: 'var(--color-text-secondary)', marginBottom: '24px' }}>
                            {result.message}
                        </p>
                        <div style={{ display: 'inline-flex', gap: '24px', marginBottom: '32px' }}>
                            <div>
                                <div style={{ fontSize: '24px', fontWeight: '600' }}>{result.total || contactCount}</div>
                                <div style={{ fontSize: '14px', color: 'var(--color-text-secondary)' }}>Total</div>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                            <button
                                className="btn-secondary"
                                onClick={() => window.location.href = '/campaigns'}
                                style={{ padding: '12px 32px' }}
                            >
                                View Campaigns
                            </button>
                            <button
                                className="pagination-btn"
                                onClick={() => {
                                    setStep(1)
                                    setResult(null)
                                    setSelectedBatch('')
                                    setSelectedTemplate('')
                                }}
                                style={{ padding: '12px 32px' }}
                            >
                                New Campaign
                            </button>
                        </div>
                    </div>
                )}

                <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginTop: '32px',
                    borderTop: '1px solid var(--color-border)',
                    paddingTop: '24px'
                }}>
                    <button
                        onClick={handleBack}
                        disabled={step === 1}
                        className="btn-secondary"
                        style={{ padding: '12px 24px' }}
                    >
                        Back
                    </button>
                    {step < 5 && (
                        <button
                            onClick={handleNext}
                            className="pagination-btn"
                            style={{ padding: '12px 24px' }}
                            disabled={
                                (step === 1 && !selectedBatch) ||
                                (step === 2 && !selectedTemplate)
                            }
                        >
                            Next Step
                        </button>
                    )}
                </div>
            </div>
        </div>
    )
}

export default SendEmails
