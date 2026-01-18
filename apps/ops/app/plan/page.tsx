"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

/**
 * Ops UI: DatumPlan Viewer & Editor (Sprint 3: Editable with SOE Locks)
 * 
 * SPRINT 3: Plans can be edited, but SOE-derived fields are locked.
 * Edits create new versions. Approval workflow required for exports.
 */

interface PlanStep {
  step_id: string;
  type: string;
  title: string;
  sequence: number;
  required: boolean;
  locked_sequence: boolean;
  soe_decision_id?: string;
  soe_why?: {
    rule_id: string;
    pack_id: string;
    citations: string[];
  };
}

interface Plan {
  id: string;
  quote_id: string;
  plan_revision: string;
  version: number;
  state: "draft" | "submitted" | "approved" | "rejected";
  locked: boolean;
  steps: PlanStep[];
  tests?: Array<{
    test_id: string;
    test_type: string;
    title: string;
    soe_decision_id?: string;
    soe_why?: {
      rule_id: string;
      pack_id: string;
      citations: string[];
    };
  }>;
  evidence_intent?: Array<{
    evidence_id: string;
    evidence_type: string;
    retention: string;
    soe_decision_id?: string;
    soe_why?: {
      rule_id: string;
      pack_id: string;
      citations: string[];
    };
  }>;
  soe_decision_ids?: string[];
  edit_metadata?: {
    edited_by: string;
    edited_at: string;
    edit_reason: string;
    overrides?: Array<{
      constraint: string;
      reason: string;
      user_id: string;
      timestamp: string;
    }>;
  };
}

export default function PlanViewer() {
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan_id");
  const quoteId = searchParams.get("quote_id");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editReason, setEditReason] = useState("");
  const [overrideReason, setOverrideReason] = useState("");
  const [allowOverrides, setAllowOverrides] = useState(false);
  const [authToken, setAuthToken] = useState<string | null>(null);

  useEffect(() => {
    async function handleLogin() {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        const response = await fetch(`${apiUrl}/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_id: "ops_001", role: "OPS" }),
        });
        if (response.ok) {
          const data = await response.json();
          setAuthToken(data.access_token);
        }
      } catch (err) {
        console.error("Login error:", err);
      }
    }
    handleLogin();
  }, []);

  useEffect(() => {
    async function fetchPlan() {
      if (!planId && !quoteId) {
        setError("Missing plan_id or quote_id");
        setLoading(false);
        return;
      }

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
        let url = `${apiUrl}/plans`;
        
        if (planId) {
          url += `/${planId}`;
        } else if (quoteId) {
          url += `/quote/${quoteId}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Failed to fetch plan: ${response.statusText}`);
        }

        const data = await response.json();
        setPlan(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch plan");
      } finally {
        setLoading(false);
      }
    }

    fetchPlan();
  }, [planId, quoteId]);

  const handleSubmitForApproval = async () => {
    if (!plan || !authToken) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/plans/${plan.id}/submit`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ reason: "Ready for approval" }),
      });

      if (response.ok) {
        const updated = await response.json();
        setPlan(updated);
        alert("Plan submitted for approval");
      } else {
        const error = await response.json();
        setError(error.detail || "Failed to submit plan");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit plan");
    }
  };

  const handleApprove = async () => {
    if (!plan || !authToken) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/plans/${plan.id}/approve`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ reason: "Plan approved" }),
      });

      if (response.ok) {
        const updated = await response.json();
        setPlan(updated);
        alert("Plan approved");
      } else {
        const error = await response.json();
        setError(error.detail || "Failed to approve plan");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve plan");
    }
  };

  const handleReject = async () => {
    if (!plan || !authToken) return;
    const reason = prompt("Enter rejection reason:");
    if (!reason) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/plans/${plan.id}/reject`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({ reason }),
      });

      if (response.ok) {
        const updated = await response.json();
        setPlan(updated);
        alert("Plan rejected");
      } else {
        const error = await response.json();
        setError(error.detail || "Failed to reject plan");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reject plan");
    }
  };

  const handleExport = async (format: "csv" | "json") => {
    if (!plan || !authToken) return;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/plans/${plan.id}/export/${format}`, {
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
      });

      if (response.ok) {
        if (format === "csv") {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `plan_${plan.id}_v${plan.version}.csv`;
          a.click();
        } else {
          const data = await response.json();
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `plan_${plan.id}_v${plan.version}.json`;
          a.click();
        }
      } else {
        const error = await response.json();
        setError(error.detail || `Failed to export ${format}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to export ${format}`);
    }
  };

  if (loading) {
    return <div className="p-8">Loading plan...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">Error: {error}</div>;
  }

  if (!plan) {
    return <div className="p-8">Plan not found</div>;
  }

  const canEdit = plan.state === "draft" && !plan.locked;
  const isSOELocked = (step: PlanStep) => step.soe_decision_id || step.locked_sequence;

  return (
    <div className="p-8">
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold mb-2">DatumPlan Viewer</h1>
            <p className="text-gray-600">
              Plan Revision: {plan.plan_revision} | Version: {plan.version} | Quote: {plan.quote_id}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className={`px-3 py-1 text-sm rounded ${
                plan.state === "draft" ? "bg-gray-200 text-gray-800" :
                plan.state === "submitted" ? "bg-yellow-200 text-yellow-800" :
                plan.state === "approved" ? "bg-green-200 text-green-800" :
                "bg-red-200 text-red-800"
              }`}>
                {plan.state.toUpperCase()}
              </span>
              {plan.locked && (
                <span className="px-3 py-1 text-sm bg-red-100 text-red-800 rounded">
                  LOCKED
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            {plan.state === "draft" && (
              <button
                onClick={() => setEditing(!editing)}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                disabled={plan.locked}
              >
                {editing ? "Cancel Edit" : "Edit Plan"}
              </button>
            )}
            {plan.state === "draft" && (
              <button
                onClick={handleSubmitForApproval}
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                disabled={plan.locked}
              >
                Submit for Approval
              </button>
            )}
            {plan.state === "submitted" && (
              <>
                <button
                  onClick={handleApprove}
                  className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                >
                  Approve
                </button>
                <button
                  onClick={handleReject}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                >
                  Reject
                </button>
              </>
            )}
            {plan.state === "approved" && (
              <>
                <button
                  onClick={() => handleExport("csv")}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Export CSV
                </button>
                <button
                  onClick={() => handleExport("json")}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Export JSON
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Edit Metadata */}
      {plan.edit_metadata && (
        <div className="mb-4 p-3 bg-gray-50 rounded border-l-4 border-gray-400">
          <p className="text-sm">
            <strong>Last edited:</strong> {new Date(plan.edit_metadata.edited_at).toLocaleString()} by {plan.edit_metadata.edited_by}
          </p>
          <p className="text-sm text-gray-600">Reason: {plan.edit_metadata.edit_reason}</p>
          {plan.edit_metadata.overrides && plan.edit_metadata.overrides.length > 0 && (
            <div className="mt-2">
              <p className="text-sm font-semibold text-orange-800">Overrides:</p>
              {plan.edit_metadata.overrides.map((override, idx) => (
                <div key={idx} className="text-xs text-orange-700 mt-1">
                  {override.constraint}: {override.reason}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Steps Section */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Manufacturing Steps</h2>
        <div className="space-y-3">
          {plan.steps.map((step) => {
            const isLocked = isSOELocked(step);
            return (
              <div
                key={step.step_id}
                className={`border rounded p-4 ${
                  isLocked ? "bg-yellow-50 border-yellow-300" : "bg-white"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-medium">{step.sequence}.</span>
                      <span className="font-semibold">{step.title}</span>
                      <span className="text-sm text-gray-500">({step.type})</span>
                      {step.required && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                          Required
                        </span>
                      )}
                      {isLocked && (
                        <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded font-semibold">
                          🔒 SOE LOCKED
                        </span>
                      )}
                      {step.locked_sequence && !step.soe_decision_id && (
                        <span className="px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded">
                          Sequence Locked
                        </span>
                      )}
                    </div>
                    {step.soe_why && (
                      <div className="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400">
                        <p className="text-sm font-medium text-yellow-800">
                          SOE Required: {step.soe_why.rule_id}
                        </p>
                        <p className="text-xs text-yellow-700 mt-1">
                          Citations: {step.soe_why.citations.join(", ")}
                        </p>
                        <p className="text-xs text-yellow-600 mt-1">
                          Decision ID: {step.soe_decision_id}
                        </p>
                        <p className="text-xs text-yellow-600 mt-1 font-semibold">
                          ⚠️ This step cannot be removed or reordered without override
                        </p>
                      </div>
                    )}
                    {editing && !isLocked && canEdit && (
                      <div className="mt-2 text-sm text-gray-600">
                        <span className="text-green-600">✓ Editable</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Tests Section */}
      {plan.tests && plan.tests.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Required Tests</h2>
          <div className="space-y-3">
            {plan.tests.map((test) => {
              const isLocked = test.soe_decision_id !== undefined;
              return (
                <div
                  key={test.test_id}
                  className={`border rounded p-4 ${
                    isLocked ? "bg-yellow-50 border-yellow-300" : "bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-semibold">{test.title}</div>
                      <div className="text-sm text-gray-600 mt-1">Type: {test.test_type}</div>
                      {isLocked && (
                        <span className="mt-2 inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded font-semibold">
                          🔒 SOE LOCKED
                        </span>
                      )}
                    </div>
                  </div>
                  {test.soe_why && (
                    <div className="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400">
                      <p className="text-sm font-medium text-yellow-800">
                        SOE Required: {test.soe_why.rule_id}
                      </p>
                      <p className="text-xs text-yellow-700 mt-1">
                        Citations: {test.soe_why.citations.join(", ")}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Evidence Intent Section */}
      {plan.evidence_intent && plan.evidence_intent.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Evidence Requirements</h2>
          <div className="space-y-3">
            {plan.evidence_intent.map((evidence) => {
              const isLocked = evidence.soe_decision_id !== undefined;
              return (
                <div
                  key={evidence.evidence_id}
                  className={`border rounded p-4 ${
                    isLocked ? "bg-yellow-50 border-yellow-300" : "bg-white"
                  }`}
                >
                  <div className="font-semibold">{evidence.evidence_type}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    Retention: {evidence.retention}
                  </div>
                  {isLocked && (
                    <span className="mt-2 inline-block px-2 py-1 text-xs bg-red-100 text-red-800 rounded font-semibold">
                      🔒 SOE LOCKED
                    </span>
                  )}
                  {evidence.soe_why && (
                    <div className="mt-2 p-2 bg-yellow-50 border-l-4 border-yellow-400">
                      <p className="text-sm font-medium text-yellow-800">
                        SOE Required: {evidence.soe_why.rule_id}
                      </p>
                      <p className="text-xs text-yellow-700 mt-1">
                        Citations: {evidence.soe_why.citations.join(", ")}
                      </p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* SOE References */}
      {plan.soe_decision_ids && plan.soe_decision_ids.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">SOE Decision References</h2>
          <div className="text-sm text-gray-600">
            This plan was generated from {plan.soe_decision_ids.length} SOE decisions.
          </div>
        </section>
      )}

      {/* Sprint 3 Notice */}
      <div className="mt-8 p-4 bg-blue-50 rounded border-l-4 border-blue-400">
        <p className="text-sm font-medium text-blue-800">
          Sprint 3: Editable & Governed Plans
        </p>
        <p className="text-xs text-blue-700 mt-1">
          Plans can be edited in draft state. SOE-locked fields (🔒) cannot be modified without override.
          Approved plans are immutable and can be exported.
        </p>
      </div>
    </div>
  );
}
