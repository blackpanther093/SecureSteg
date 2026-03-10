import React, { useState } from 'react'
import { AlertCircle, CheckCircle, KeyRound, LockKeyhole, SlidersHorizontal } from 'lucide-react'
import toast from 'react-hot-toast'
import { secureStegAPI } from '../api/client'
import { useAppStore } from '../store'
import { UploadDropzone } from './UploadDropzone'

const encryptionModes = [
  {
    id: 'none',
    label: 'No Credentials',
    description: 'Extract later without a password or recovery key.',
  },
  {
    id: 'auto',
    label: 'Auto Key',
    description: 'Generate a recovery key for this hidden payload.',
  },
  {
    id: 'manual',
    label: 'Password',
    description: 'Encrypt with your own password.',
  },
]

export const EmbedMode = () => {
  const {
    embedFile,
    setEmbedFile,
    secretMessage,
    setSecretMessage,
    embedPassword,
    setEmbedPassword,
    setRecoveryKey,
    embeddingMethod,
    setEmbeddingMethod,
    compressionEnabled,
    setCompressionEnabled,
    capacityInfo,
    setCapacityInfo,
    embedResult,
    setEmbedResult,
    isLoading,
    setIsLoading,
    error,
    setError,
  } = useAppStore()

  const [contentMode, setContentMode] = useState('text')
  const [secretFileToHide, setSecretFileToHide] = useState(null)
  const [encryptionMode, setEncryptionMode] = useState('none')
  const [decodeLimit, setDecodeLimit] = useState(0)
  const [timeLimitHours, setTimeLimitHours] = useState(0)

  const processCoverImage = async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      toast.error('Select a valid cover image')
      return
    }

    setEmbedFile(file)
    setEmbedResult(null)
    setError(null)

    const loadingToast = toast.loading('Calculating image capacity...')
    try {
      const response = await secureStegAPI.capacity(file)
      setCapacityInfo(response.data)
      toast.success('Cover image ready', { id: loadingToast })
    } catch (err) {
      const message = err.response?.data?.detail || 'Capacity analysis failed'
      setError(message)
      toast.error(message, { id: loadingToast })
    }
  }

  const handleEmbed = async () => {
    if (!embedFile) {
      setError('Select a cover image first')
      return
    }

    if (contentMode === 'text' && !secretMessage.trim()) {
      setError('Enter text to hide')
      return
    }

    if (contentMode === 'file' && !secretFileToHide) {
      setError('Select a file to hide')
      return
    }

    if (encryptionMode === 'manual' && !embedPassword.trim()) {
      setError('Enter a password for manual encryption')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await secureStegAPI.embed(
        embedFile,
        contentMode === 'text' ? secretMessage : '',
        embedPassword,
        embeddingMethod,
        compressionEnabled,
        {
          encryptionMode,
          selfDestructMode: 'unlimited',
          decodeLimit,
          timeLimitHours,
          watermarkMode: 'hidden',
          secretFile: contentMode === 'file' ? secretFileToHide : null,
          isFile: contentMode === 'file',
          filename: secretFileToHide?.name,
        }
      )

      setEmbedResult(response.data)
      setRecoveryKey(response.data.recovery_key || '')
      toast.success('Payload hidden successfully')
    } catch (err) {
      const message = err.response?.data?.detail || 'Embedding failed'
      setError(message)
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const maxCapacity = capacityInfo?.capacities?.multi_layer?.max_capacity_kb || 0
  const contentSizeKb = contentMode === 'file' && secretFileToHide
    ? secretFileToHide.size / 1024
    : new Blob([secretMessage]).size / 1024

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <article className="panel space-y-5">
          <div className="section-heading">
            <h2 className="section-title">Hide Payload</h2>
            <p className="section-copy">Select a cover image, choose text or file mode, then configure encryption and access limits.</p>
          </div>

          <UploadDropzone
            title="Drop cover image or click to browse"
            description="Supports PNG, JPG, BMP, GIF, and TIFF cover images."
            file={embedFile}
            accept="image/*"
            onFileSelect={processCoverImage}
            kind="image"
            buttonLabel="Choose image"
          />

          <div className="grid gap-4 lg:grid-cols-[0.76fr_1fr]">
            <div className="subpanel space-y-4">
              <div className="tab-strip">
                <button
                  type="button"
                  className={`tab-button ${contentMode === 'text' ? 'tab-button-active' : ''}`}
                  onClick={() => setContentMode('text')}
                >
                  Text
                </button>
                <button
                  type="button"
                  className={`tab-button ${contentMode === 'file' ? 'tab-button-active' : ''}`}
                  onClick={() => {
                    setContentMode('file')
                    setSecretMessage('')
                  }}
                >
                  File
                </button>
              </div>

              {contentMode === 'text' ? (
                <textarea
                  value={secretMessage}
                  onChange={(event) => setSecretMessage(event.target.value)}
                  placeholder="Enter hidden text, notes, code, JSON, or a secure message..."
                  className="app-textarea"
                />
              ) : (
                <UploadDropzone
                  title="Drop the file you want to hide"
                  description="PDF, ZIP, DOCX, audio, video, and any binary file are accepted."
                  file={secretFileToHide}
                  accept="*/*"
                  onFileSelect={(file) => {
                    setSecretFileToHide(file)
                    setError(null)
                  }}
                  buttonLabel="Choose secret file"
                />
              )}

              <div className="meta-row">
                <span>Payload size</span>
                <strong>{contentSizeKb.toFixed(2)} KB</strong>
              </div>
              <div className="meta-row">
                <span>Estimated cover capacity</span>
                <strong>{maxCapacity.toFixed(2)} KB</strong>
              </div>
            </div>

            <div className="subpanel space-y-5">
              <div>
                <div className="subpanel-title"><LockKeyhole className="h-4 w-4" /> Encryption</div>
                <div className="option-grid mt-3">
                  {encryptionModes.map((mode) => (
                    <button
                      type="button"
                      key={mode.id}
                      onClick={() => {
                        setEncryptionMode(mode.id)
                        if (mode.id !== 'manual') {
                          setEmbedPassword('')
                        }
                      }}
                      className={`choice-card ${encryptionMode === mode.id ? 'choice-card-active' : ''}`}
                    >
                      <span className="choice-card__title">{mode.label}</span>
                      <span className="choice-card__copy">{mode.description}</span>
                    </button>
                  ))}
                </div>
                {encryptionMode === 'manual' && (
                  <input
                    type="password"
                    value={embedPassword}
                    onChange={(event) => setEmbedPassword(event.target.value)}
                    placeholder="Enter password"
                    className="app-input mt-3"
                  />
                )}
              </div>

              <div>
                <div className="subpanel-title"><SlidersHorizontal className="h-4 w-4" /> Access Limits</div>
                <div className="space-y-4 mt-3">
                  <label className="slider-group">
                    <div className="slider-header">
                      <span>Decode limit</span>
                      <strong>{decodeLimit === 0 ? 'Unlimited' : decodeLimit}</strong>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="10"
                      value={decodeLimit}
                      onChange={(event) => setDecodeLimit(Number(event.target.value))}
                    />
                  </label>

                  <label className="slider-group">
                    <div className="slider-header">
                      <span>Time limit</span>
                      <strong>{timeLimitHours === 0 ? 'Unlimited' : `${timeLimitHours} h`}</strong>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="72"
                      step="1"
                      value={timeLimitHours}
                      onChange={(event) => setTimeLimitHours(Number(event.target.value))}
                    />
                  </label>
                </div>
              </div>

              <div>
                <div className="subpanel-title"><KeyRound className="h-4 w-4" /> Embedding Method</div>
                <select
                  value={embeddingMethod}
                  onChange={(event) => setEmbeddingMethod(event.target.value)}
                  className="app-input mt-3"
                >
                  <option value="multi_layer_lsb">Multi-Layer LSB</option>
                  <option value="lsb">Basic LSB</option>
                  <option value="spread_spectrum">Spread Spectrum</option>
                  <option value="histogram_shifting">Histogram Shifting</option>
                  <option value="dct">DCT</option>
                </select>
              </div>

              <label className="inline-flex items-center gap-3 text-sm text-[color:var(--muted)]">
                <input
                  type="checkbox"
                  checked={compressionEnabled}
                  onChange={(event) => setCompressionEnabled(event.target.checked)}
                />
                Compress payload before hiding
              </label>
            </div>
          </div>

          {error && (
            <div className="alert alert-error">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <button type="button" onClick={handleEmbed} disabled={isLoading || !embedFile} className="btn-primary w-full justify-center">
            {isLoading ? 'Embedding payload...' : 'Hide Data'}
          </button>
        </article>

        <article className="panel panel-compact space-y-4">
          <div className="section-heading">
            <h2 className="section-title">Result</h2>
            <p className="section-copy">The generated artifact stays hidden-only. Visible watermark mode has been removed.</p>
          </div>

          {embedResult ? (
            <>
              <div className="success-banner">
                <CheckCircle className="w-5 h-5" />
                Payload embedded successfully.
              </div>

              <div className="metric-stack">
                <div className="meta-row"><span>Payload bytes</span><strong>{embedResult.payload_size_bytes}</strong></div>
                <div className="meta-row"><span>Stored bytes</span><strong>{embedResult.encrypted_size_bytes}</strong></div>
                <div className="meta-row"><span>Method</span><strong>{embedResult.embedding_method}</strong></div>
                <div className="meta-row"><span>Decode limit</span><strong>{embedResult.decode_limit || 'Unlimited'}</strong></div>
                <div className="meta-row"><span>Time limit</span><strong>{embedResult.time_limit_hours ? `${embedResult.time_limit_hours} h` : 'Unlimited'}</strong></div>
                <div className="meta-row"><span>Encryption</span><strong>{embedResult.encryption_mode}</strong></div>
              </div>

              {embedResult.recovery_key && (
                <div className="key-panel">
                  <div className="key-panel__label">Recovery key</div>
                  <div className="key-panel__value">{embedResult.recovery_key}</div>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(embedResult.recovery_key)
                      toast.success('Recovery key copied')
                    }}
                    className="btn-secondary btn-compact mt-3"
                  >
                    Copy key
                  </button>
                </div>
              )}

              <button
                type="button"
                onClick={async () => {
                  try {
                    await secureStegAPI.downloadStego(embedResult.session_id, embedResult.output_filename || 'stego_output.png')
                  } catch {
                    toast.error('Download failed')
                  }
                }}
                className="btn-primary w-full justify-center"
              >
                Download Result
              </button>
            </>
          ) : (
            <div className="empty-state">
              Configure the payload, choose limits, and run embedding to generate your stego output.
            </div>
          )}
        </article>
      </section>
    </div>
  )
}
