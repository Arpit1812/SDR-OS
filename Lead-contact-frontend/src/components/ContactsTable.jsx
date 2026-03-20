import { useState } from 'react'
import './ContactsTable.css'

function ContactsTable({ contacts, onDelete }) {
    const [sortField, setSortField] = useState('created_at')
    const [sortDirection, setSortDirection] = useState('desc')

    const handleSort = (field) => {
        if (sortField === field) {
            setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
        } else {
            setSortField(field)
            setSortDirection('asc')
        }
    }

    const sortedContacts = [...contacts].sort((a, b) => {
        let aVal = a[sortField]
        let bVal = b[sortField]

        // Handle null/undefined values
        if (!aVal) return 1
        if (!bVal) return -1

        // Handle dates
        if (sortField === 'created_at' || sortField === 'updated_at') {
            aVal = new Date(aVal)
            bVal = new Date(bVal)
        }

        // Handle strings
        if (typeof aVal === 'string') {
            aVal = aVal.toLowerCase()
            bVal = bVal.toLowerCase()
        }

        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
        return 0
    })

    const formatDate = (dateString) => {
        const date = new Date(dateString)
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const handleDelete = (contact) => {
        if (window.confirm(`Are you sure you want to delete ${contact.email}?`)) {
            onDelete(contact.id)
        }
    }

    const SortIcon = ({ field }) => {
        if (sortField !== field) return <span className="sort-icon">↕</span>
        return sortDirection === 'asc' ?
            <span className="sort-icon active">↑</span> :
            <span className="sort-icon active">↓</span>
    }

    return (
        <div className="contacts-table-container">
            <table className="contacts-table">
                <thead>
                    <tr>
                        <th onClick={() => handleSort('email')} className="sortable">
                            Email <SortIcon field="email" />
                        </th>
                        <th onClick={() => handleSort('name')} className="sortable">
                            Name <SortIcon field="name" />
                        </th>
                        <th onClick={() => handleSort('company')} className="sortable">
                            Company <SortIcon field="company" />
                        </th>
                        <th onClick={() => handleSort('phone')} className="sortable">
                            Phone <SortIcon field="phone" />
                        </th>
                        <th onClick={() => handleSort('source')} className="sortable">
                            Source <SortIcon field="source" />
                        </th>
                        <th onClick={() => handleSort('created_at')} className="sortable">
                            Created <SortIcon field="created_at" />
                        </th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {sortedContacts.map((contact) => (
                        <tr key={contact.id}>
                            <td className="email-cell">{contact.email}</td>
                            <td>{contact.name || '-'}</td>
                            <td>{contact.company || '-'}</td>
                            <td>{contact.phone || '-'}</td>
                            <td>
                                <span className="source-badge">
                                    {contact.source}
                                </span>
                            </td>
                            <td className="date-cell">
                                {formatDate(contact.created_at)}
                            </td>
                            <td>
                                <button
                                    onClick={() => handleDelete(contact)}
                                    className="delete-btn"
                                    title="Delete contact"
                                >
                                    Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
}

export default ContactsTable
