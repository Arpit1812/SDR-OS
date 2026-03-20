import { useState, useEffect } from 'react'
import { apiUrl } from '../utils/api'
import './ContactModal.css'

function ContactModal({ isOpen, onClose, csvSource, userId }) {
  const [contacts, setContacts] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalContacts, setTotalContacts] = useState(0)
  const pageSize = 50

  useEffect(() => {
    if (isOpen && csvSource) {
      loadContacts()
    }
  }, [isOpen, csvSource, page])

  const loadContacts = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        apiUrl(`/api/contacts/by-source/${encodeURIComponent(csvSource)}?page=${page}&page_size=${pageSize}`),
        {
          headers: {
            'X-User-Id': userId
          }
        }
      )

      if (response.ok) {
        const data = await response.json()
        setContacts(data.contacts)
        setTotalContacts(data.total)
      } else {
        setError('Failed to load contacts')
      }
    } catch (err) {
      console.error('Error loading contacts:', err)
      setError('Failed to load contacts')
    } finally {
      setLoading(false)
    }
  }

  const handleClose = () => {
    setPage(1)
    setContacts([])
    setError(null)
    onClose()
  }

  const handleNextPage = () => {
    if (page * pageSize < totalContacts) {
      setPage(page + 1)
    }
  }

  const handlePrevPage = () => {
    if (page > 1) {
      setPage(page - 1)
    }
  }

  if (!isOpen) return null

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title">{csvSource}</h2>
            <p className="modal-subtitle">{totalContacts} contacts</p>
          </div>
          <button className="modal-close" onClick={handleClose}>
            ×
          </button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="modal-loading">
              <div className="loading-spinner"></div>
              <p>Loading contacts...</p>
            </div>
          )}

          {error && (
            <div className="modal-error">
              <span className="error-icon">!</span>
              {error}
            </div>
          )}

          {!loading && !error && contacts.length > 0 && (
            <div className="contacts-table-container">
              <table className="contacts-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Company</th>
                    <th>Phone</th>
                  </tr>
                </thead>
                <tbody>
                  {contacts.map((contact) => (
                    <tr key={contact.id}>
                      <td className="contact-email">{contact.email}</td>
                      <td>{contact.name || '-'}</td>
                      <td>{contact.company || '-'}</td>
                      <td>{contact.phone || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && !error && contacts.length === 0 && (
            <div className="modal-empty">
              <p>No contacts found</p>
            </div>
          )}
        </div>

        {!loading && !error && totalContacts > pageSize && (
          <div className="modal-footer">
            <div className="pagination-info">
              Showing {(page - 1) * pageSize + 1} - {Math.min(page * pageSize, totalContacts)} of {totalContacts}
            </div>
            <div className="pagination-controls">
              <button
                className="pagination-button"
                onClick={handlePrevPage}
                disabled={page === 1}
              >
                Previous
              </button>
              <span className="pagination-page">Page {page}</span>
              <button
                className="pagination-button"
                onClick={handleNextPage}
                disabled={page * pageSize >= totalContacts}
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ContactModal

