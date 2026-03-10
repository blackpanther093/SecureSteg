import React, { useRef, useState } from 'react'
import { Upload, FileText, Image as ImageIcon } from 'lucide-react'

export const UploadDropzone = ({
  title,
  description,
  file,
  accept,
  onFileSelect,
  kind = 'default',
  buttonLabel = 'Choose file',
}) => {
  const inputRef = useRef(null)
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (event) => {
    event.preventDefault()
    event.stopPropagation()

    if (event.type === 'dragenter' || event.type === 'dragover') {
      setDragActive(true)
      return
    }

    setDragActive(false)
  }

  const handleDrop = (event) => {
    event.preventDefault()
    event.stopPropagation()
    setDragActive(false)

    const droppedFile = event.dataTransfer.files?.[0]
    if (droppedFile) {
      onFileSelect(droppedFile)
    }
  }

  const Icon = kind === 'image' ? ImageIcon : FileText

  return (
    <div
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={`upload-dropzone ${dragActive ? 'upload-dropzone-active' : ''}`}
      role="button"
      tabIndex={0}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          inputRef.current?.click()
        }
      }}
    >
      <div className="upload-dropzone__icon-wrap">
        {file ? <Icon className="h-6 w-6" /> : <Upload className="h-6 w-6" />}
      </div>

      <div className="space-y-1">
        <p className="upload-dropzone__title">{file ? file.name : title}</p>
        <p className="upload-dropzone__meta">
          {file
            ? `${(file.size / 1024).toFixed(2)} KB`
            : description}
        </p>
      </div>

      <button type="button" className="btn-secondary btn-compact pointer-events-none">
        {buttonLabel}
      </button>

      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={(event) => onFileSelect(event.target.files?.[0] || null)}
      />
    </div>
  )
}
