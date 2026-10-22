import { useEffect, useState } from "react";
import { getReports } from "../../services/dashboardService";
import {
  fetchReports,
  generateReport,
  fetchReportById,
} from "../../services/dashboardApi";
import type { Report } from "../../types/dashboard";

function Reports() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [reportList, setReportList] = useState<Report[]>(() => getReports());
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    fetchReports()
      .then((data) => {
        if (Array.isArray(data)) {
          setReportList(data);
        }
      })
      .catch(() => {
        // Fall back to local data if backend is offline
        setReportList(getReports());
      });
  }, []);

  const handleGenerateReport = async () => {
    if (isGenerating) {
      return;
    }

    setIsGenerating(true);
    setMessage(null);

    try {
      const newReport = await generateReport("AI CCTV Activity & Intrusion Report");
      if (newReport) {
        setReportList((current) => [newReport, ...current.filter((r) => r.id !== newReport.id)]);
        setMessage(`Report ${newReport.id} successfully compiled from genuine database events.`);
      }
    } catch (err: unknown) {
      const errMsg = err instanceof Error ? err.message : "Failed to compile report from database records.";
      setMessage(errMsg);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleViewReport = async (reportId: string) => {
    setLoadingDetail(true);
    setMessage(null);

    try {
      const detailed = await fetchReportById(reportId);
      setSelectedReport(detailed);
    } catch {
      // Fallback to local report if API is offline
      const local = reportList.find((r) => r.id === reportId) || null;
      setSelectedReport(local);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleCloseReport = () => {
    setSelectedReport(null);
  };

  return (
    <div className="reports">
      <div className="reports-header">
        <div>
          <span className="eyebrow">SECURITY DOCUMENTATION</span>
          <h3>Reports & Evidence Archive</h3>
          <p>
            Audit and review AI detection reports compiled from genuine CCTV events, captured intrusion photos, and 2-minute incident videos.
          </p>
        </div>

        <button
          type="button"
          className="report-action"
          onClick={handleGenerateReport}
          disabled={isGenerating}
        >
          {isGenerating ? "Compiling Real Records..." : "Generate Report"}
        </button>
      </div>

      {message && (
        <div style={{
          marginTop: "12px",
          padding: "10px 14px",
          borderRadius: "6px",
          fontSize: "11px",
          background: message.includes("success") ? "rgba(34, 197, 94, 0.12)" : "rgba(239, 68, 68, 0.12)",
          color: message.includes("success") ? "#4ade80" : "#f87171",
          border: `1px solid ${message.includes("success") ? "rgba(34, 197, 94, 0.25)" : "rgba(239, 68, 68, 0.25)"}`
        }}>
          {message}
        </div>
      )}

      <div className="reports-list">
        {reportList.length === 0 ? (
          <div style={{
            padding: "36px",
            textAlign: "center",
            background: "#0b1017",
            border: "1px dashed #1c2632",
            borderRadius: "8px",
            color: "#64748b",
            fontSize: "12px",
            marginTop: "18px"
          }}>
            No security reports available. Click &quot;Generate Report&quot; to compile genuine CCTV records from MongoDB.
          </div>
        ) : (
          reportList.map((report) => (
            <div className="report-item" key={report.id}>
              <div className="report-icon">▤</div>

              <div className="report-info">
                <strong>{report.title}</strong>
                <span>{report.id}</span>
              </div>

              <div className="report-date">
                <span>Created</span>
                <strong>{report.createdAt}</strong>
              </div>

              <div className={`report-status ${report.status}`}>
                {report.status}
              </div>

              <button
                type="button"
                className="report-view"
                onClick={() => handleViewReport(report.id)}
                disabled={loadingDetail}
              >
                View
              </button>
            </div>
          ))
        )}
      </div>

      {/* DEDICATED REPORT & MEDIA MODAL */}
      {selectedReport && (
        <div className="report-modal-overlay" onClick={handleCloseReport}>
          <div
            className="report-modal-container"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="report-modal-title"
          >
            <div className="report-modal-header">
              <div className="report-modal-title-wrap">
                <span className="eyebrow">OFFICIAL SECURITY REPORT</span>
                <h3 id="report-modal-title">{selectedReport.title}</h3>
                <span className="report-meta-sub">
                  Report ID: {selectedReport.id} • Generated: {selectedReport.createdAt} • Status: {selectedReport.status.toUpperCase()}
                </span>
              </div>

              <button
                type="button"
                className="report-modal-close-btn"
                onClick={handleCloseReport}
                aria-label="Close report modal"
              >
                ×
              </button>
            </div>

            <div className="report-modal-body">
              <div className="report-summary-card">
                <span className="eyebrow">AUDIT SUMMARY</span>
                <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "12px", lineHeight: "1.6" }}>
                  {selectedReport.summary ||
                    "This report compiles verified CCTV events, timestamps, alert classifications, and media recordings stored in MongoDB Atlas."}
                </p>

                <div className="report-summary-stats">
                  <div className="report-stat-item">
                    <span>Total AI Detections</span>
                    <strong>{selectedReport.totalDetections ?? selectedReport.detections?.length ?? 0}</strong>
                  </div>
                  <div className="report-stat-item danger">
                    <span>High / Critical Incidents</span>
                    <strong>{selectedReport.highSeverityCount ?? 0}</strong>
                  </div>
                  <div className="report-stat-item">
                    <span>Camera Sources</span>
                    <strong>CAM-001 (Live PC)</strong>
                  </div>
                </div>
              </div>

              <div className="report-events-section-title">
                <span>Verified Event Records & Media Evidence</span>
                <span style={{ fontSize: "11px", fontWeight: "normal", color: "#64748b" }}>
                  ({selectedReport.detections?.length || 0} events attached)
                </span>
              </div>

              {(!selectedReport.detections || selectedReport.detections.length === 0) ? (
                <div className="report-events-empty">
                  No detection events or intrusion incidents recorded in the database during this period.
                </div>
              ) : (
                selectedReport.detections.map((event, idx) => {
                  const severityClass = event.severity || "medium";
                  const confidencePercent = Math.round((event.confidence || 0.85) * 100);

                  return (
                    <div className="report-event-card" key={event.id || idx}>
                      <div className="report-event-header">
                        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                          <span className={`report-event-badge ${severityClass}`}>
                            {severityClass} severity
                          </span>
                          <strong style={{ fontSize: "13px", color: "#f1f5f9" }}>
                            {event.type.toUpperCase()}
                          </strong>
                        </div>

                        <div className="report-event-info">
                          <span>
                            Camera: <strong>{event.cameraName || event.cameraId || "CAM-001"}</strong>
                          </span>
                          <span>
                            Timestamp: <strong>{event.timestamp}</strong>
                          </span>
                          <span>
                            Confidence: <strong>{confidencePercent}%</strong>
                          </span>
                        </div>
                      </div>

                      <div className="report-event-media-grid">
                        {/* INTRUSION IMAGE */}
                        <div className="report-media-box">
                          <span className="report-media-label">
                            Captured Intrusion Image
                          </span>
                          {event.imageUrl ? (
                            <img
                              src={event.imageUrl}
                              alt={`Intrusion ${event.type}`}
                              className="report-media-img"
                              onError={(e) => {
                                const target = e.currentTarget;
                                target.style.display = "none";
                                const parent = target.parentElement;
                                if (parent) {
                                  const fallback = document.createElement("div");
                                  fallback.className = "report-media-empty";
                                  fallback.innerText = "Intrusion image file not available on storage server";
                                  parent.appendChild(fallback);
                                }
                              }}
                            />
                          ) : (
                            <div className="report-media-empty">
                              No intrusion image recorded for this event
                            </div>
                          )}
                        </div>

                        {/* 2-MINUTE VIDEO */}
                        <div className="report-media-box">
                          <span className="report-media-label">
                            Associated 2-Minute Incident Video
                          </span>
                          {event.videoUrl ? (
                            <video
                              controls
                              preload="metadata"
                              className="report-media-video"
                              src={event.videoUrl}
                            >
                              Your browser does not support HTML5 video playback.
                            </video>
                          ) : (
                            <div className="report-media-empty">
                              No 2-minute video recording attached to this event
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>

            <div className="report-modal-footer">
              <button
                type="button"
                className="report-modal-close-action"
                onClick={handleCloseReport}
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
