import { getApiBaseUrl } from "./config";

export function getApiUrl(): string {
  return getApiBaseUrl();
}

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  role: "Admin" | "Vendor" | "Shopkeeper";
  is_active: boolean;
  is_verified: boolean;
  phone_number?: string;
  profile_photo?: string;
  language?: string;
  timezone?: string;
  notification_preferences?: string;
  status?: string;
  created_at: string;
  updated_at: string;
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("refresh_token");
}

export function setTokens(access: string, refresh: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user_profile");
}

export function getUserProfile(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem("user_profile");
  if (!raw) return null;
  try {
    return JSON.parse(raw) as UserProfile;
  } catch {
    return null;
  }
}

export function setUserProfile(profile: UserProfile): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("user_profile", JSON.stringify(profile));
}

/**
 * Perform token refresh request and save result.
 */
export async function refreshTokens(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  try {
    const apiBase = getApiBaseUrl();
    const res = await fetch(`${apiBase}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });

    if (!res.ok) {
      clearTokens();
      return null;
    }

    const data = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch (err) {
    loggerError("Refresh failed:", err);
    clearTokens();
    return null;
  }
}

/**
 * Fetch wrapper that automatically injects JWT access token
 * and handles token refresh if 401 Unauthorized occurs.
 */
export async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  let token = getAccessToken();
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  options.headers = headers;
  const apiBase = getApiBaseUrl();
  let response = await fetch(`${apiBase}${url}`, options);

  // If unauthorized, token might have expired. Try to refresh.
  if (response.status === 401) {
    const newToken = await refreshTokens();
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      options.headers = headers;
      response = await fetch(`${apiBase}${url}`, options);
    } else {
      // Refresh failed, redirect to login
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
  }

  return response;
}

function loggerError(msg: string, err: any) {
  console.error(msg, err);
}
