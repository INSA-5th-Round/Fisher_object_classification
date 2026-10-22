import type {
  Alert,
  AlertNotificationRequest,
  Camera,
  DashboardStatistics,
  Detection,
  Report,
  User,
} from "../types/dashboard";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "/api").replace(
  /\/+$/,
  "",
);

const AUTH_TOKEN_KEY = "fisher_auth_token";
const CURRENT_USER_KEY = "fisher_user";

export function getAuthToken(): string | null {
  try {
    return localStorage.getItem(AUTH_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAuthToken(token: string): void {
  try {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } catch {
    // Ignore storage errors
  }
}

export function clearAuthToken(): void {
  try {
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(CURRENT_USER_KEY);
  } catch {
    // Ignore storage errors
  }
}

export function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(CURRENT_USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user: User): void {
  try {
    localStorage.setItem(CURRENT_USER_KEY, JSON.stringify(user));
  } catch {
    // Ignore storage errors
  }
}

export function getMediaUrl(path?: string): string {
  if (!path) return "";
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  const cleanPath = path.replace(/^\/+/, "");
  return `${API_BASE_URL.replace(/\/api$/, "")}/${cleanPath}`;
}

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export async function requestApi<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...requestOptions } = options;
  const token = getAuthToken();

  const authHeaders: Record<string, string> = {};
  if (token) {
    authHeaders["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/${path.replace(/^\/+/, "")}`,
    {
      ...requestOptions,
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...authHeaders,
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    },
  );

  if (!response.ok) {
    const responseText = await response.text();
    let message = responseText || response.statusText || "API request failed.";

    if (responseText) {
      try {
        const payload: unknown = JSON.parse(responseText);
        if (
          typeof payload === "object" &&
          payload !== null &&
          "detail" in payload &&
          typeof (payload as { detail: unknown }).detail === "string"
        ) {
          message = (payload as { detail: string }).detail;
        } else if (
          typeof payload === "object" &&
          payload !== null &&
          "message" in payload &&
          typeof (payload as { message: unknown }).message === "string"
        ) {
          message = (payload as { message: string }).message;
        }
      } catch {
        // Keep the response text as the error message when the body is not JSON.
      }
    }

    throw new ApiError(message, response.status);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

// ==========================================
// AUTHENTICATION
// ==========================================

export interface LoginResponse {
  status: string;
  token: string;
  user: User;
}

export async function login(
  username: string,
  email: string,
  password: string,
): Promise<LoginResponse> {
  const response = await requestApi<LoginResponse>("/auth/login", {
    method: "POST",
    body: { username, email, password },
  });

  if (response && response.token) {
    setAuthToken(response.token);
  }
  if (response && response.user) {
    setStoredUser(response.user);
  }

  return response;
}

export async function fetchCurrentUser(): Promise<User> {
  const user = await requestApi<User>("/auth/me");
  if (user) {
    setStoredUser(user);
  }
  return user;
}

export async function updateProfile(
  nameOrPayload: string | { name: string; email: string },
  email?: string,
): Promise<{ status: string; user: User; message: string }> {
  const body =
    typeof nameOrPayload === "string"
      ? { name: nameOrPayload, email: email || "" }
      : nameOrPayload;

  const res = await requestApi<{ status: string; user: User; message: string }>(
    "/auth/profile",
    {
      method: "PUT",
      body,
    },
  );
  if (res && res.user) {
    setStoredUser(res.user);
  }
  return res;
}

export async function changePassword(
  payloadOrCurrent:
    | string
    | { currentPassword: string; newPassword: string },
  newPassword?: string,
): Promise<{ status: string; message: string }> {
  const body =
    typeof payloadOrCurrent === "string"
      ? { currentPassword: payloadOrCurrent, newPassword: newPassword || "" }
      : payloadOrCurrent;

  return requestApi<{ status: string; message: string }>(
    "/auth/change-password",
    {
      method: "POST",
      body,
    },
  );
}

export async function logout(): Promise<void> {
  try {
    await requestApi<void>("/auth/logout", { method: "POST" });
  } catch {
    // Continue cleanup even if server is unreachable
  } finally {
    clearAuthToken();
  }
}

// ==========================================
// CAMERAS & DETECTIONS
// ==========================================

export function fetchCameras(): Promise<Camera[]> {
  return requestApi<Camera[]>("/cameras");
}

export function fetchDetections(): Promise<Detection[]> {
  return requestApi<Detection[]>("/detections");
}

export function setDetectionStatus(
  detectionId: string,
  status: Detection["status"],
): Promise<Detection> {
  return requestApi<Detection>(
    `/detections/${encodeURIComponent(detectionId)}`,
    {
      method: "PATCH",
      body: { status },
    },
  );
}

export function fetchAlerts(): Promise<Alert[]> {
  return requestApi<Alert[]>("/alerts");
}

export function fetchDashboardStatistics(): Promise<DashboardStatistics> {
  return requestApi<DashboardStatistics>("/dashboard/statistics");
}

// ==========================================
// REPORTS
// ==========================================

export function fetchReports(): Promise<Report[]> {
  return requestApi<Report[]>("/reports");
}

export function generateReport(title: string = "Detection Activity Report"): Promise<Report> {
  return requestApi<Report>("/reports", {
    method: "POST",
    body: { title },
  });
}

export function fetchReportById(reportId: string): Promise<Report> {
  return requestApi<Report>(`/reports/${encodeURIComponent(reportId)}`);
}

// ==========================================
// USER MANAGEMENT
// ==========================================

export function fetchUsers(): Promise<User[]> {
  return requestApi<User[]>("/users");
}

export interface CreateUserData {
  name: string;
  email: string;
  role?: User["role"];
  username?: string;
  password?: string;
}

export function createRemoteUser(
  userOrName: CreateUserData | string,
  role?: User["role"],
): Promise<User> {
  const body =
    typeof userOrName === "string"
      ? { name: userOrName, role: role || "operator" }
      : {
          name: userOrName.name,
          email: userOrName.email,
          role: userOrName.role || "operator",
          username: userOrName.username,
          password: userOrName.password,
        };

  return requestApi<User>("/users", {
    method: "POST",
    body,
  });
}

export function updateRemoteUser(
  userId: string,
  updates: Partial<Pick<User, "name" | "role" | "status">>,
): Promise<User> {
  return requestApi<User>(`/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    body: updates,
  });
}

export function deleteRemoteUser(userId: string): Promise<{ status: string; id: string; message: string }> {
  return requestApi<{ status: string; id: string; message: string }>(
    `/users/${encodeURIComponent(userId)}`,
    {
      method: "DELETE",
    },
  );
}

// ==========================================
// ALERTS NOTIFICATIONS
// ==========================================

export function sendAlertNotification(
  request: AlertNotificationRequest,
): Promise<void> {
  return requestApi<void>(
    `/alerts/${encodeURIComponent(request.alertId)}/notify`,
    {
      method: "POST",
      body: request,
    },
  );
}
