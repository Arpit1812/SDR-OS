import React from 'react'
import './Textarea.css'

const Textarea = ({
  label,
  error,
  className = '',
  rows = 4,
  ...props
}) => {
  const textareaId = props.id || `textarea-${Math.random().toString(36).substr(2, 9)}`

  return (
    <div className={`textarea-group ${className}`}>
      {label && (
        <label htmlFor={textareaId} className="textarea-label">
          {label}
        </label>
      )}
      <textarea
        id={textareaId}
        className={`textarea ${error ? 'textarea-error' : ''}`}
        rows={rows}
        {...props}
      />
      {error && (
        <span className="textarea-error-message">{error}</span>
      )}
    </div>
  )
}

export default Textarea
