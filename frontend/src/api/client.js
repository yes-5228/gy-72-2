const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'

function extractErrorMessage(body, status) {
  if (body.detail) {
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => {
        if (typeof item === 'object' && item !== null) {
          return Object.values(item).join('；')
        }
        return String(item)
      }).join('；')
    }
    if (typeof body.detail === 'object' && body.detail !== null) {
      return Object.values(body.detail).join('；')
    }
    return String(body.detail)
  }
  for (const key of Object.keys(body)) {
    const val = body[key]
    if (Array.isArray(val) && val.length > 0) {
      return val.map((v) => String(v)).join('；')
    }
    if (typeof val === 'string' && val) {
      return val
    }
  }
  return `请求失败：${status}`
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const message = extractErrorMessage(body, response.status)
    throw new Error(message)
  }

  if (response.status === 204) {
    return null
  }
  return response.json()
}

export const api = {
  get: (path) => request(path),
  post: (path, data) => request(path, { method: 'POST', body: JSON.stringify(data) }),
  patch: (path, data) => request(path, { method: 'PATCH', body: JSON.stringify(data) }),
}
