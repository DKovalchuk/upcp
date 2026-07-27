export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  is_active: boolean;
  is_superuser: boolean;
  organizations: { id: string; name: string; role: string }[];
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

const AUTH_BASE = '/auth';

async function authRequest<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: response.statusText,
    }));
    throw new Error(error.detail || response.statusText);
  }

  return response.json();
}

export async function authSetup(
  email: string,
  password: string,
  display_name: string
): Promise<AuthTokens & { user: AuthUser }> {
  return authRequest(`${AUTH_BASE}/setup`, {
    method: 'POST',
    body: JSON.stringify({ email, password, display_name }),
  });
}

export async function authLogin(
  email: string,
  password: string
): Promise<AuthTokens> {
  return authRequest(`${AUTH_BASE}/login`, {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
}

export async function authMe(token: string): Promise<AuthUser> {
  return authRequest(`${AUTH_BASE}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function authRefresh(
  refresh_token: string
): Promise<AuthTokens> {
  return authRequest(`${AUTH_BASE}/refresh`, {
    method: 'POST',
    body: JSON.stringify({ refresh_token }),
  });
}
