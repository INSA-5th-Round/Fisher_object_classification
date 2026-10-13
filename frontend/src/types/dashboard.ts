export interface Camera {
  id: string;
  name: string;
  location: string;
  status: "online" | "offline";
}

export interface Detection {
  id: string;
  cameraId: string;
  type: string;
  confidence: number;
  severity: "low" | "medium" | "high" | "critical";
  timestamp: string;
  status: "new" | "reviewed" | "dismissed";
}

export interface Alert {
  id: string;
  title: string;
  description: string;
  confidence: number;
  severity: "low" | "medium" | "high" | "critical";
  status: "open" | "reviewed" | "resolved";
  timestamp: string;
  cameraId?: string;
}

export interface AlertNotificationRequest {
  channels: ("sms" | "telegram")[];
  alertId: string;
  title: string;
  severity: Alert["severity"];
  cameraId?: string;
  confidence: number;
  imageUrl?: string;
  incidentUrl: string;
}

export interface DashboardStatistics {
  totalCameras: number;
  onlineCameras: number;
  totalDetections: number;
  activeAlerts: number;
}

export interface Report {
  id: string;
  title: string;
  createdAt: string;
  status: "ready" | "processing";
}

export interface User {
  id: string;
  name: string;
  role: "admin" | "operator" | "viewer";
  status: "active" | "inactive";
}
