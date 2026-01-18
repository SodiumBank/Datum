"use client";

import { useState } from "react";
import { apiClient, DatumApiError } from "../../lib/api";
import { useErrorHandler } from "../../lib/error-handler";

/**
 * SOE Run UI - Allow users to run SOE evaluations from the UI (Sprint 8).
 */

export default function SOEPage() {
  const { handleApiError } = useErrorHandler();
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [soeRun, setSoeRun] = useState<any>(null);

  // Form state
  const [industryProfile, setIndustryProfile] = useState<string>("space");
  const [hardwareClass, setHardwareClass] = useState<string>("flight");
  const [processes, setProcesses] = useState<string[]>(["SMT", "REFLOW"]);
  const [testsRequested, setTestsRequested] = useState<string[]>([]);
  const [materials, setMaterials] = useState<string[]>([]);
  const [bomRiskFlags, setBomRiskFlags] = useState<string[]>([]);
  const [additionalPacks, setAdditionalPacks] = useState<string>("");
  const [profileBundleId, setProfileBundleId] = useState<string>("");

  const handleLogin = async () => {
    try {
      const response = await apiClient.login("customer_001", "CUSTOMER");
      apiClient.setAuthToken(response.access_token);
      setAuthToken(response.access_token);
    } catch (err) {
      handleApiError(err);
    }
  };

  const handleRunSOE = async () => {
    if (!authToken) {
      handleLogin();
      return;
    }

    setLoading(true);
    setSoeRun(null);

    try {
      const inputs = {
        industry_profile: industryProfile,
        hardware_class: hardwareClass || undefined,
        inputs: {
          processes: processes.filter((p) => p.trim()),
          tests_requested: testsRequested.filter((t) => t.trim()),
          materials: materials.filter((m) => m.trim()),
          bom_risk_flags: bomRiskFlags.filter((f) => f.trim()),
        },
        additional_packs: additionalPacks
          ? additionalPacks.split(",").map((p) => p.trim()).filter(Boolean)
          : undefined,
        profile_bundle_id: profileBundleId || undefined,
      };

      const result = await apiClient.evaluateSOE(inputs);
      setSoeRun(result);
    } catch (err) {
      handleApiError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1200, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <h1>SOE Evaluation</h1>
        {!authToken ? (
          <button
            onClick={handleLogin}
            style={{
              padding: "8px 16px",
              backgroundColor: "#0070f3",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
            }}
          >
            Login
          </button>
        ) : (
          <div style={{ color: "green", fontSize: 14 }}>✓ Authenticated</div>
        )}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "400px 1fr", gap: 24 }}>
        {/* Input Form */}
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>SOE Inputs</h2>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Industry Profile *
            </label>
            <select
              value={industryProfile}
              onChange={(e) => setIndustryProfile(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            >
              <option value="space">Space</option>
              <option value="aerospace">Aerospace</option>
              <option value="medical">Medical</option>
              <option value="automotive">Automotive</option>
              <option value="industrial">Industrial</option>
            </select>
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Hardware Class
            </label>
            <input
              type="text"
              value={hardwareClass}
              onChange={(e) => setHardwareClass(e.target.value)}
              placeholder="e.g., flight, class_2, generic"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Processes (comma-separated)
            </label>
            <input
              type="text"
              value={processes.join(", ")}
              onChange={(e) => setProcesses(e.target.value.split(",").map((p) => p.trim()))}
              placeholder="SMT, REFLOW, CONFORMAL_COAT"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Tests Requested (comma-separated)
            </label>
            <input
              type="text"
              value={testsRequested.join(", ")}
              onChange={(e) => setTestsRequested(e.target.value.split(",").map((t) => t.trim()))}
              placeholder="FUNCTIONAL, X_RAY"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Materials (comma-separated)
            </label>
            <input
              type="text"
              value={materials.join(", ")}
              onChange={(e) => setMaterials(e.target.value.split(",").map((m) => m.trim()))}
              placeholder="EPOXY_3M_SCOTCHWELD_2216"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              BOM Risk Flags (comma-separated)
            </label>
            <input
              type="text"
              value={bomRiskFlags.join(", ")}
              onChange={(e) => setBomRiskFlags(e.target.value.split(",").map((f) => f.trim()))}
              placeholder="LONG_LEAD_EEE, SINGLE_SOURCE"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Additional Packs (comma-separated, optional)
            </label>
            <input
              type="text"
              value={additionalPacks}
              onChange={(e) => setAdditionalPacks(e.target.value)}
              placeholder="PACK_ID_1, PACK_ID_2"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <div style={{ marginTop: 16 }}>
            <label style={{ display: "block", marginBottom: 8, fontWeight: "500" }}>
              Profile Bundle ID (optional)
            </label>
            <input
              type="text"
              value={profileBundleId}
              onChange={(e) => setProfileBundleId(e.target.value)}
              placeholder="bundle_id"
              style={{
                width: "100%",
                padding: "8px 12px",
                border: "1px solid #ddd",
                borderRadius: 4,
              }}
            />
          </div>

          <button
            onClick={handleRunSOE}
            disabled={loading || !industryProfile}
            style={{
              marginTop: 24,
              width: "100%",
              padding: "12px 24px",
              backgroundColor: loading || !industryProfile ? "#ccc" : "#0070f3",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: loading || !industryProfile ? "not-allowed" : "pointer",
              fontWeight: "bold",
            }}
          >
            {loading ? "Running SOE..." : "Run SOE Evaluation"}
          </button>
        </section>

        {/* Results Viewer */}
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
          <h2>SOE Results</h2>

          {!soeRun ? (
            <div style={{ marginTop: 32, padding: 48, textAlign: "center", color: "#666" }}>
              <p>Run an SOE evaluation to see results</p>
            </div>
          ) : (
            <div style={{ marginTop: 16 }}>
              {/* Summary */}
              <div style={{ marginBottom: 24, padding: 16, backgroundColor: "#f0f9ff", borderRadius: 4 }}>
                <div style={{ fontWeight: "bold", marginBottom: 8 }}>Evaluation Summary</div>
                <div style={{ fontSize: 14 }}>
                  <div>Industry: <strong>{soeRun.industry_profile}</strong></div>
                  <div>Hardware Class: <strong>{soeRun.hardware_class || "generic"}</strong></div>
                  <div>Active Packs: <strong>{soeRun.active_packs?.length || 0}</strong></div>
                  <div>Decisions: <strong>{soeRun.decisions?.length || 0}</strong></div>
                </div>
              </div>

              {/* Active Packs */}
              {soeRun.active_packs && soeRun.active_packs.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 16, marginBottom: 8 }}>Active Standards Packs</h3>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {soeRun.active_packs.map((pack: string, idx: number) => (
                      <span
                        key={idx}
                        style={{
                          padding: "4px 8px",
                          backgroundColor: "#e0f2fe",
                          border: "1px solid #0284c7",
                          borderRadius: 4,
                          fontSize: 12,
                        }}
                      >
                        {pack}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Decisions */}
              {soeRun.decisions && soeRun.decisions.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 16, marginBottom: 8 }}>SOE Decisions ({soeRun.decisions.length})</h3>
                  <div style={{ maxHeight: 400, overflowY: "auto" }}>
                    {soeRun.decisions.map((decision: any, idx: number) => (
                      <div
                        key={idx}
                        style={{
                          marginBottom: 12,
                          padding: 12,
                          border: "1px solid #ddd",
                          borderRadius: 4,
                          backgroundColor: "#fff",
                        }}
                      >
                        <div style={{ fontWeight: "bold", marginBottom: 4 }}>
                          {decision.action} - {decision.object_type} ({decision.object_id})
                        </div>
                        <div style={{ fontSize: 12, color: "#666", marginBottom: 4 }}>
                          Decision ID: {decision.id}
                        </div>
                        {decision.why && (
                          <div style={{ fontSize: 12, color: "#666" }}>
                            Rule: {decision.why.rule_id} (Pack: {decision.why.pack_id})
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Gates */}
              {soeRun.gates && soeRun.gates.length > 0 && (
                <div style={{ marginBottom: 24 }}>
                  <h3 style={{ fontSize: 16, marginBottom: 8 }}>Release Gates</h3>
                  {soeRun.gates.map((gate: any, idx: number) => (
                    <div
                      key={idx}
                      style={{
                        padding: 12,
                        border: `1px solid ${gate.status === "blocked" ? "#fcc" : "#0c0"}`,
                        borderRadius: 4,
                        backgroundColor: gate.status === "blocked" ? "#fffbf0" : "#f0fff0",
                      }}
                    >
                      <div style={{ fontWeight: "bold" }}>
                        {gate.gate_id}: {gate.status.toUpperCase()}
                      </div>
                      {gate.blocked_by && gate.blocked_by.length > 0 && (
                        <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                          Blocked by: {gate.blocked_by.join(", ")}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
