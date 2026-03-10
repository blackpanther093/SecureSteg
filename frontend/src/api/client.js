import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

export const secureStegAPI = {
  // Embed data into media — returns JSON metadata; use downloadStego() for the file
  embed: async (file, secretMessage, password = '', method = 'multi_layer_lsb', compression = true, options = {}) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('secret_message', typeof secretMessage === 'string' ? secretMessage : '')
    if (options.secretFile) {
      formData.append('secret_file', options.secretFile)
    }
    formData.append('password', password)
    formData.append('method', method)
    formData.append('compression', compression)
    formData.append('encryption_mode', options.encryptionMode || 'auto')
    formData.append('self_destruct_mode', options.selfDestructMode || 'unlimited')
    formData.append('decode_limit', String(options.decodeLimit || 0))
    formData.append('time_limit_hours', String(options.timeLimitHours || 0))
    formData.append('watermark_mode', options.watermarkMode || 'hidden')
    formData.append('is_file', options.isFile || false)
    if (options.filename) formData.append('filename', options.filename)

    return api.post('/embed', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  // Extract hidden data
  extract: async (file, password = '', recoveryKey = '', method = 'auto') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('password', password)
    formData.append('recovery_key', recoveryKey)
    formData.append('method', method)
    
    return api.post('/extract', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Detect hidden data
  detect: async (file, sensitivity = 'medium') => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('sensitivity', sensitivity)
    
    return api.post('/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Calculate capacity
  capacity: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    
    return api.post('/capacity', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // Generate recovery key
  generateKey: async (format = 'hex') => {
    return api.post('/generate-key', { format_style: format })
  },

  // Download stego file — triggers a browser download
  downloadStego: async (sessionId, filename = 'stego_output.png') => {
    const response = await api.get('/download-stego', {
      params: { session_id: sessionId, filename },
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  },

  // Health check
  health: async () => {
    try {
      return await api.get('/health')
    } catch (error) {
      return null
    }
  }
}

export default api
