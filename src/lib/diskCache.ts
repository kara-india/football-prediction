import fs from 'fs'
import path from 'path'

const CACHE_DIR = path.join(process.cwd(), '.cache')

function ensureDir() {
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true })
  }
}

export function getDiskCache<T>(key: string, maxAgeMs: number): T | null {
  ensureDir()
  const filePath = path.join(CACHE_DIR, `${key}.json`)
  if (!fs.existsSync(filePath)) return null

  try {
    const raw = fs.readFileSync(filePath, 'utf-8')
    const { timestamp, data } = JSON.parse(raw)
    const age = Date.now() - timestamp

    if (age < maxAgeMs) {
      return data as T
    }
    return null
  } catch {
    return null
  }
}

export function setDiskCache<T>(key: string, data: T) {
  ensureDir()
  const filePath = path.join(CACHE_DIR, `${key}.json`)
  try {
    const payload = {
      timestamp: Date.now(),
      data
    }
    fs.writeFileSync(filePath, JSON.stringify(payload, null, 2))
  } catch (err) {
    console.error(`Failed to write disk cache for ${key}:`, err)
  }
}
