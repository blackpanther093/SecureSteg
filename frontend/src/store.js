import { create } from 'zustand'

const getInitialTheme = () => {
  if (typeof window === 'undefined') {
    return 'dark'
  }

  const savedTheme = window.localStorage.getItem('securesteg-theme')
  if (savedTheme === 'light' || savedTheme === 'dark') {
    return savedTheme
  }

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export const useAppStore = create((set) => ({
  // UI state
  currentMode: 'embed', // 'embed', 'extract', 'detect', 'mechanism'
  setCurrentMode: (mode) => set({ currentMode: mode }),
  theme: getInitialTheme(),
  setTheme: (theme) => set({ theme }),

  // Embed mode state
  embedFile: null,
  setEmbedFile: (file) => set({ embedFile: file }),
  
  secretMessage: '',
  setSecretMessage: (msg) => set({ secretMessage: msg }),
  
  embedPassword: '',
  setEmbedPassword: (pwd) => set({ embedPassword: pwd }),
  
  useKeylessMode: false,
  setUseKeylessMode: (val) => set({ useKeylessMode: val }),
  
  recoveryKey: '',
  setRecoveryKey: (key) => set({ recoveryKey: key }),
  
  embeddingMethod: 'multi_layer_lsb',
  setEmbeddingMethod: (method) => set({ embeddingMethod: method }),
  
  compressionEnabled: true,
  setCompressionEnabled: (val) => set({ compressionEnabled: val }),

  // Capacity info
  capacityInfo: null,
  setCapacityInfo: (info) => set({ capacityInfo: info }),

  // Extract mode state
  extractFile: null,
  setExtractFile: (file) => set({ extractFile: file }),
  
  extractPassword: '',
  setExtractPassword: (pwd) => set({ extractPassword: pwd }),
  
  extractRecoveryKey: '',
  setExtractRecoveryKey: (key) => set({ extractRecoveryKey: key }),

  // Detect mode state
  detectFile: null,
  setDetectFile: (file) => set({ detectFile: file }),
  
  detectSensitivity: 'medium',
  setDetectSensitivity: (sens) => set({ detectSensitivity: sens }),

  // Results
  embedResult: null,
  setEmbedResult: (result) => set({ embedResult: result }),
  
  extractedData: null,
  setExtractedData: (data) => set({ extractedData: data }),
  
  detectionResult: null,
  setDetectionResult: (result) => set({ detectionResult: result }),

  // Loading states
  isLoading: false,
  setIsLoading: (val) => set({ isLoading: val }),
  
  error: null,
  setError: (err) => set({ error: err }),

  // Reset store
  resetEmbedMode: () => set({
    embedFile: null,
    secretMessage: '',
    embedPassword: '',
    useKeylessMode: false,
    recoveryKey: '',
    capacityInfo: null,
    embedResult: null,
    error: null
  }),

  resetExtractMode: () => set({
    extractFile: null,
    extractPassword: '',
    extractRecoveryKey: '',
    extractedData: null,
    error: null
  }),

  resetDetectMode: () => set({
    detectFile: null,
    detectSensitivity: 'medium',
    detectionResult: null,
    error: null
  })
}))
