/**
 * Safe localStorage wrapper — gracefully degrades when storage is unavailable.
 *
 * Handles: private browsing, disabled storage, quota exceeded, iframe contexts.
 * Falls back to in-memory storage when localStorage is not accessible.
 */

let memoryStorage: Record<string, string> = {};

function isLocalStorageAvailable(): boolean {
  try {
    const test = '__storage_test__';
    localStorage.setItem(test, test);
    localStorage.removeItem(test);
    return true;
  } catch {
    return false;
  }
}

const available = isLocalStorageAvailable();

export const safeStorage = {
  getItem(key: string): string | null {
    if (available) {
      try {
        return localStorage.getItem(key);
      } catch {
        return memoryStorage[key] ?? null;
      }
    }
    return memoryStorage[key] ?? null;
  },

  setItem(key: string, value: string): void {
    if (available) {
      try {
        localStorage.setItem(key, value);
        return;
      } catch {
        // Quota exceeded or other error — fall through to memory
      }
    }
    memoryStorage[key] = value;
  },

  removeItem(key: string): void {
    if (available) {
      try {
        localStorage.removeItem(key);
      } catch {
        // Ignore
      }
    }
    delete memoryStorage[key];
  },
};
