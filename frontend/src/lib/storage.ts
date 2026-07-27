/**
 * Safe storage wrapper — localStorage → cookie → memory fallback chain.
 *
 * Priority:
 * 1. localStorage (fastest, most capacity)
 * 2. cookie (persists across reloads, works in most environments)
 * 3. memory (last resort, lost on reload)
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

function setCookie(key: string, value: string, days: number = 7): void {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${key}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

function getCookie(key: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^| )${key}=([^;]*)`));
  return match ? decodeURIComponent(match[1]) : null;
}

function deleteCookie(key: string): void {
  document.cookie = `${key}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
}

const localStorageAvailable = isLocalStorageAvailable();

export const safeStorage = {
  getItem(key: string): string | null {
    // 1. Try localStorage
    if (localStorageAvailable) {
      try {
        const value = localStorage.getItem(key);
        if (value !== null) return value;
      } catch {
        // Fall through
      }
    }

    // 2. Try cookie
    try {
      const value = getCookie(key);
      if (value !== null) return value;
    } catch {
      // Fall through
    }

    // 3. Memory fallback
    return memoryStorage[key] ?? null;
  },

  setItem(key: string, value: string): void {
    // 1. Try localStorage
    if (localStorageAvailable) {
      try {
        localStorage.setItem(key, value);
        return;
      } catch {
        // Fall through
      }
    }

    // 2. Try cookie
    try {
      setCookie(key, value);
      return;
    } catch {
      // Fall through
    }

    // 3. Memory fallback
    memoryStorage[key] = value;
  },

  removeItem(key: string): void {
    if (localStorageAvailable) {
      try {
        localStorage.removeItem(key);
      } catch {
        // Ignore
      }
    }
    try {
      deleteCookie(key);
    } catch {
      // Ignore
    }
    delete memoryStorage[key];
  },
};
