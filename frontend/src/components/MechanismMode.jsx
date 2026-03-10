import React from 'react'
import { ShieldCheck, Layers3, LockKeyhole, Radar, Database, Clock3 } from 'lucide-react'

const sections = [
  {
    icon: ShieldCheck,
    title: 'End-to-End Flow',
    points: [
      'A cover image is selected in the Hide tab and capacity is estimated before embedding starts.',
      'The secret content can be either plain text or a binary file such as PDF, ZIP, audio, video, or office documents.',
      'The payload is optionally compressed, then wrapped in a structured SecureSteg container with metadata.',
      'Metadata stores the content type, original filename, embedding method, encryption mode, decode limit, and time limit.',
      'The final payload is embedded into image channels using the selected image steganography method and then returned for download.'
    ]
  },
  {
    icon: LockKeyhole,
    title: 'Encryption Paths',
    points: [
      'No-encryption mode keeps extraction credential-free. The payload still uses the SecureSteg container for metadata and limit enforcement.',
      'Auto-key mode generates a unique 256-bit AES-GCM key for the current embed operation and returns it as a recovery key.',
      'Manual-password mode derives the encryption key from the provided password using PBKDF2 and stores a salt with the encrypted payload.',
      'AES-GCM provides confidentiality plus integrity, so tampering or a wrong password causes authentication failure during extraction.'
    ]
  },
  {
    icon: Layers3,
    title: 'Image Steganography Methods',
    points: [
      'Multi-Layer LSB uses seeded pseudo-random pixel-channel positions and hides the structured payload bitstream in least-significant bits.',
      'Basic LSB uses the same seeded position model with a simpler presentation layer.',
      'Spread Spectrum first adds low-amplitude natural noise to decorrelate channel statistics, then embeds via seeded LSB for reversible extraction.',
      'Histogram Shifting applies light contrast-limited histogram equalization before seeded LSB embedding to make statistical detection harder.',
      'DCT embeds in the frequency domain and trades simplicity for increased robustness.'
    ]
  },
  {
    icon: Clock3,
    title: 'Decode Limits And Time Limits',
    points: [
      'Decode limits are enforced server-side after successful extraction.',
      'Time limits use an absolute expiration timestamp stored in payload metadata.',
      'If both controls are zero, the message is treated as unlimited.',
      'If a decode limit is reached or a time window expires, extraction returns an expired response instead of exposing content.'
    ]
  },
  {
    icon: Radar,
    title: 'Detection Pipeline',
    points: [
      'The Detect tab evaluates LSB anomalies, entropy anomalies, and channel correlation anomalies.',
      'These signals are combined into an overall hidden-data probability score and recommendation.',
      'The result is intended to be a practical risk signal for triage, not a formal proof of hidden data.'
    ]
  },
  {
    icon: Database,
    title: 'Runtime Storage Behavior',
    points: [
      'Generated output files are intended to be served from short-lived runtime memory instead of being persisted as user files on disk.',
      'Temporary filesystem usage is only needed when a third-party handler requires a real file path for processing.',
      'Decode counters and output delivery should remain ephemeral for operational safety and privacy.'
    ]
  }
]

const featureGroups = [
  {
    title: 'Hide Tab',
    items: [
      'Cover image upload with drag-and-drop',
      'Secret text mode and binary file mode',
      'Credential-free, auto-key, or password-based embedding',
      'Decode limit and time limit sliders',
      'Capacity hints and result metadata',
      'Download trigger for the generated stego artifact'
    ]
  },
  {
    title: 'Extract Tab',
    items: [
      'Optional password and optional recovery key',
      'Credential-free extraction for non-encrypted content',
      'Binary payload download support',
      'Decode count and active limit reporting in the result panel'
    ]
  }
]

export const MechanismMode = () => {
  return (
    <div className="space-y-6">
      <section className="panel panel-hero">
        <div className="space-y-3 max-w-4xl">
          <div className="eyebrow">Mechanism Overview</div>
          <h2 className="text-3xl font-semibold tracking-tight">How SecureSteg works from input to extraction</h2>
          <p className="text-sm md:text-base text-[color:var(--muted)] leading-7">
            This tab documents the app as a complete product: what the frontend collects,
            how the backend transforms it, where cryptography is applied, how extraction is validated,
            and how detection and limits are enforced.
          </p>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {sections.map(({ icon: Icon, title, points }) => (
          <article key={title} className="panel panel-compact">
            <div className="flex items-start gap-4">
              <div className="feature-icon">
                <Icon className="h-5 w-5" />
              </div>
              <div className="space-y-3">
                <h3 className="text-lg font-semibold">{title}</h3>
                <ul className="space-y-2 text-sm text-[color:var(--muted)] leading-6">
                  {points.map((point) => (
                    <li key={point}>• {point}</li>
                  ))}
                </ul>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {featureGroups.map((group) => (
          <article key={group.title} className="panel panel-compact">
            <h3 className="text-base font-semibold mb-3">{group.title}</h3>
            <ul className="space-y-2 text-sm text-[color:var(--muted)] leading-6">
              {group.items.map((item) => (
                <li key={item}>• {item}</li>
              ))}
            </ul>
          </article>
        ))}
      </section>
    </div>
  )
}
