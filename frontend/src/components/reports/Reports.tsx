import { useState } from "react";
import { getReports } from "../../services/dashboardService";

function Reports() {
  const [isGenerating, setIsGenerating] = useState(false);

  const [reportList, setReportList] = useState(getReports());

  const [selectedReportId, setSelectedReportId] = useState<string | null>(null);

  const selectedReport = reportList.find(
    (report) => report.id === selectedReportId,
  );

  const handleGenerateReport = () => {
    if (isGenerating) {
      return;
    }

    setIsGenerating(true);

    setTimeout(() => {
      const newReport = {
        id: `REP-${String(reportList.length + 1).padStart(3, "0")}`,

        title: "Detection Activity Report",

        createdAt: new Date().toISOString().split("T")[0],

        status: "ready" as const,
      };

      setReportList((currentReports) => [...currentReports, newReport]);

      setIsGenerating(false);
    }, 1500);
  };

  const handleViewReport = (reportId: string) => {
    setSelectedReportId(reportId);
  };

  const handleCloseReport = () => {
    setSelectedReportId(null);
  };

  return (
    <div className="reports">
      <div className="reports-header">
        <div>
          <span className="eyebrow">SECURITY DOCUMENTATION</span>

          <h3>Reports</h3>

          <p>
            Review generated reports from FISHER detection and monitoring
            activity.
          </p>
        </div>

        <button
          type="button"
          className="report-action"
          onClick={handleGenerateReport}
          disabled={isGenerating}
        >
          {isGenerating ? "Generating..." : "Generate Report"}
        </button>
      </div>

      <div className="reports-list">
        {reportList.map((report) => (
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
            >
              View
            </button>
          </div>
        ))}
      </div>

      {selectedReport && (
        <div className="report-details">
          <div className="report-details-header">
            <div>
              <span className="eyebrow">SELECTED REPORT</span>

              <h4>{selectedReport.title}</h4>
            </div>

            <button
              type="button"
              className="report-close"
              onClick={handleCloseReport}
              aria-label="Close report details"
            >
              ×
            </button>
          </div>

          <div className="report-details-grid">
            <div>
              <span>Report ID</span>

              <strong>{selectedReport.id}</strong>
            </div>

            <div>
              <span>Title</span>

              <strong>{selectedReport.title}</strong>
            </div>

            <div>
              <span>Created</span>

              <strong>{selectedReport.createdAt}</strong>
            </div>

            <div>
              <span>Status</span>

              <strong
                className={`report-detail-status ${selectedReport.status}`}
              >
                {selectedReport.status}
              </strong>
            </div>
          </div>

          <div className="report-summary">
            <span>Report Summary</span>

            <p>
              This report contains a summary of FISHER detection and monitoring
              activity for the selected reporting period.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default Reports;
