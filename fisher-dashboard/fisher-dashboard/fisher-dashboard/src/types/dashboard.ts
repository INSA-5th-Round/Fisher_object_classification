export interface Camera {
  id: string;
  name: string;
  location: string;
  status: "online" | "offline";
  streamUrl?: string;
}

export interface Detection {
  id: string;
  cameraId: string;
  type: string;
  confidence: number;
  severity: "low" | "medium" | "high" | "critical";
  timestamp: string;
  status: "new" | "reviewed" | "dismissed";
  image?: string;
  imageUrl?: string;
  video?: string;
  videoUrl?: string;
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

export interface ReportDetection {
  id: string;
  cameraId?: string;
  cameraName?: string;
  type: string;
  confidence: number;
  severity: "low" | "medium" | "high" | "critical";
  timestamp: string;
  status?: string;
  image?: string;
  imageUrl?: string;
  video?: string;
  videoUrl?: string;
  description?: string;
}

export interface Report {
  id: string;
  title: string;
  createdAt: string;
  status: "ready" | "processing";
  totalDetections?: number;
  highSeverityCount?: number;
  summary?: string;
  detections?: ReportDetection[];
}

export interface User {
  id: string;
  name: string;
  email?: string;
  username?: string;
  role: "admin" | "operator" | "viewer";
  status: "active" | "inactive";
  lastLogin?: string;
}
