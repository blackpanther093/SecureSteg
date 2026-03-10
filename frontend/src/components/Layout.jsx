import React from 'react'
import { Moon, Shield, SunMedium } from 'lucide-react'
import { useAppStore } from '../store'

export const Header = () => {
  const { theme, setTheme } = useAppStore()

  return (
    <header className="app-header sticky top-0 z-50">
      <div className="app-container py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="brand-mark">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">SecureSteg</h1>
              <p className="text-xs text-[color:var(--muted)]">Private steganography workflow for secure data hiding</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="btn-secondary btn-icon"
              aria-label="Toggle theme"
            >
              {theme === 'dark' ? <SunMedium className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}

export const Footer = () => {
  return (
    <footer className="mt-10 border-t border-[color:var(--border-subtle)] bg-[color:var(--panel)]/70">
      <div className="app-container py-8">
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3 mb-6">
          <div>
            <h3 className="font-semibold mb-3">Features</h3>
            <ul className="text-sm text-[color:var(--muted)] space-y-2">
              <li>AES-256-GCM Encryption</li>
              <li>Decode And Time Limits</li>
              <li>Multi-method Image Embedding</li>
              <li>Steganalysis Detection</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-3">Security</h3>
            <ul className="text-sm text-[color:var(--muted)] space-y-2">
              <li>Structured SecureSteg Payload</li>
              <li>Authenticated Encryption</li>
              <li>Optional Credential-Free Extraction</li>
              <li>Stealth-Oriented Image Processing</li>
            </ul>
          </div>

          <div>
            <h3 className="font-semibold mb-3">Tech Stack</h3>
            <ul className="text-sm text-[color:var(--muted)] space-y-2">
              <li>FastAPI Backend</li>
              <li>React Frontend</li>
              <li>Live Status Page</li>
              <li>Theme-Aware SaaS Interface</li>
            </ul>
          </div>
        </div>

        <div className="border-t border-[color:var(--border-subtle)] pt-6 text-center">
          <p className="text-sm text-[color:var(--muted)]">
            SecureSteg is built as a compact SaaS-style steganography workspace for secure operations.
          </p>
          <p className="text-xs text-[color:var(--muted-soft)] mt-2">
            Process content only in environments where hidden-data workflows are authorized.
          </p>
        </div>
      </div>
    </footer>
  )
}
