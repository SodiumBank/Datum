"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "../../../lib/api";
import { useErrorHandler } from "../../../lib/error-handler";

/**
 * Plan Detail Page - View full plan details with editing capabilities (Sprint 8).
 */

export default function PlanDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { handleApiError } = useErrorHandler();
  const planId = params.planId as string;

  const [authToken, setAuthToken] = useState<string | null>(null);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editedPlan, setEditedPlan] = useState<any>(null);

  useEffect(() => {
    handleLogin();
  }, []);

  useEffect(() => {
    if (authToken && planId) {
      fetchPlan();
    }
  }, [authToken, planId]);

  const handleLogin = async () => {
    try {
      const response = await apiClient.login("customer_001", "CUSTOMER");
      apiClient.setAuthToken(response.access_token);
      setAuthToken(response.access_token);
    } catch (err) {
      handleApiError(err);
    }
  };

  const fetchPlan = async () => {
    if (!authToken || !planId) return;

    setLoading(true);
    try {
      const planData = await apiClient.getPlan(planId);
      setPlan(planData);
      setEditedPlan(planData);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitForApproval = async () => {
    if (!authToken || !planId) return;

    setLoading(true);
    try {
      await apiClient.submitPlan(planId, "Submitted from UI");
      await fetchPlan();
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !plan) {
    return (
      <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
        <div>Loading plan...</div>
      </main>
    );
  }

  if (!plan) {
    return (
      <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
        <div>Plan not found</div>
        <a href="/plans" style={{ color: "#0070f3", textDecoration: "underline" }}>
          ← Back to Plans
        </a>
      </main>
    );
  }

  const canEdit = plan.state === "draft" && !plan.locked;

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <a
          href="/plans"
          style={{ color: "#0070f3", textDecoration: "underline", marginBottom: 16, display: "inline-block" }}
        >
          ← Back to Plans
        </a>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16 }}>
          <div>
            <h1 style={{ margin: 0 }}>Plan: {plan.id}</h1>
            <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
              Version {plan.version || 1} • {plan.state || "draft"}
            </div>
          </div>
          <div>
            {canEdit && (
              <button
                onClick={() => setEditMode(!editMode)}
                style={{
                  padding: "8px 16px",
                  backgroundColor: editMode ? "#666" : "#0070f3",
                  color: "white",
                  border: "none",
                  borderRadius: 4,
                  cursor: "pointer",
                  marginRight: 8,
                }}
              >
                {editMode ? "Cancel Edit" : "Edit Plan"}
              </button>
            )}
            {plan.state === "draft" && (
              <button
                onClick={handleSubmitForApproval}
                disabled={loading}
                style={{
                  padding: "8px 16px",
                  backgroundColor: loading ? "#ccc" : "#0070f3",
                  color: "white",
                  border: "none",
                  borderRadius: 4,
                  cursor: loading ? "not-allowed" : "pointer",
                }}
              >
                {loading ? "Submitting..." : "Submit for Approval"}
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Plan Metadata */}
      <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24, marginBottom: 24 }}>
        <h2>Plan Information</h2>
        <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div>
            <strong>Quote ID:</strong> {plan.quote_id || "N/A"}
          </div>
          <div>
            <strong>State:</strong> {plan.state || "draft"}
          </div>
          <div>
            <strong>Version:</strong> {plan.version || 1}
          </div>
          <div>
            <strong>Locked:</strong> {plan.locked ? "Yes" : "No"}
          </div>
        </div>
      </section>

      {/* Steps */}
      {plan.steps && plan.steps.length > 0 && (
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>Manufacturing Steps ({plan.steps.length})</h2>
          <div style={{ marginTop: 16 }}>
            {plan.steps.map((step: any, idx: number) => {
              const isSOELocked =
                step.soe_decision_id || step.locked_sequence || step.source_rules?.some((r: any) => r.ruleset_version === 1);

              return (
                <div
                  key={idx}
                  style={{
                    marginBottom: 12,
                    padding: 16,
                    border: `2px solid ${isSOELocked ? "#fcc" : "#ddd"}`,
                    borderRadius: 4,
                    backgroundColor: isSOELocked ? "#fffbf0" : "#fff",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "bold", marginBottom: 4 }}>
                        {step.sequence || idx + 1}. {step.title || step.type}
                      </div>
                      <div style={{ fontSize: 12, color: "#666" }}>
                        Type: {step.type} • Required: {step.required ? "Yes" : "No"}
                      </div>
                      {step.soe_decision_id && (
                        <div style={{ fontSize: 11, color: "#d97706", marginTop: 4 }}>
                          🔒 SOE Locked (Decision: {step.soe_decision_id})
                        </div>
                      )}
                      {step.source_rules && step.source_rules.length > 0 && (
                        <div style={{ marginTop: 8, fontSize: 11, color: "#666" }}>
                          Source Rules: {step.source_rules.map((r: any) => r.rule_id || "unknown").join(", ")}
                        </div>
                      )}
                    </div>
                    {isSOELocked && (
                      <div
                        style={{
                          padding: "2px 8px",
                          backgroundColor: "#fffbf0",
                          border: "1px solid #fa0",
                          borderRadius: 4,
                          fontSize: 11,
                          color: "#d97706",
                          fontWeight: "bold",
                        }}
                      >
                        SOE LOCKED
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </main>
  );
}
