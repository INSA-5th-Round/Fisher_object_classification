import { useState } from "react";
import {
  getCameras,
  getDashboardStatistics,
  getDetections,
} from "../services/dashboardService";
import type { Detection } from "../types/dashboard";
import CCTVFeed from "../components/cctv/CCTVFeed";
import DetectionResults from "../components/detections/DetectionResults";
import Statistics from "../components/statistics/Statistics";
import Reports from "../components/reports/Reports";
import UserManagement from "../components/users/UserManagement";
import AlertCenter from "../components/alerts/AlertCenter";

function Dashboard() {
  const cameras = getCameras();
  const dashboardStatistics = getDashboardStatistics();

  const [detections, setDetections] = useState<Detection[]>(getDetections());

  const offlineCameras =
    dashboardStatistics.totalCameras - dashboardStatistics.onlineCameras;

  const handleDetectionStatusChange = (
    detectionId: string,
    status: "new" | "reviewed" | "dismissed",
  ) => {
    setDetections((currentDetections) =>
      currentDetections.map((detection) =>
        detection.id === detectionId ? { ...detection, status } : detection,
      ),
    );
  };

  return (
    <section className="dashboard-page" id="dashboard">
      <div className="dashboard-intro">
        <div>
          <span className="eyebrow">INTELLIGENCE OPERATIONS CENTER</span>

          <h2>
            FISHER <span className="dashboard-word">Dashboard</span>
          </h2>

          <p>
            Monitor camera activity, review AI detections, and investigate
            security events from one centralized workspace.
          </p>
        </div>

        <div className="live-monitoring-group">
          <div className="ethiopian-strip" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </div>

          <div className="live-indicator">
            <span className="status-dot"></span>
            Live Monitoring
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        <div className="dashboard-card">
          <span>CAMERAS</span>
          <strong>{dashboardStatistics.totalCameras}</strong>
          <small>Registered CCTV sources</small>
        </div>

        <div className="dashboard-card">
          <span>ONLINE</span>
          <strong>{dashboardStatistics.onlineCameras}</strong>
          <small>Currently available</small>
        </div>

        <div className="dashboard-card">
          <span>OFFLINE</span>
          <strong>{offlineCameras}</strong>
          <small>Currently unavailable</small>
        </div>

        <div className="dashboard-card">
          <span>ALERTS</span>
          <strong>{dashboardStatistics.activeAlerts}</strong>
          <small>Events requiring review</small>
        </div>
      </div>

      <div className="dashboard-section" id="live-cctv">
        <div>
          <span className="eyebrow">MONITORING</span>
          <h3>Live CCTV Feed</h3>
        </div>

        <div className="cctv-grid">
          {cameras.map((camera) => (
            <CCTVFeed
              key={camera.id}
              cameraName={camera.name}
              location={camera.location}
              status={camera.status}
            />
          ))}
        </div>
      </div>

      <div className="dashboard-section" id="alerts">
        <AlertCenter />
      </div>

      <div className="dashboard-section" id="detection-results">
        <DetectionResults
          detections={detections}
          onStatusChange={handleDetectionStatusChange}
        />
      </div>

      <div className="dashboard-section" id="statistics">
        <Statistics />
      </div>

      <div className="dashboard-section" id="reports">
        <Reports />
      </div>

      <div className="dashboard-section" id="user-management">
        <UserManagement />
      </div>
    </section>
  );
}

export default Dashboard;
