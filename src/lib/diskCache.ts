import fs from 'fs'
import path from 'path'

/**
 * Vercel Functions have a read-only deployment filesystem with writable
 * /tmp scratch space. Use /tmp in Vercel and the project-local .cache
 * directory elsewhere (local development / GitHub Actions).
 *
 * This cache is opportunistic runtime cache only; it is not durable storage.
 */
const CACHE_DIR = process.env.VERCEL
  ? path.join('/tmp', 'football-prediction-cache')
  : path.join(process.cwd(), '.cache')

function ensureDir(): boolean {
  try {
    if (!fs.existsSync(CACHE_DIR)) {
      fs.mkdirSync(CACHE_DIR, { recursive: true })
    }
    return true
  } catch (err) {
    console.error('Failed to initialize runtime cache directory:', err)
    return false
  }
}

export function getDiskCache<T>(key: string, maxAgeMs: number): T | null {
  if (!ensureDir()) return null

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
  if (!ensureDir()) return

  const filePath = path.join(CACHE_DIR, `${key}.json`)
  try {
    const payload = {
      timestamp: Date.now(),
      data
    }
    fs.writeFileSync(filePath, JSON.stringify(payload, null, 2))
  } catch (err) {
    console.error(`Failed to write runtime cache for ${key}:`, err)
  }
}
