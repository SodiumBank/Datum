"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { apiClient } from "../../../../lib/api";
import { useErrorHandler } from "../../../../lib/error-handler";

/**
 * Compliance & Standards Visualization (Sprint 8 - Story 6).
 * Display compliance trace, standards stack, and step-level compliance inspection.
 */

export default function CompliancePage() {
  const params = useParams();
  const { handleApiError } = useErrorHandler();
  const planId = params.planId as string;

  const [authToken, setAuthToken] = useState<string | null>(null);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [selectedStep, setSelectedStep] = useState<any | null>(null);

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
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !plan) {
    return (
      <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
        <div>Loading compliance data...</div>
      </main>
    );
  }

  if (!plan) {
    return (
      <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
        <div>Plan not found</div>
        <a href={`/plans/${planId}`} style={{ color: "#0070f3", textDecoration: "underline" }}>
          ← Back to Plan
        </a>
      </main>
    );
  }

  // Extract profile stack from plan (if available from SOE run)
  const profileStack = plan.soe_run?.profile_stack || [];
  const hasOverrides = plan.edit_metadata?.overrides?.length > 0;

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1400, margin: "0 auto" }}>
      <div style={{ marginBottom: 24 }}>
        <a
          href={`/plans/${planId}`}
          style={{ color: "#0070f3", textDecoration: "underline", marginBottom: 16, display: "inline-block" }}
        >
          ← Back to Plan
        </a>
        <h1 style={{ margin: 0 }}>Compliance & Standards: {plan.id}</h1>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "400px 1fr", gap: 24 }}>
        {/* Profile Stack Viewer */}
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>Standards Profile Stack</h2>
          {profileStack.length > 0 ? (
            <div style={{ marginTop: 16 }}>
              {profileStack.map((profile: any, idx: number) => (
                <div
                  key={idx}
                  style={{
                    marginBottom: 12,
                    padding: 12,
                    border: "1px solid #ddd",
                    borderRadius: 4,
                    backgroundColor: profile.layer === 2 ? "#fffbf0" : profile.layer === 1 ? "#f0f9ff" : "#f5f5f5",
                  }}
                >
                  <div style={{ fontWeight: "bold", marginBottom: 4 }}>
                    Layer {profile.layer}: {profile.profile_type}
                  </div>
                  <div style={{ fontSize: 12, color: "#666" }}>
                    {profile.profile_id}
                  </div>
                  {profile.name && (
                    <div style={{ fontSize: 11, color: "#999", marginTop: 4 }}>
                      {profile.name}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ marginTop: 16, padding: 16, color: "#666", fontStyle: "italic" }}>
              No profile stack data available
            </div>
          )}

          {/* Override Warnings */}
          {hasOverrides && (
            <div style={{ marginTop: 24, padding: 16, backgroundColor: "#fffbf0", border: "2px solid #fa0", borderRadius: 4 }}>
              <div style={{ fontWeight: "bold", color: "#d97706", marginBottom: 8 }}>
                ⚠️ Plan Has Overrides
              </div>
              <div style={{ fontSize: 12, color: "#666" }}>
                {plan.edit_metadata.overrides.length} override(s) applied
              </div>
            </div>
          )}
        </section>

        {/* Step Compliance Inspector */}
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>Step Compliance Inspector</h2>
          <p style={{ fontSize: 14, color: "#666", marginTop: 8 }}>
            Click a step to view compliance requirements and source rules
          </p>

          {plan.steps && plan.steps.length > 0 ? (
            <div style={{ marginTop: 16, maxHeight: 600, overflowY: "auto" }}>
              {plan.steps.map((step: any, idx: number) => {
                const isSOELocked =
                  step.soe_decision_id || step.locked_sequence || step.source_rules?.some((r: any) => r.ruleset_version === 1);
                const hasOverrides = plan.edit_metadata?.overrides?.some((o: any) =>
                  o.constraint?.includes(step.step_id || step.title)
                );

                return (
                  <div
                    key={idx}
                    onClick={() => setSelectedStep(selectedStep === step ? null : step)}
                    style={{
                      marginBottom: 12,
                      padding: 16,
                      border: `2px solid ${isSOELocked ? "#fcc" : hasOverrides ? "#faa" : "#ddd"}`,
                      borderRadius: 4,
                      backgroundColor: isSOELocked ? "#fffbf0" : hasOverrides ? "#ffeef0" : "#fff",
                      cursor: "pointer",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: "bold", marginBottom: 4 }}>
                          {step.sequence || idx + 1}. {step.title || step.type}
                        </div>
                        <div style={{ fontSize: 12, color: "#666" }}>
                          Type: {step.type}
                        </div>
                        {isSOELocked && (
                          <div style={{ fontSize: 11, color: "#d97706", marginTop: 4 }}>
                            🔒 SOE Required
                          </div>
                        )}
                        {hasOverrides && (
                          <div style={{ fontSize: 11, color: "#c00", marginTop: 4 }}>
                            ⚠️ Overridden
                          </div>
                        )}
                      </div>
                      <div>
                        {isSOELocked && (
                          <span
                            style={{
                              padding: "2px 8px",
                              backgroundColor: "#fffbf0",
                              border: "1px solid #fa0",
                              borderRadius: 4,
                              fontSize: 11,
                              color: "#d97706",
                              fontWeight: "bold",
                              marginRight: 8,
                            }}
                          >
                            SOE
                          </span>
                        )}
                        {selectedStep === step && (
                          <span style={{ fontSize: 12, color: "#0070f3" }}>▼</span>
                        )}
                        {selectedStep !== step && (
                          <span style={{ fontSize: 12, color: "#666" }}>▶</span>
                        )}
                      </div>
                    </div>

                    {/* Expanded Step Details */}
                    {selectedStep === step && (
                      <div style={{ marginTop: 16, padding: 16, backgroundColor: "#f9f9f9", borderRadius: 4 }}>
                        <h3 style={{ fontSize: 14, marginBottom: 12 }}>Compliance Requirements</h3>

                        {step.source_rules && step.source_rules.length > 0 && (
                          <div style={{ marginBottom: 16 }}>
                            <div style={{ fontWeight: "bold", fontSize: 12, marginBottom: 8 }}>Source Rules:</div>
                            {step.source_rules.map((rule: any, ruleIdx: number) => (
                              <div
                                key={ruleIdx}
                                style={{
                                  marginBottom: 8,
                                  padding: 8,
                                  backgroundColor: "#fff",
                                  border: "1px solid #ddd",
                                  borderRadius: 4,
                                  fontSize: 12,
                                }}
                              >
                                <div style={{ fontWeight: "500" }}>Rule ID: {rule.rule_id || "unknown"}</div>
                                {rule.ruleset_version && (
                                  <div style={{ fontSize: 11, color: "#666", marginTop: 2 }}>
                                    Ruleset Version: {rule.ruleset_version}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}

                        {step.soe_decision_id && (
                          <div style={{ marginBottom: 16 }}>
                            <div style={{ fontWeight: "bold", fontSize: 12, marginBottom: 8 }}>SOE Decision:</div>
                            <div style={{ padding: 8, backgroundColor: "#fffbf0", border: "1px solid #fa0", borderRadius: 4, fontSize: 12 }}>
                              Decision ID: {step.soe_decision_id}
                            </div>
                          </div>
                        )}

                        {step.soe_why && (
                          <div style={{ marginBottom: 16 }}>
                            <div style={{ fontWeight: "bold", fontSize: 12, marginBottom: 8 }}>Why Required:</div>
                            <div style={{ padding: 8, backgroundColor: "#fff", border: "1px solid #ddd", borderRadius: 4, fontSize: 12 }}>
                              <div>Rule: {step.soe_why.rule_id}</div>
                              <div>Pack: {step.soe_why.pack_id}</div>
                              {step.soe_why.citations && step.soe_why.citations.length > 0 && (
                                <div style={{ marginTop: 4, color: "#666" }}>
                                  Citations: {step.soe_why.citations.join(", ")}
                                </div>
                              )}
                            </div>
                          </div>
                        )}

                        {!step.source_rules && !step.soe_decision_id && (
                          <div style={{ fontSize: 12, color: "#666", fontStyle: "italic" }}>
                            No compliance requirements documented for this step
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ marginTop: 16, padding: 32, textAlign: "center", color: "#666" }}>
              No steps found in plan
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
