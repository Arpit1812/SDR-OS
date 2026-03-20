import React from 'react'
import './Input.css'

const Input = ({
  label,
  error,
  className = '',
  ...props
}) => {
  const inputId = props.id || `input-${Math.random().toString(36).substr(2, 9)}`

  return (
    <div className={`input-group ${className}`}>
      {label && (
        <label htmlFor={inputId} className="input-label">
          {label}
        </label>
      )}
      <input
        id={inputId}
        className={`input ${error ? 'input-error' : ''}`}
        {...props}
      />
      {error && (
        <span className="input-error-message">{error}</span>
      )}
    </div>
  )
}

export default Input
