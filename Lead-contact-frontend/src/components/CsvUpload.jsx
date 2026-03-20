import { useState, useRef } from 'react'
import { apiUrl } from '../utils/api'
import './CsvUpload.css'

function CsvUpload({ userId, onUploadComplete }) {
  const [file, setFile] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [uploadResult, setUploadResult] = useState(null)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (selectedFile) => {
    setError(null)
    setUploadResult(null)

    // Validate file type
    const fileName = selectedFile.name.toLowerCase()
    if (!fileName.endsWith('.csv') && !fileName.endsWith('.txt')) {
      setError('Please select a CSV file (.csv or .txt)')
      return
    }

    // Validate file size (5MB)
    if (selectedFile.size > 5 * 1024 * 1024) {
      setError('File size must be less than 5MB')
      return
    }

    setFile(selectedFile)
  }

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first')
      return
    }

    setUploading(true)
    setError(null)
    setUploadResult(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(apiUrl('/api/contacts/upload'), {
        method: 'POST',
        headers: {
          'X-User-Id': userId
        },
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        setUploadResult(data)
        setFile(null)
        if (fileInputRef.current) {
          fileInputRef.current.value = ''
        }

        // Notify parent component
        if (onUploadComplete) {
          onUploadComplete(data)
        }
      } else {
        setError(data.detail || 'Upload failed')
      }
    } catch (err) {
      console.error('Upload error:', err)
      setError('Failed to upload file. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="csv-upload-container">
      <h3>Upload Contacts</h3>
      <p className="csv-upload-subtitle">
        Import your contacts from a CSV file
      </p>

      {/* Drag and drop area */}
      <div
        className={`csv-dropzone ${dragActive ? 'active' : ''} ${file ? 'has-file' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.txt"
          onChange={handleFileInputChange}
          style={{ display: 'none' }}
        />

        {file ? (
          <div className="csv-file-info">
            <div className="csv-file-name">{file.name}</div>
            <div className="csv-file-size">
              {(file.size / 1024).toFixed(2)} KB
            </div>
          </div>
        ) : (
          <div className="csv-dropzone-content">
            <p className="csv-dropzone-text">
              Drag and drop your CSV file here
            </p>
            <p className="csv-dropzone-subtext">or click to browse</p>
            <p className="csv-file-requirements">
              CSV format • Max 5MB
            </p>
          </div>
        )}
      </div>

      {/* Upload button */}
      {file && (
        <button
          className="csv-upload-button"
          onClick={handleUpload}
          disabled={uploading}
        >
          {uploading ? (
            <>
              <div className="loading-spinner-small"></div>
              Uploading...
            </>
          ) : (
            'Upload Contacts'
          )}
        </button>
      )}

      {/* Error message */}
      {error && (
        <div className="csv-message csv-error">
          <span className="csv-message-icon">!</span>
          {error}
        </div>
      )}

      {/* Success message */}
      {uploadResult && (
        <div className="csv-message csv-success">
          <span className="csv-message-icon">✓</span>
          <div className="csv-result-details">
            <div className="csv-result-title">{uploadResult.message}</div>
            <div className="csv-result-stats">
              <span>Total: {uploadResult.total_rows}</span>
              <span>Imported: {uploadResult.imported}</span>
              {uploadResult.duplicates > 0 && (
                <span>Duplicates: {uploadResult.duplicates}</span>
              )}
              {uploadResult.invalid > 0 && (
                <span>Invalid: {uploadResult.invalid}</span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* CSV format help */}
      <div className="csv-format-help">
        <details>
          <summary>Expected CSV format</summary>
          <pre className="csv-format-example">{`email,name,company,phone
john@example.com,John Doe,Acme Inc,+1234567890
jane@example.com,Jane Smith,Tech Corp,+1234567891`}</pre>
          <p className="csv-format-note">
            <strong>email</strong> is required. Other fields are optional.
            Additional columns will be saved as custom fields.
          </p>
        </details>
      </div>
    </div>
  )
}

export default CsvUpload
