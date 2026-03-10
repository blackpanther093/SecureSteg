import React from 'react'
import { AlertCircle, CheckCircle, KeyRound, Unlock } from 'lucide-react'
import toast from 'react-hot-toast'
import { secureStegAPI } from '../api/client'
import { useAppStore } from '../store'
import { UploadDropzone } from './UploadDropzone'

export const ExtractMode = () => {
  const {
    extractFile,
    setExtractFile,
    extractPassword,
    setExtractPassword,
    extractRecoveryKey,
    setExtractRecoveryKey,
    extractedData,
    setExtractedData,
    isLoading,
    setIsLoading,
    error,
    setError,
  } = useAppStore()

  const handleExtract = async () => {
    if (!extractFile) {
      setError('Select a stego file to extract from')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const response = await secureStegAPI.extract(extractFile, extractPassword, extractRecoveryKey)
      setExtractedData(response.data)
      toast.success('Extraction completed')
    } catch (err) {
      const message = err.response?.data?.detail || 'Extraction failed'
      setError(message)
      toast.error(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownload = () => {
    if (!extractedData) {
      return
    }

    if (extractedData.content_type && !extractedData.content_type.startsWith('text/')) {
      const raw = atob(extractedData.extracted_data)
      const bytes = new Uint8Array(raw.length)
      for (let index = 0; index < raw.length; index += 1) {
        bytes[index] = raw.charCodeAt(index)
      }

      const blob = new Blob([bytes], { type: extractedData.content_type || 'application/octet-stream' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = extractedData.filename || 'extracted.bin'
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      URL.revokeObjectURL(url)
      return
    }

    const anchor = document.createElement('a')
    anchor.href = `data:text/plain;charset=utf-8,${encodeURIComponent(extractedData.extracted_data)}`
    anchor.download = extractedData.filename || 'extracted_data.txt'
    document.body.appendChild(anchor)
    anchor.click()
    document.body.removeChild(anchor)
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-6 xl:grid-cols-[1fr_0.9fr]">
        <article className="panel space-y-5">
          <div className="section-heading">
            <h2 className="section-title">Extract Payload</h2>
            <p className="section-copy">Upload the stego artifact. Password and recovery key are optional and only required when the payload was encrypted.</p>
          </div>

          <UploadDropzone
            title="Drop stego file or click to browse"
            description="Use the file returned by the Hide flow. Images and other generated outputs are accepted."
            file={extractFile}
            accept="*/*"
            onFileSelect={(file) => {
              setExtractFile(file)
              setExtractedData(null)
              setError(null)
            }}
            buttonLabel="Choose file"
          />

          <div className="grid gap-4 md:grid-cols-2">
            <div className="subpanel">
              <div className="subpanel-title"><Unlock className="h-4 w-4" /> Password</div>
              <input
                type="password"
                value={extractPassword}
                onChange={(event) => setExtractPassword(event.target.value)}
                placeholder="Leave empty for non-encrypted payloads"
                className="app-input mt-3"
              />
            </div>

            <div className="subpanel">
              <div className="subpanel-title"><KeyRound className="h-4 w-4" /> Recovery Key</div>
              <input
                type="text"
                value={extractRecoveryKey}
                onChange={(event) => setExtractRecoveryKey(event.target.value)}
                placeholder="Optional auto-generated key"
                className="app-input mt-3"
              />
            </div>
          </div>

          {error && (
            <div className="alert alert-error">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <button type="button" onClick={handleExtract} disabled={isLoading || !extractFile} className="btn-primary w-full justify-center">
            {isLoading ? 'Extracting payload...' : 'Extract Hidden Data'}
          </button>
        </article>

        <article className="panel panel-compact space-y-4">
          <div className="section-heading">
            <h2 className="section-title">Extracted Result</h2>
            <p className="section-copy">Decoded content, access counters, and download actions appear here after successful extraction.</p>
          </div>

          {extractedData ? (
            <>
              <div className="success-banner">
                <CheckCircle className="w-5 h-5" />
                Extraction completed successfully.
              </div>

              <div className="metric-stack">
                <div className="meta-row"><span>Data size</span><strong>{extractedData.data_size_bytes} bytes</strong></div>
                <div className="meta-row"><span>Content type</span><strong>{extractedData.content_type || 'text/plain'}</strong></div>
                <div className="meta-row"><span>Filename</span><strong>{extractedData.filename || 'Inline text'}</strong></div>
                <div className="meta-row"><span>Decode count</span><strong>{typeof extractedData.decode_count === 'number' ? extractedData.decode_count : 'n/a'}</strong></div>
                <div className="meta-row"><span>Decode limit</span><strong>{extractedData.decode_limit || 'Unlimited'}</strong></div>
              </div>

              <div className="result-surface">
                {extractedData.content_type?.startsWith('text/') || !extractedData.content_type
                  ? extractedData.extracted_data
                  : 'Binary payload extracted successfully. Use Download to save the restored file.'}
              </div>

              <div className="grid gap-3 md:grid-cols-2">
                <button
                  type="button"
                  onClick={() => {
                    navigator.clipboard.writeText(extractedData.extracted_data)
                    toast.success('Extracted content copied')
                  }}
                  className="btn-secondary w-full justify-center"
                >
                  Copy
                </button>
                <button type="button" onClick={handleDownload} className="btn-primary w-full justify-center">
                  Download
                </button>
              </div>
            </>
          ) : (
            <div className="empty-state">
              Upload a stego artifact and run extraction to inspect the recovered content.
            </div>
          )}
        </article>
      </section>
    </div>
  )
}
