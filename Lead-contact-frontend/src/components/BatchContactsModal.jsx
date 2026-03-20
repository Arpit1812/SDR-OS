import { useEffect } from 'react'
import ContactsTable from './ContactsTable'
import './Modal.css'

function BatchContactsModal({ batch, contacts, total, onClose, onDelete, loading }) {
    useEffect(() => {
        // Prevent body scroll when modal is open
        document.body.style.overflow = 'hidden'
        return () => {
            document.body.style.overflow = 'unset'
        }
    }, [])

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose()
        }
    }

    return (
        <div className="modal-backdrop" onClick={handleBackdropClick}>
            <div className="modal-content">
                <div className="modal-header">
                    <div>
                        <h2 className="modal-title">{batch.filename}</h2>
                        <p className="modal-subtitle">
                            {batch.imported_count} contacts imported
                            {batch.duplicate_count > 0 && ` • ${batch.duplicate_count} duplicates`}
                            {batch.invalid_count > 0 && ` • ${batch.invalid_count} invalid`}
                        </p>
                    </div>
                    <button onClick={onClose} className="modal-close">
                        ×
                    </button>
                </div>

                <div className="modal-body">
                    {loading ? (
                        <div style={{ textAlign: 'center', padding: '40px 0' }}>
                            <div className="loading-spinner"></div>
                            <p style={{ marginTop: '20px', color: '#737373' }}>Loading contacts...</p>
                        </div>
                    ) : contacts.length === 0 ? (
                        <p style={{ color: '#737373', fontStyle: 'italic', padding: '40px 0', textAlign: 'center' }}>
                            No contacts found in this batch.
                        </p>
                    ) : (
                        <ContactsTable
                            contacts={contacts}
                            onDelete={onDelete}
                        />
                    )}
                </div>

                <div className="modal-footer">
                    <button onClick={onClose} className="btn-secondary">
                        Close
                    </button>
                </div>
            </div>
        </div>
    )
}

export default BatchContactsModal
