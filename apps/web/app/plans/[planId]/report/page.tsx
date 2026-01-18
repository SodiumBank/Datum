"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "../../../../lib/api";
import { useErrorHandler } from "../../../../lib/error-handler";

/**
 * Compliance Report Access UI (Sprint 8 - Story 7).
 * Generate and view compliance reports for plans.
 */

export default function ComplianceReportPage() {
  const params = useParams();
  const { handleApiError } = useErrorHandler();
  const planId = params.planId as string;

  const [authToken, setAuthToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<any>(null);
  const [reportFormat, setReportFormat] = useState<"html" | "pdf">("html");

  useEffect(() => {
    handleLogin();
  }, []);

  const handleLogin = async () => {
    try {
      const response = await apiClient.login("customer_001", "CUSTOMER");
      apiClient.setAuthToken(response.access_token);
      setAuthToken(response.access_token);
    } catch (err) {
      handleApiError(err);
    }
  };

  const handleGenerateReport = async () => {
    if (!authToken || !planId) return;

    setLoading(true);
    setReport(null);

    try {
      const reportData = await apiClient.getComplianceReport(planId, reportFormat);
      setReport(reportData);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <a
          href={`/plans/${planId}`}
          style={{ color: "#0070f3", textDecoration: "underline", marginBottom: 16, display: "inline-block" }}
        >
          ← Back to Plan
        </a>
        <h1 style={{ margin: 0 }}>Compliance Report: {planId}</h1>
      </div>

      {/* Generate Report Controls */}
      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24, marginBottom: 24 }}>
        <h2>Generate Compliance Report</h2>
        <div style={{ marginTop: 16, display: "flex", gap: 16, alignItems: "center" }}>
          <div>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>Format:</label>
            <select
              value={reportFormat}
              onChange={(e) => setReportFormat(e.target.value as "html" | "pdf")}
              style={{
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            >
              <option value="html">HTML</option>
              <option value="pdf">PDF</option>
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <button
              onClick={handleGenerateReport}
              disabled={loading}
              style={{
                padding: "12px 24px",
                backgroundColor: loading ? "#ccc" : "#0070f3",
                color: "white",
                border: "none",
                borderRadius: 4,
                cursor: loading ? "not-allowed" : "pointer",
                fontWeight: "bold",
              }}
            >
              {loading ? "Generating..." : "Generate Report"}
            </button>
          </div>
        </div>
      </section>

      {/* Report Viewer */}
      {report && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>Compliance Report</h2>

          {/* Report Metadata */}
          {report.metadata && (
            <div style={{ marginTop: 16, padding: 16, backgroundColor: "#f0f9ff", borderRadius: 4 }}>
              <div style={{ fontWeight: "bold", marginBottom: 8 }}>Report Metadata</div>
              <div style={{ fontSize: 12, color: "#666" }}>
                {report.metadata.plan_version && (
                  <div>Plan Version: {report.metadata.plan_version}</div>
                )}
                {report.metadata.report_hash && (
                  <div>Report Hash: <code style={{ fontSize: 11 }}>{report.metadata.report_hash}</code></div>
                )}
                {report.metadata.generated_at && (
                  <div>Generated At: {report.metadata.generated_at}</div>
                )}
              </div>
            </div>
          )}

          {/* Report Content */}
          {reportFormat === "html" && report.content && (
            <div
              style={{ marginTop: 24 }}
              dangerouslySetInnerHTML={{ __html: report.content }}
            />
          )}

          {reportFormat === "html" && !report.content && report.report && (
            <div style={{ marginTop: 24, padding: 16, border: "1px solid #ddd", borderRadius: 4 }}>
              <pre style={{ fontSize: 12, overflow: "auto", whiteSpace: "pre-wrap" }}>
                {JSON.stringify(report.report, null, 2)}
              </pre>
            </div>
          )}

          {reportFormat === "pdf" && (
            <div style={{ marginTop: 24, padding: 32, textAlign: "center", color: "#666" }}>
              PDF report generation is available. Download link or binary content would be displayed here.
            </div>
          )}
        </section>
      )}

      {!report && !loading && (
        <div style={{ padding: 48, textAlign: "center", color: "#666" }}>
          <p>Generate a compliance report to view it here</p>
        </div>
      )}
    </main>
  );
}
