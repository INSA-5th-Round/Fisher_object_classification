import { useState } from "react";
import { getCameras, getDetections } from "../../services/dashboardService";

type Severity = "low" | "medium" | "high" | "critical";

function Statistics() {
  const [selectedSeverity, setSelectedSeverity] = useState<Severity | null>(
    null,
  );

  const detections = getDetections();
  const cameras = getCameras();

  const totalDetections = detections.length;

  const lowDetections = detections.filter(
    (detection) => detection.severity === "low",
  ).length;

  const mediumDetections = detections.filter(
    (detection) => detection.severity === "medium",
  ).length;

  const highDetections = detections.filter(
    (detection) => detection.severity === "high",
  ).length;

  const criticalDetections = detections.filter(
    (detection) => detection.severity === "critical",
  ).length;

  const getPercentage = (count: number) => {
    if (totalDetections === 0) {
      return 0;
    }

    return Math.round((count / totalDetections) * 100);
  };

  const selectedDetections = selectedSeverity
    ? detections.filter((detection) => detection.severity === selectedSeverity)
    : [];

  const handleSeverityClick = (severity: Severity) => {
    setSelectedSeverity((current) => (current === severity ? null : severity));
  };

  return (
    <div className="statistics">
      <div className="statistics-header">
        <div>
          <span className="eyebrow">SECURITY ANALYTICS</span>

          <h3>Detection Statistics</h3>

          <p>
            Overview of AI-generated detection activity and severity levels.
          </p>
        </div>

        <div className="statistics-total">
          <span>Total Detections</span>
          <strong>{totalDetections}</strong>
        </div>
      </div>

      <div className="statistics-grid">
        <button
          type="button"
          className={
            selectedSeverity === "low"
              ? "statistics-card selected"
              : "statistics-card"
          }
          onClick={() => handleSeverityClick("low")}
        >
          <div className="statistics-card-header">
            <span>LOW</span>
            <span className="statistics-indicator low"></span>
          </div>

          <strong>{lowDetections}</strong>

          <small>{getPercentage(lowDetections)}% of detections</small>
        </button>

        <button
          type="button"
          className={
            selectedSeverity === "medium"
              ? "statistics-card selected"
              : "statistics-card"
          }
          onClick={() => handleSeverityClick("medium")}
        >
          <div className="statistics-card-header">
            <span>MEDIUM</span>
            <span className="statistics-indicator medium"></span>
          </div>

          <strong>{mediumDetections}</strong>

          <small>{getPercentage(mediumDetections)}% of detections</small>
        </button>

        <button
          type="button"
          className={
            selectedSeverity === "high"
              ? "statistics-card selected"
              : "statistics-card"
          }
          onClick={() => handleSeverityClick("high")}
        >
          <div className="statistics-card-header">
            <span>HIGH</span>
            <span className="statistics-indicator high"></span>
          </div>

          <strong>{highDetections}</strong>

          <small>{getPercentage(highDetections)}% of detections</small>
        </button>

        <button
          type="button"
          className={
            selectedSeverity === "critical"
              ? "statistics-card selected"
              : "statistics-card"
          }
          onClick={() => handleSeverityClick("critical")}
        >
          <div className="statistics-card-header">
            <span>CRITICAL</span>
            <span className="statistics-indicator critical"></span>
          </div>

          <strong>{criticalDetections}</strong>

          <small>{getPercentage(criticalDetections)}% of detections</small>
        </button>
      </div>

      <div className="severity-distribution">
        <div className="severity-distribution-header">
          <div>
            <span className="eyebrow">SEVERITY DISTRIBUTION</span>

            <h4>Detection Activity</h4>
          </div>

          <span>{totalDetections} total</span>
        </div>

        <div className="severity-bar">
          {lowDetections > 0 && (
            <button
              type="button"
              className="severity-bar-segment low"
              style={{
                width: `${getPercentage(lowDetections)}%`,
              }}
              title={`Low: ${lowDetections}`}
              onClick={() => handleSeverityClick("low")}
              aria-label="View low severity detections"
            ></button>
          )}

          {mediumDetections > 0 && (
            <button
              type="button"
              className="severity-bar-segment medium"
              style={{
                width: `${getPercentage(mediumDetections)}%`,
              }}
              title={`Medium: ${mediumDetections}`}
              onClick={() => handleSeverityClick("medium")}
              aria-label="View medium severity detections"
            ></button>
          )}

          {highDetections > 0 && (
            <button
              type="button"
              className="severity-bar-segment high"
              style={{
                width: `${getPercentage(highDetections)}%`,
              }}
              title={`High: ${highDetections}`}
              onClick={() => handleSeverityClick("high")}
              aria-label="View high severity detections"
            ></button>
          )}

          {criticalDetections > 0 && (
            <button
              type="button"
              className="severity-bar-segment critical"
              style={{
                width: `${getPercentage(criticalDetections)}%`,
              }}
              title={`Critical: ${criticalDetections}`}
              onClick={() => handleSeverityClick("critical")}
              aria-label="View critical severity detections"
            ></button>
          )}
        </div>

        <div className="severity-legend">
          <button type="button" onClick={() => handleSeverityClick("low")}>
            <span className="statistics-indicator low"></span>
            <span>Low</span>
            <strong>{lowDetections}</strong>
          </button>

          <button type="button" onClick={() => handleSeverityClick("medium")}>
            <span className="statistics-indicator medium"></span>
            <span>Medium</span>
            <strong>{mediumDetections}</strong>
          </button>

          <button type="button" onClick={() => handleSeverityClick("high")}>
            <span className="statistics-indicator high"></span>
            <span>High</span>
            <strong>{highDetections}</strong>
          </button>

          <button type="button" onClick={() => handleSeverityClick("critical")}>
            <span className="statistics-indicator critical"></span>
            <span>Critical</span>
            <strong>{criticalDetections}</strong>
          </button>
        </div>
      </div>

      {selectedSeverity && (
        <div className="statistics-details">
          <div className="statistics-details-header">
            <div>
              <span className="eyebrow">FILTERED ANALYSIS</span>

              <h4>{selectedSeverity} severity detections</h4>
            </div>

            <button
              type="button"
              className="statistics-clear"
              onClick={() => setSelectedSeverity(null)}
            >
              Clear Selection
            </button>
          </div>

          {selectedDetections.length > 0 ? (
            <div className="statistics-detection-list">
              {selectedDetections.map((detection) => {
                const camera = cameras.find(
                  (cameraItem) => cameraItem.id === detection.cameraId,
                );

                return (
                  <div className="statistics-detection-item" key={detection.id}>
                    <div>
                      <strong>{detection.type}</strong>

                      <span>{detection.id}</span>
                    </div>

                    <div>
                      <span>Camera</span>

                      <strong>{camera ? camera.name : "Unknown"}</strong>
                    </div>

                    <div>
                      <span>Confidence</span>

                      <strong>{detection.confidence}%</strong>
                    </div>

                    <div>
                      <span>Time</span>

                      <strong>{detection.timestamp}</strong>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="statistics-empty">
              No detections found for this severity.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Statistics;
