/**
 * Utility functions for server connectivity
 */

const PORTS = [5002, 5004]
const PING_TIMEOUT = 2000 // 2 seconds

/**
 * Ping a server with timeout
 * @param {string} url - The URL to ping
 * @param {number} timeout - Timeout in milliseconds
 * @returns {Promise<boolean>} - True if server responds, false otherwise
 */
const pingServer = async (url, timeout = PING_TIMEOUT) => {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeout)
    
    const response = await fetch(`${url}/ping`, {
      method: 'GET',
      signal: controller.signal
    })
    
    clearTimeout(timeoutId)
    return response.ok
  } catch (error) {
    return false
  }
}

/**
 * Find the first available server from the list of ports
 * @returns {Promise<string|null>} - Returns the base URL of available server or null
 */
export const findAvailableServer = async () => {
  for (const port of PORTS) {
    const baseUrl = `http://127.0.0.1:${port}`
    const isAvailable = await pingServer(baseUrl)
    if (isAvailable) {
      return baseUrl
    }
  }
  return null
}

/**
 * Make a request to the server with automatic server discovery
 * @param {string} endpoint - The endpoint to call (e.g., '/commands', '/commandName')
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<Object>} - The response object with data and server info
 */
export const makeServerRequest = async (endpoint, options = {}) => {
  const serverUrl = await findAvailableServer()
  
  if (!serverUrl) {
    throw new Error('No server is available. Please make sure the server is running.')
  }
  
  const url = `${serverUrl}${endpoint}`
  const response = await fetch(url, {
    timeout: 10000, // 10 seconds for actual requests
    ...options
  })
  
  if (!response.ok) {
    throw new Error(`Server error: ${response.status} ${response.statusText}`)
  }
  
  const data = await response.json()
  return {
    data,
    serverUrl,
    status: response.status
  }
}

/**
 * Check if any server is currently available
 * @returns {Promise<boolean>} - True if any server is available
 */
export const isServerAvailable = async () => {
  const serverUrl = await findAvailableServer()
  return serverUrl !== null
}