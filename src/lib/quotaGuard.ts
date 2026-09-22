import fs from 'fs'
import path from 'path'

const CACHE_DIR = path.join(process.cwd(), '.cache')
const QUOTA_FILE = path.join(CACHE_DIR, 'api_quota.json')

export interface QuotaState {
  date: string
  currentUsed: number
  dailyLimit: number
  maxAutoUsage: number       // Max 50 requests for automated / list ingestion
  userReservedCount: number  // 50 requests strictly reserved for user on-demand analysis
  hardStopLimit: number      // Hard stop at 95 to prevent any chance of overage
  lastSyncedAt: string
}

function getTodayString(): string {
  // Use UTC date as API-Football resets at 00:00 UTC
  return new Date().toISOString().split('T')[0]
}

function ensureDir() {
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true })
  }
}

export function getQuotaState(): QuotaState {
  ensureDir()
  const today = getTodayString()

  const defaultState: QuotaState = {
    date: today,
    currentUsed: 26, // Seeded with today's verified actual usage
    dailyLimit: 100,
    maxAutoUsage: 50,
    userReservedCount: 50,
    hardStopLimit: 95,
    lastSyncedAt: new Date().toISOString()
  }

  if (!fs.existsSync(QUOTA_FILE)) {
    fs.writeFileSync(QUOTA_FILE, JSON.stringify(defaultState, null, 2))
    return defaultState
  }

  try {
    const raw = fs.readFileSync(QUOTA_FILE, 'utf-8')
    const state: QuotaState = JSON.parse(raw)

    // Reset daily if date has rolled over
    if (state.date !== today) {
      state.date = today
      state.currentUsed = 0
      state.lastSyncedAt = new Date().toISOString()
      fs.writeFileSync(QUOTA_FILE, JSON.stringify(state, null, 2))
    }

    return state
  } catch {
    return defaultState
  }
}

export function saveQuotaState(state: QuotaState) {
  ensureDir()
  fs.writeFileSync(QUOTA_FILE, JSON.stringify(state, null, 2))
}

/**
 * Checks whether an API request is permitted.
 * @param isUserDemand true if user explicitly clicked "Analyze Match" or refreshed a specific match.
 *                     false for automated background listing or scheduled polling.
 */
export function canMakeAPIRequest(isUserDemand: boolean = false): { allowed: boolean; reason?: string } {
  const quota = getQuotaState()

  // 1. Hard stop safeguard (at 95 requests)
  if (quota.currentUsed >= quota.hardStopLimit) {
    return {
      allowed: false,
      reason: `Hard safety limit reached (${quota.currentUsed}/${quota.dailyLimit}). Stopped to prevent charges.`
    }
  }

  // 2. Automated / Background listing limit (Max 50 requests)
  if (!isUserDemand && quota.currentUsed >= quota.maxAutoUsage) {
    return {
      allowed: false,
      reason: `Automated quota reached (${quota.currentUsed}/${quota.maxAutoUsage}). Remaining ${quota.dailyLimit - quota.currentUsed} requests are reserved for user match analysis.`
    }
  }

  return { allowed: true }
}

/**
 * Records that an API request was successfully made.
 */
export function recordAPIRequest(endpoint: string, actualRemoteUsed?: number) {
  const quota = getQuotaState()
  if (actualRemoteUsed !== undefined && actualRemoteUsed > quota.currentUsed) {
    quota.currentUsed = actualRemoteUsed
  } else {
    quota.currentUsed += 1
  }
  quota.lastSyncedAt = new Date().toISOString()
  saveQuotaState(quota)
  console.log(`[QUOTA GUARD] Request logged for ${endpoint}. Used today: ${quota.currentUsed}/${quota.dailyLimit}`)
}
