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

async function requestApi<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, headers, ...requestOptions } = options;
  const response = await fetch(
    `${API_BASE_URL}/${path.replace(/^\/+/, "")}`,
    {
      ...requestOptions,
      headers: {
        Accept: "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
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
          "message" in payload &&
          typeof payload.message === "string"
        ) {
          message = payload.message;
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

export function fetchReports(): Promise<Report[]> {
  return requestApi<Report[]>("/reports");
}

export function generateReport(): Promise<Report> {
  return requestApi<Report>("/reports", { method: "POST" });
}

export function fetchUsers(): Promise<User[]> {
  return requestApi<User[]>("/users");
}

export function createRemoteUser(
  name: string,
  role: User["role"],
): Promise<User> {
  return requestApi<User>("/users", {
    method: "POST",
    body: { name, role },
  });
}

export function updateRemoteUser(
  userId: string,
  updates: Pick<User, "role" | "status">,
): Promise<User> {
  return requestApi<User>(`/users/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    body: updates,
  });
}

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
