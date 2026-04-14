const VIEWER_ID_STORAGE_KEY = 'cws_viewer_id';

export function generateViewerId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `viewer_${crypto.randomUUID().slice(0, 8)}`;
  }
  return `viewer_${Math.random().toString(36).slice(2, 10)}`;
}

export function loadOrCreateViewerId() {
  if (typeof window === 'undefined') {
    return 'viewer_local';
  }

  const existing = window.localStorage.getItem(VIEWER_ID_STORAGE_KEY)?.trim();
  if (existing) {
    return existing;
  }

  const created = generateViewerId();
  window.localStorage.setItem(VIEWER_ID_STORAGE_KEY, created);
  return created;
}

export function getViewerIdentityPayload<T extends Record<string, unknown>>(payload: T) {
  return {
    ...payload,
    viewer_id: loadOrCreateViewerId(),
  };
}
