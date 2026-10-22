import { useEffect, useState } from "react";
import {
  getCameras,
  getDashboardStatistics,
} from "../services/dashboardService";
import {
  fetchCameras,
  fetchDashboardStatistics,
  fetchDetections,
  setDetectionStatus,
} from "../services/dashboardApi";
import type { Camera, DashboardStatistics, Detection } from "../types/dashboard";
import CCTVFeed from "../components/cctv/CCTVFeed";
import DetectionResults from "../components/detections/DetectionResults";
import Reports from "../components/reports/Reports";
import UserManagement from "../components/users/UserManagement";
import AlertCenter from "../components/alerts/AlertCenter";

function Dashboard() {
  const [cameras, setCameras] = useState<Camera[]>(() => getCameras());
  const [dashboardStatistics, setDashboardStatistics] =
    useState<DashboardStatistics>(() => getDashboardStatistics());
  const [detections, setDetections] = useState<Detection[]>([]);

  useEffect(() => {
    let isMounted = true;

    async function loadBackendData() {
      try {
        const [camerasResult, statsResult, detectionsResult] =
          await Promise.allSettled([
            fetchCameras(),
            fetchDashboardStatistics(),
            fetchDetections(),
          ]);

        if (!isMounted) return;

        if (
          camerasResult.status === "fulfilled" &&
          Array.isArray(camerasResult.value) &&
          camerasResult.value.length > 0
        ) {
          setCameras(camerasResult.value);
        }

        if (statsResult.status === "fulfilled" && statsResult.value) {
          setDashboardStatistics(statsResult.value);
        }

        if (
          detectionsResult.status === "fulfilled" &&
          Array.isArray(detectionsResult.value)
        ) {
          setDetections(detectionsResult.value);
        }
      } catch {
        // Backend offline fallback
      }
    }

    void loadBackendData();

    // Periodic sync with the backend
    const intervalId = setInterval(() => {
      void loadBackendData();
    }, 2500);

    return () => {
      isMounted = false;
      clearInterval(intervalId);
    };
  }, []);

  const offlineCameras =
    dashboardStatistics.totalCameras - dashboardStatistics.onlineCameras;

  const handleDetectionStatusChange = async (
    detectionId: string,
    status: "new" | "reviewed" | "dismissed",
  ) => {
    // Optimistic local state update
    setDetections((currentDetections) =>
      currentDetections.map((detection) =>
        detection.id === detectionId ? { ...detection, status } : detection,
      ),
    );

    try {
      await setDetectionStatus(detectionId, status);
      const updatedStats = await fetchDashboardStatistics();
      setDashboardStatistics(updatedStats);
    } catch {
      // Ignored
    }
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
            Monitor real PC camera activity, review AI detections, and investigate
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
          <small>{offlineCameras > 0 ? `${offlineCameras} offline` : "All systems operational"}</small>
        </div>

        <div className="dashboard-card">
          <span>DETECTIONS</span>
          <strong>{dashboardStatistics.totalDetections}</strong>
          <small>Total AI detections logged</small>
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
              streamUrl={camera.streamUrl}
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
          cameras={cameras}
          onStatusChange={handleDetectionStatusChange}
        />
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
