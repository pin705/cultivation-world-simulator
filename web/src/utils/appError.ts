export function toErrorMessage(error: unknown, fallback = 'Unknown error'): string {
  if (error instanceof Error && error.message) return error.message
  if (typeof error === 'string' && error.trim()) return error
  return fallback
}

export function logError(scope: string, error: unknown): void {
  console.error(`[${scope}]`, error)
}

export function logWarn(scope: string, error: unknown): void {
  console.warn(`[${scope}]`, error)
}

