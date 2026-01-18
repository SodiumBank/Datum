"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";

/**
 * Ops UI: DatumPlan Viewer (Sprint 2: Read-Only)
 * 
 * SPRINT 2 GUARDRAIL: This component is read-only.
 * NO edit buttons, NO override options, NO mutations.
 * Plans are immutable in Sprint 2.
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
  steps: PlanStep[];
  tests?: Array<{
    test_id: string;
    test_type: string;
    title: string;
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
    soe_why?: {
      rule_id: string;
      pack_id: string;
      citations: string[];
    };
  }>;
  soe_decision_ids?: string[];
}

export default function PlanViewer() {
  const searchParams = useSearchParams();
  const planId = searchParams.get("plan_id");
  const quoteId = searchParams.get("quote_id");
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) {
    return <div className="p-8">Loading plan...</div>;
  }

  if (error) {
    return <div className="p-8 text-red-600">Error: {error}</div>;
  }

  if (!plan) {
    return <div className="p-8">Plan not found</div>;
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-2">DatumPlan Viewer</h1>
        <p className="text-gray-600">
          Plan Revision: {plan.plan_revision} | Quote: {plan.quote_id}
        </p>
        <p className="text-sm text-gray-500 mt-2">
          Sprint 2: Read-only view. Plans are immutable.
        </p>
      </div>

      {/* Steps Section */}
      <section className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Manufacturing Steps</h2>
        <div className="space-y-3">
          {plan.steps.map((step) => (
            <div
              key={step.step_id}
              className="border rounded p-4 bg-white"
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
                    {step.locked_sequence && (
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-800 rounded">
                        Locked
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
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Tests Section */}
      {plan.tests && plan.tests.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Required Tests</h2>
          <div className="space-y-3">
            {plan.tests.map((test) => (
              <div key={test.test_id} className="border rounded p-4 bg-white">
                <div className="font-semibold">{test.title}</div>
                <div className="text-sm text-gray-600 mt-1">Type: {test.test_type}</div>
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
            ))}
          </div>
        </section>
      )}

      {/* Evidence Intent Section */}
      {plan.evidence_intent && plan.evidence_intent.length > 0 && (
        <section className="mb-8">
          <h2 className="text-xl font-semibold mb-4">Evidence Requirements</h2>
          <div className="space-y-3">
            {plan.evidence_intent.map((evidence) => (
              <div key={evidence.evidence_id} className="border rounded p-4 bg-white">
                <div className="font-semibold">{evidence.evidence_type}</div>
                <div className="text-sm text-gray-600 mt-1">
                  Retention: {evidence.retention}
                </div>
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
            ))}
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

      {/* Sprint 2 Notice */}
      <div className="mt-8 p-4 bg-gray-100 rounded border-l-4 border-gray-400">
        <p className="text-sm font-medium text-gray-800">
          Sprint 2: Read-Only Intent Layer
        </p>
        <p className="text-xs text-gray-600 mt-1">
          This plan is immutable. No edits or overrides are allowed.
          Changes require creating a new revision (Sprint 3+).
        </p>
      </div>
    </div>
  );
}
