"use client";

import { useState, useEffect } from "react";
import { apiClient } from "../../lib/api";
import { useErrorHandler } from "../../lib/error-handler";

/**
 * Plan Generation & Viewing UI (Sprint 8).
 * List plans and generate new plans from quotes.
 */

export default function PlansPage() {
  const { handleApiError } = useErrorHandler();
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [plans, setPlans] = useState<any[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [quoteId, setQuoteId] = useState<string>("");

  useEffect(() => {
    handleLogin();
  }, []);

  useEffect(() => {
    if (authToken) {
      fetchPlans();
    }
  }, [authToken]);

  const handleLogin = async () => {
    try {
      const response = await apiClient.login("customer_001", "CUSTOMER");
      apiClient.setAuthToken(response.access_token);
      setAuthToken(response.access_token);
    } catch (err) {
      handleApiError(err);
    }
  };

  const fetchPlans = async () => {
    if (!authToken) return;

    setLoading(true);
    try {
      const response = await apiClient.listPlans();
      setPlans(response.plans || []);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlanDetails = async (planId: string) => {
    if (!authToken) return;

    setLoading(true);
    try {
      const plan = await apiClient.getPlan(planId);
      setSelectedPlan(plan);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGeneratePlan = async () => {
    if (!authToken || !quoteId.trim()) {
      handleApiError(new Error("Quote ID required"));
      return;
    }

    setLoading(true);
    try {
      const plan = await apiClient.generatePlan(quoteId);
      setSelectedPlan(plan);
      await fetchPlans();
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1400, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <h1>Plans</h1>
        {authToken && (
          <div style={{ color: "green", fontSize: 14 }}>✓ Authenticated</div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "400px 1fr", gap: 24 }}>
        {/* Plans List */}
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>Plan List</h2>

          {/* Generate New Plan */}
          <div style={{ marginTop: 16, marginBottom: 24, padding: 16, backgroundColor: "#f0f9ff", borderRadius: 4 }}>
            <div style={{ fontWeight: "bold", marginBottom: 8 }}>Generate Plan</div>
            <input
              type="text"
              value={quoteId}
              onChange={(e) => setQuoteId(e.target.value)}
              placeholder="Quote ID"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
                marginBottom: 8,
              }}
            />
            <button
              onClick={handleGeneratePlan}
              disabled={loading || !quoteId.trim()}
              style={{
                width: "100%",
                padding: "8px 16px",
                backgroundColor: loading || !quoteId.trim() ? "#ccc" : "#0070f3",
                color: "white",
                border: "none",
                borderRadius: 4,
                cursor: loading || !quoteId.trim() ? "not-allowed" : "pointer",
              }}
            >
              {loading ? "Generating..." : "Generate Plan"}
            </button>
          </div>

          {loading && <div style={{ marginTop: 16 }}>Loading...</div>}
          {!loading && plans.length === 0 && (
            <div style={{ marginTop: 16, padding: 16, color: "#666", fontStyle: "italic" }}>
              No plans found
            </div>
          )}

          <div style={{ maxHeight: 600, overflowY: "auto" }}>
            {plans.map((plan) => (
              <div
                key={plan.id}
                onClick={() => fetchPlanDetails(plan.id)}
                style={{
                  padding: 12,
                  marginBottom: 8,
                  border: "1px solid #ddd",
                  borderRadius: 4,
                  cursor: "pointer",
                  backgroundColor: selectedPlan?.id === plan.id ? "#f0f9ff" : "white",
                  borderColor: selectedPlan?.id === plan.id ? "#0070f3" : "#ddd",
                }}
              >
                <div style={{ fontWeight: "bold", fontSize: 14 }}>{plan.id}</div>
                <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                  State: <strong>{plan.state || "draft"}</strong> • Version: {plan.version || 1}
                </div>
                {plan.steps && (
                  <div style={{ fontSize: 11, color: "#999", marginTop: 4 }}>
                    {plan.steps.length} steps
                  </div>
                )}
              </div>
            ))}
          </div>

          <button
            onClick={fetchPlans}
            style={{
              marginTop: 16,
              width: "100%",
              padding: "8px 16px",
              backgroundColor: "#0070f3",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            Refresh
          </button>
        </section>

        {/* Plan Detail */}
        <section>
          {selectedPlan ? (
            <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 24 }}>
                <div>
                  <h2 style={{ margin: 0 }}>Plan Details</h2>
                  <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
                    Plan ID: <code>{selectedPlan.id}</code>
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div
                    style={{
                      padding: "4px 12px",
                      backgroundColor:
                        selectedPlan.state === "approved"
                          ? "#f0fff0"
                          : selectedPlan.state === "submitted"
                          ? "#fffbf0"
                          : "#f5f5f5",
                      border: `1px solid ${
                        selectedPlan.state === "approved"
                          ? "#0a0"
                          : selectedPlan.state === "submitted"
                          ? "#fa0"
                          : "#ddd"
                      }`,
                      borderRadius: 4,
                      fontSize: 12,
                      fontWeight: "bold",
                      color:
                        selectedPlan.state === "approved"
                          ? "#0a0"
                          : selectedPlan.state === "submitted"
                          ? "#d97706"
                          : "#666",
                    }}
                  >
                    {selectedPlan.state?.toUpperCase() || "DRAFT"}
                  </div>
                  <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                    Version {selectedPlan.version || 1}
                  </div>
                </div>
              </div>

              {/* Plan Metadata */}
              <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                <div>
                  <strong>Quote ID:</strong> {selectedPlan.quote_id || "N/A"}
                </div>
                <div>
                  <strong>Org ID:</strong> {selectedPlan.org_id || "N/A"}
                </div>
              </div>

              {/* Steps List */}
              {selectedPlan.steps && selectedPlan.steps.length > 0 && (
                <div style={{ marginTop: 24 }}>
                  <h3>Steps ({selectedPlan.steps.length})</h3>
                  <div style={{ marginTop: 16, maxHeight: 500, overflowY: "auto" }}>
                    {selectedPlan.steps.map((step: any, idx: number) => {
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
                              {step.locked_sequence && (
                                <div style={{ fontSize: 11, color: "#d97706", marginTop: 4 }}>
                                  🔒 Sequence Locked
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
                                SOE
                              </div>
                            )}
                          </div>

                          {step.source_rules && step.source_rules.length > 0 && (
                            <div style={{ marginTop: 8, fontSize: 11, color: "#666" }}>
                              Source Rules: {step.source_rules.map((r: any) => r.rule_id || "unknown").join(", ")}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Navigation */}
              <div style={{ marginTop: 32, padding: 16, backgroundColor: "#f5f5f5", borderRadius: 4 }}>
                <a
                  href={`/plans/${selectedPlan.id}`}
                  style={{
                    display: "inline-block",
                    padding: "8px 16px",
                    backgroundColor: "#0070f3",
                    color: "white",
                    textDecoration: "none",
                    borderRadius: 4,
                  }}
                >
                  View Full Plan Details →
                </a>
              </div>
            </div>
          ) : (
            <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 48, textAlign: "center", color: "#666" }}>
              <p>Select a plan from the list to view details</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
