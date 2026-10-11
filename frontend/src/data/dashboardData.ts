import type {
  Alert,
  Camera,
  DashboardStatistics,
  Detection,
  Report,
  User,
} from "../types/dashboard";

export const cameras: Camera[] = [
  {
    id: "CAM-001",
    name: "Main Entrance",
    location: "North Gate",
    status: "online",
  },
  {
    id: "CAM-002",
    name: "Parking Area",
    location: "East Parking",
    status: "online",
  },
  {
    id: "CAM-003",
    name: "Building A",
    location: "Ground Floor",
    status: "online",
  },
  {
    id: "CAM-004",
    name: "Service Road",
    location: "South Gate",
    status: "offline",
  },
];

export const detections: Detection[] = [
  {
    id: "DET-001",
    cameraId: "CAM-001",
    type: "Person detected",
    confidence: 96,
    severity: "low",
    timestamp: "2026-09-05 10:42",
    status: "reviewed",
  },
  {
    id: "DET-002",
    cameraId: "CAM-002",
    type: "Vehicle detected",
    confidence: 91,
    severity: "medium",
    timestamp: "2026-09-05 10:37",
    status: "new",
  },
  {
    id: "DET-003",
    cameraId: "CAM-003",
    type: "Unusual activity",
    confidence: 87,
    severity: "high",
    timestamp: "2026-09-05 10:31",
    status: "new",
  },
];

export const alerts: Alert[] = [
  {
    id: "ALT-001",
    title: "Unusual activity detected",
    description: "Unusual activity detected near Building A ground floor.",
    confidence: 87,
    severity: "high",
    status: "open",
    timestamp: "2026-09-05 10:31",
    cameraId: "CAM-003",
  },
  {
    id: "ALT-002",
    title: "Vehicle activity requires review",
    description: "Vehicle activity requires review in the east parking area.",
    confidence: 91,
    severity: "medium",
    status: "open",
    timestamp: "2026-09-05 10:37",
    cameraId: "CAM-002",
  },
];

export const dashboardStatistics: DashboardStatistics = {
  totalCameras: cameras.length,
  onlineCameras: cameras.filter((camera) => camera.status === "online").length,
  totalDetections: detections.length,
  activeAlerts: alerts.filter((alert) => alert.status === "open").length,
};

export const reports: Report[] = [
  {
    id: "REP-001",
    title: "Daily Detection Summary",
    createdAt: "2026-09-05",
    status: "ready",
  },
];

export const users: User[] = [
  {
    id: "USR-001",
    name: "Administrator",
    role: "admin",
    status: "active",
  },
];
