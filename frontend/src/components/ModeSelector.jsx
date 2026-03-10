import React from 'react'
import { Lock, Unlock, Search, LibraryBig } from 'lucide-react'
import { useAppStore } from '../store'

export const ModeSelector = () => {
  const { currentMode, setCurrentMode } = useAppStore()

  const modes = [
    {
      id: 'embed',
      label: 'Hide',
      icon: Lock,
      description: 'Hide encrypted data inside media'
    },
    {
      id: 'extract',
      label: 'Extract',
      icon: Unlock,
      description: 'Extract hidden data from media'
    },
    {
      id: 'detect',
      label: 'Detect',
      icon: Search,
      description: 'Analyze file for hidden data'
    },
    {
      id: 'mechanism',
      label: 'Mechanism',
      icon: LibraryBig,
      description: 'Detailed system overview'
    }
  ]

  return (
    <div className="mode-selector-grid">
      {modes.map(({ id, label, icon: Icon, description }) => (
        <button
          key={id}
          onClick={() => setCurrentMode(id)}
          className={`mode-card ${
            currentMode === id
              ? 'mode-card-active'
              : 'mode-card-idle'
          }`}
        >
          <div className="mode-card__icon">
            <Icon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-base mb-1">{label}</h3>
            <p className="text-sm text-[color:var(--muted)]">{description}</p>
          </div>
        </button>
      ))}
    </div>
  )
}
