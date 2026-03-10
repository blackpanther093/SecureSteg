/**
 * Main App Component
 * SecureSteg Platform Entry Point
 */

import React, { useEffect } from 'react'
import { Toaster } from 'react-hot-toast'
import { useAppStore } from './store'
import { Header, Footer } from './components/Layout'
import { ModeSelector } from './components/ModeSelector'
import { EmbedMode } from './components/EmbedMode'
import { ExtractMode } from './components/ExtractMode'
import { DetectMode } from './components/DetectMode'
import { MechanismMode } from './components/MechanismMode'
import { secureStegAPI } from './api/client'
import './index.css'

function App() {
  const { currentMode, setError, theme } = useAppStore()

  useEffect(() => {
    // Health check on mount
    secureStegAPI.health()
      .then(response => {
        if (!response) {
          setError('Backend server is not responding. Please ensure FastAPI server is running on http://localhost:8000')
        }
      })
      .catch(() => {
        setError('Cannot connect to backend. Ensure FastAPI is running.')
      })
  }, [setError])

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    window.localStorage.setItem('securesteg-theme', theme)
  }, [theme])

  return (
    <div className="app-shell min-h-screen flex flex-col">
      <Header />

      <main className="flex-1">
        <div className="app-container py-8 sm:py-10">
          <section className="panel panel-hero mb-6 overflow-hidden">
            <div className="hero-grid">
              <div className="space-y-4">
                <div className="eyebrow">Professional Steganography Workspace</div>
                <h1 className="hero-title">Hide sensitive payloads inside media with a product-grade workflow.</h1>
                <p className="hero-copy">
                  SecureSteg combines structured payload wrapping, optional AES-GCM encryption,
                  decode and time-based controls, and steganalysis inspection in one compact interface.
                </p>
              </div>

              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-label">Credentials</div>
                  <div className="stat-value">None / Auto / Password</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Core Methods</div>
                  <div className="stat-value">LSB, Spread, DCT</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Limits</div>
                  <div className="stat-value">Decode + Time</div>
                </div>
                <div className="stat-card">
                  <div className="stat-label">Health</div>
                  <div className="stat-value">Live Backend Status</div>
                </div>
              </div>
            </div>
          </section>

          <div className="mb-6">
            <ModeSelector />
          </div>

          <div className="mb-12">
            {currentMode === 'embed' && <EmbedMode />}
            {currentMode === 'extract' && <ExtractMode />}
            {currentMode === 'detect' && <DetectMode />}
            {currentMode === 'mechanism' && <MechanismMode />}
          </div>
        </div>
      </main>

      <Footer />

      {/* Toast Notifications */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: 'var(--panel-elevated)',
            color: 'var(--foreground)',
            border: '1px solid var(--border-subtle)',
            backdropFilter: 'blur(10px)'
          }
        }}
      />
    </div>
  )
}

export default App
