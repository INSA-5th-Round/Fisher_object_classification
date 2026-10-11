import {
  cameras,
  detections,
  alerts,
  dashboardStatistics,
  reports,
  users,
} from "../data/dashboardData";
import type {
  Alert,
  AlertNotificationRequest,
  Camera,
  DashboardStatistics,
  Detection,
  Report,
  User,
} from "../types/dashboard";
import { sendAlertNotification } from "./dashboardApi";

export function getCameras(): Camera[] {
  return cameras;
}

export function getDetections(): Detection[] {
  return detections;
}

export function getAlerts(): Alert[] {
  return alerts;
}

export function getDashboardStatistics(): DashboardStatistics {
  return dashboardStatistics;
}

export function getReports(): Report[] {
  return reports;
}

export function getUsers(): User[] {
  return users;
}

export async function notifyAlert(
  request: AlertNotificationRequest,
): Promise<void> {
  await sendAlertNotification(request);
}

export function updateDetectionStatus(
  detectionId: string,
  status: "new" | "reviewed" | "dismissed",
): boolean {
  const detection = detections.find((item) => item.id === detectionId);

  if (!detection) {
    return false;
  }

  detection.status = status;

  return true;
}

export function updateUser(
  userId: string,
  role: "admin" | "operator" | "viewer",
  status: "active" | "inactive",
): boolean {
  const user = users.find((item) => item.id === userId);

  if (!user) {
    return false;
  }

  user.role = role;
  user.status = status;

  return true;
}

export function createUser(
  name: string,
  role: "admin" | "operator" | "viewer",
): User | null {
  const trimmedName = name.trim();

  if (!trimmedName) {
    return null;
  }

  const nextUserNumber = users.length + 1;

  const newUser = {
    id: `USR-${String(nextUserNumber).padStart(3, "0")}`,
    name: trimmedName,
    role,
    status: "active" as const,
  };

  users.push(newUser);

  return newUser;
}
