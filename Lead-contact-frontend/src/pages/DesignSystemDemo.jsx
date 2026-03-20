import React, { useState } from 'react'
import { Button, Card, Input, Textarea, Modal, Toast } from '../components/common'

function DesignSystemDemo() {
  const [showModal, setShowModal] = useState(false)
  const [showToast, setShowToast] = useState(false)
  const [toastType, setToastType] = useState('success')
  const [inputValue, setInputValue] = useState('')
  const [textareaValue, setTextareaValue] = useState('')

  const showToastMessage = (type) => {
    setToastType(type)
    setShowToast(true)
  }

  return (
    <div className="design-system-demo">
      <div className="page-header">
        <h1 className="text-h1">Design System Demo</h1>
        <p className="text-body-secondary">Showcase of the new LeadFlow design system components</p>
      </div>

      {/* Typography Section */}
      <Card className="mb-xl">
        <h2 className="text-h2 mb-lg">Typography</h2>

        <div className="mb-lg">
          <h1 className="text-h1">Heading 1 - The quick brown fox</h1>
          <p className="text-small text-muted">H1 - 32px / Semibold</p>
        </div>

        <div className="mb-lg">
          <h2 className="text-h2">Heading 2 - The quick brown fox</h2>
          <p className="text-small text-muted">H2 - 24px / Semibold</p>
        </div>

        <div className="mb-lg">
          <h3 className="text-h3">Heading 3 - The quick brown fox</h3>
          <p className="text-small text-muted">H3 - 18px / Semibold</p>
        </div>

        <div className="mb-lg">
          <p className="text-body">Body text - The quick brown fox jumps over the lazy dog. This is regular body text using the Inter font family.</p>
          <p className="text-small text-muted">Body - 14px / Regular</p>
        </div>

        <div className="mb-lg">
          <p className="text-body-secondary">Secondary body text - The quick brown fox jumps over the lazy dog.</p>
          <p className="text-small text-muted">Secondary Body - 14px / Regular / Gray</p>
        </div>

        <div>
          <p className="text-small">Small text - The quick brown fox jumps over the lazy dog.</p>
          <p className="text-small text-muted">Small - 12px / Regular</p>
        </div>
      </Card>

      {/* Colors Section */}
      <Card className="mb-xl">
        <h2 className="text-h2 mb-lg">Colors</h2>

        <div className="flex gap-md mb-lg">
          <div className="color-swatch">
            <div className="color-preview" style={{ backgroundColor: 'var(--color-brand-primary)' }}></div>
            <p className="text-small">Primary</p>
            <code className="text-small text-muted">#1D3557</code>
          </div>

          <div className="color-swatch">
            <div className="color-preview" style={{ backgroundColor: 'var(--color-brand-secondary)' }}></div>
            <p className="text-small">Secondary</p>
            <code className="text-small text-muted">#F28482</code>
          </div>

          <div className="color-swatch">
            <div className="color-preview" style={{ backgroundColor: 'var(--color-semantic-success)' }}></div>
            <p className="text-small">Success</p>
            <code className="text-small text-muted">#16A34A</code>
          </div>

          <div className="color-swatch">
            <div className="color-preview" style={{ backgroundColor: 'var(--color-semantic-error)' }}></div>
            <p className="text-small">Error</p>
            <code className="text-small text-muted">#DC2626</code>
          </div>
        </div>

        <div className="status-badges-demo">
          <span className="status-badge status-success">Success</span>
          <span className="status-badge status-warning">Warning</span>
          <span className="status-badge status-error">Error</span>
          <span className="status-badge status-info">Info</span>
        </div>
      </Card>

      {/* Buttons Section */}
      <Card className="mb-xl">
        <h2 className="text-h2 mb-lg">Buttons</h2>

        <div className="flex gap-md flex-wrap mb-lg">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="success">Success</Button>
          <Button variant="warning">Warning</Button>
          <Button variant="error">Error</Button>
          <Button variant="info">Info</Button>
        </div>

        <div className="flex gap-md flex-wrap mb-lg">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </div>

        <div className="flex gap-md flex-wrap">
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button loading disabled>Loading Disabled</Button>
        </div>
      </Card>

      {/* Form Elements Section */}
      <Card className="mb-xl">
        <h2 className="text-h2 mb-lg">Form Elements</h2>

        <div className="mb-lg">
          <Input
            label="Email Address"
            placeholder="Enter your email"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
          />
        </div>

        <div className="mb-lg">
          <Textarea
            label="Message"
            placeholder="Enter your message"
            rows={4}
            value={textareaValue}
            onChange={(e) => setTextareaValue(e.target.value)}
          />
        </div>
      </Card>

      {/* Interactive Components Section */}
      <Card className="mb-xl">
        <h2 className="text-h2 mb-lg">Interactive Components</h2>

        <div className="flex gap-md flex-wrap mb-lg">
          <Button onClick={() => setShowModal(true)}>Open Modal</Button>

          <Button onClick={() => showToastMessage('success')}>Show Success Toast</Button>
          <Button onClick={() => showToastMessage('error')}>Show Error Toast</Button>
          <Button onClick={() => showToastMessage('warning')}>Show Warning Toast</Button>
          <Button onClick={() => showToastMessage('info')}>Show Info Toast</Button>
        </div>
      </Card>

      {/* Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Demo Modal"
      >
        <p className="text-body mb-md">
          This is a demo modal using the new design system. It showcases how modals
          should look and behave in the LeadFlow application.
        </p>
        <div className="flex gap-md justify-end">
          <Button variant="secondary" onClick={() => setShowModal(false)}>
            Cancel
          </Button>
          <Button onClick={() => setShowModal(false)}>
            Confirm
          </Button>
        </div>
      </Modal>

      {/* Toast */}
      <Toast
        message={`This is a ${toastType} message!`}
        type={toastType}
        show={showToast}
        onClose={() => setShowToast(false)}
      />

      <style jsx>{`
        .color-swatch {
          text-align: center;
        }

        .color-preview {
          width: 60px;
          height: 60px;
          border-radius: 8px;
          margin-bottom: var(--spacing-sm);
          border: 1px solid var(--color-neutral-border);
        }

        .status-badges-demo {
          display: flex;
          gap: var(--spacing-sm);
          flex-wrap: wrap;
        }
      `}</style>
    </div>
  )
}

export default DesignSystemDemo
