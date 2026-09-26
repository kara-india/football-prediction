/**
 * Ephemeral per-runtime cache.
 *
 * This intentionally uses memory rather than the Vercel filesystem. It is
 * never authoritative state and may disappear whenever a serverless instance
 * is recycled. Durable match/odds state belongs in Supabase.
 */

type CacheEntry = {
  timestamp: number
  data: unknown
}

const cache = new Map<string, CacheEntry>()

export function getDiskCache<T>(key: string, maxAgeMs: number): T | null {
  const entry = cache.get(key)
  if (!entry) return null

  const age = Date.now() - entry.timestamp
  if (age < maxAgeMs) {
    return entry.data as T
  }

  cache.delete(key)
  return null
}

export function setDiskCache<T>(key: string, data: T): void {
  cache.set(key, {
    timestamp: Date.now(),
    data,
  })
}
