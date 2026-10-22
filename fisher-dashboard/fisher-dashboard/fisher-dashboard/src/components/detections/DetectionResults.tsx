import { useState } from "react";
import { getCameras } from "../../services/dashboardService";
import type { Camera, Detection } from "../../types/dashboard";
import { getMediaUrl } from "../../services/dashboardApi";

type DetectionFilter = "all" | "new" | "reviewed" | "dismissed";
type SeverityFilter = "all" | "low" | "medium" | "high" | "critical";

interface DetectionResultsProps {
  detections: Detection[];
  cameras?: Camera[];
  onStatusChange: (
    detectionId: string,
    status: "new" | "reviewed" | "dismissed",
  ) => void;
}

function DetectionResults({
  detections,
  cameras: propCameras,
  onStatusChange,
}: DetectionResultsProps) {
  const [activeFilter, setActiveFilter] = useState<DetectionFilter>("all");
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [selectedDetectionId, setSelectedDetectionId] = useState<string | null>(
    null,
  );

  const cameras = propCameras && propCameras.length > 0 ? propCameras : getCameras();

  const filteredDetections = detections.filter((detection) => {
    const matchesStatus =
      activeFilter === "all" || detection.status === activeFilter;

    const matchesSeverity =
      severityFilter === "all" || detection.severity === severityFilter;

    return matchesStatus && matchesSeverity;
  });

  const selectedDetection = detections.find(
    (detection) => detection.id === selectedDetectionId,
  );

  const selectedCamera = selectedDetection
    ? cameras.find((camera) => camera.id === selectedDetection.cameraId)
    : undefined;

  const handleStatusUpdate = (status: "reviewed" | "dismissed") => {
    if (!selectedDetectionId) {
      return;
    }

    onStatusChange(selectedDetectionId, status);
  };

  return (
    <div className="detection-results">
      <div className="detection-toolbar">
        <div>
          <span className="eyebrow">AI ANALYSIS</span>
          <h3>Detection Results</h3>
        </div>

        <div className="detection-filters">
          <button
            type="button"
            className={
              activeFilter === "all" ? "filter-button active" : "filter-button"
            }
            onClick={() => setActiveFilter("all")}
          >
            All
          </button>

          <button
            type="button"
            className={
              activeFilter === "new" ? "filter-button active" : "filter-button"
            }
            onClick={() => setActiveFilter("new")}
          >
            New
          </button>

          <button
            type="button"
            className={
              activeFilter === "reviewed"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() => setActiveFilter("reviewed")}
          >
            Reviewed
          </button>

          <button
            type="button"
            className={
              activeFilter === "dismissed"
                ? "filter-button active"
                : "filter-button"
            }
            onClick={() => setActiveFilter("dismissed")}
          >
            Dismissed
          </button>
        </div>
      </div>

      <div className="severity-filters">
        <span>Severity</span>

        <button
          type="button"
          className={
            severityFilter === "all"
              ? "severity-filter active"
              : "severity-filter"
          }
          onClick={() => setSeverityFilter("all")}
        >
          All
        </button>

        <button
          type="button"
          className={
            severityFilter === "low"
              ? "severity-filter active"
              : "severity-filter"
          }
          onClick={() => setSeverityFilter("low")}
        >
          Low
        </button>

        <button
          type="button"
          className={
            severityFilter === "medium"
              ? "severity-filter active"
              : "severity-filter"
          }
          onClick={() => setSeverityFilter("medium")}
        >
          Medium
        </button>

        <button
          type="button"
          className={
            severityFilter === "high"
              ? "severity-filter active"
              : "severity-filter"
          }
          onClick={() => setSeverityFilter("high")}
        >
          High
        </button>

        <button
          type="button"
          className={
            severityFilter === "critical"
              ? "severity-filter active"
              : "severity-filter"
          }
          onClick={() => setSeverityFilter("critical")}
        >
          Critical
        </button>
      </div>

      <div className="detection-table-wrapper">
        <table className="detection-table">
          <thead>
            <tr>
              <th>Detection</th>
              <th>Camera</th>
              <th>Confidence</th>
              <th>Severity</th>
              <th>Time</th>
              <th>Status</th>
            </tr>
          </thead>

          <tbody>
            {filteredDetections.map((detection) => {
              const camera = cameras.find(
                (cameraItem) => cameraItem.id === detection.cameraId,
              );

              const severityClass = "severity-badge " + detection.severity;
              const statusClass = "detection-status " + detection.status;
              const isSelected = selectedDetectionId === detection.id;

              return (
                <tr
                  key={detection.id}
                  className={
                    isSelected ? "detection-row selected" : "detection-row"
                  }
                  onClick={() => setSelectedDetectionId(detection.id)}
                >
                  <td>
                    <div className="detection-name">
                      <strong>{detection.type}</strong>
                      <span>{detection.id}</span>
                    </div>
                  </td>

                  <td>
                    <div className="camera-cell">
                      <strong>{camera ? camera.name : "PC Camera (OpenCV)"}</strong>
                      <span>{camera ? camera.location : "Local Workstation"}</span>
                    </div>
                  </td>

                  <td>
                    <span className="confidence-value">
                      {Math.round(detection.confidence)}%
                    </span>
                  </td>

                  <td>
                    <span className={severityClass}>{detection.severity}</span>
                  </td>

                  <td>
                    <span className="detection-time">
                      {detection.timestamp}
                    </span>
                  </td>

                  <td>
                    <span className={statusClass}>{detection.status}</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filteredDetections.length === 0 && (
          <div className="detection-empty" style={{ textAlign: "center", padding: "40px 16px" }}>
            <strong style={{ display: "block", color: "#cbd5e1", marginBottom: "6px" }}>
              No detection events recorded
            </strong>
            <span style={{ color: "#64748b", fontSize: "13px" }}>
              The system is monitoring the live camera feed. New genuine detection events will appear here in real time.
            </span>
          </div>
        )}
      </div>

      {selectedDetection && (
        <div className="detection-details">
          <div className="detection-details-header">
            <div>
              <span className="eyebrow">SELECTED DETECTION</span>
              <h4>{selectedDetection.type}</h4>
            </div>

            <button
              type="button"
              className="detection-close"
              onClick={() => setSelectedDetectionId(null)}
              aria-label="Close detection details"
            >
              ×
            </button>
          </div>

          <div className="detection-details-grid">
            <div>
              <span>Detection ID</span>
              <strong>{selectedDetection.id}</strong>
            </div>

            <div>
              <span>Camera</span>
              <strong>
                {selectedCamera ? selectedCamera.name : "PC Camera (OpenCV)"}
              </strong>
            </div>

            <div>
              <span>Location</span>
              <strong>
                {selectedCamera ? selectedCamera.location : "Local Workstation"}
              </strong>
            </div>

            <div>
              <span>Confidence</span>
              <strong>{Math.round(selectedDetection.confidence)}%</strong>
            </div>

            <div>
              <span>Severity</span>
              <strong className="detection-detail-severity">
                {selectedDetection.severity}
              </strong>
            </div>

            <div>
              <span>Status</span>
              <strong>{selectedDetection.status}</strong>
            </div>

            <div>
              <span>Timestamp</span>
              <strong>{selectedDetection.timestamp}</strong>
            </div>
          </div>

          {selectedDetection.imageUrl && (
            <div style={{ marginTop: "16px", marginBottom: "16px" }}>
              <span style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "6px" }}>
                Captured Evidence Snapshot:
              </span>
              <img
                src={getMediaUrl(selectedDetection.imageUrl)}
                alt="Detection evidence"
                style={{ maxWidth: "100%", maxHeight: "240px", borderRadius: "8px", border: "1px solid #334155" }}
                onError={(e) => {
                  (e.target as HTMLElement).style.display = "none";
                }}
              />
            </div>
          )}

          <div className="detection-actions">
            <span>Operator Actions</span>

            <div>
              <button
                type="button"
                className="detection-action review"
                onClick={() => handleStatusUpdate("reviewed")}
                disabled={selectedDetection.status === "reviewed"}
              >
                Mark as Reviewed
              </button>

              <button
                type="button"
                className="detection-action dismiss"
                onClick={() => handleStatusUpdate("dismissed")}
                disabled={selectedDetection.status === "dismissed"}
              >
                Dismiss Detection
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DetectionResults;
