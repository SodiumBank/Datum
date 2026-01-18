"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";

const API_BASE = "http://localhost:8000";

function QuoteContent() {
  const searchParams = useSearchParams();
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const gerberUploadId = searchParams.get("gerber_upload_id");
  const bomUploadId = searchParams.get("bom_upload_id");
  const quantity = parseInt(searchParams.get("quantity") || "1");

  useEffect(() => {
    // Auto-login
    handleLogin();
  }, []);

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: "customer_001", role: "CUSTOMER" }),
      });
      if (response.ok) {
        const data = await response.json();
        setAuthToken(data.access_token);
      }
    } catch (err) {
      console.error("Login error:", err);
    }
  };

  const fetchQuote = async () => {
    if (!gerberUploadId || !authToken) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/quotes/estimate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          gerber_upload_id: gerberUploadId,
          bom_upload_id: bomUploadId,
          quantity: quantity,
          assumptions: { assembly_sides: ["TOP"] },
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setQuote(data);
      } else {
        const errorData = await response.json();
        setError(`Quote generation failed: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      setError(`Error: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (authToken && gerberUploadId) {
      fetchQuote();
    }
  }, [authToken, gerberUploadId]);

  if (!gerberUploadId) {
    return (
      <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui" }}>
        <h1>Quote View</h1>
        <p>Missing gerber_upload_id parameter</p>
        <a href="/" style={{ color: "#0070f3", textDecoration: "underline" }}>
          Go to Upload Page
        </a>
      </main>
    );
  }

  const costBreakdown = quote?.cost_breakdown;
  const riskFactors = quote?.risk_factors || [];

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1000, margin: "0 auto" }}>
      <h1>Datum Quote</h1>

      {error && (
        <div
          style={{
            marginTop: 16,
            padding: 12,
            backgroundColor: "#fee",
            border: "1px solid #fcc",
            borderRadius: 4,
            color: "#c00",
          }}
        >
          {error}
        </div>
      )}

      {loading && (
        <div style={{ marginTop: 16, padding: 12 }}>
          Generating quote...
        </div>
      )}

      {quote && (
        <div style={{ marginTop: 24 }}>
          {/* Quote Header */}
          <section style={{ padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ margin: 0 }}>Quote Summary</h2>
                <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
                  Quote ID: <code>{quote.id}</code>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 32, fontWeight: "bold", color: "#0070f3" }}>
                  ${costBreakdown?.total?.toFixed(2) || "0.00"}
                </div>
                <div style={{ fontSize: 14, color: "#666" }}>
                  {costBreakdown?.currency || "USD"}
                </div>
              </div>
            </div>
            <div style={{ marginTop: 16, fontSize: 14 }}>
              <div>Quantity: {quote.quantity || 1} units</div>
              <div>Lead Time: {quote.lead_time_days || 0} days</div>
              <div>Status: <strong>{quote.status}</strong></div>
            </div>
          </section>

          {/* Cost Breakdown */}
          <section style={{ marginTop: 24, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
            <h2>Cost Breakdown</h2>
            <table style={{ width: "100%", marginTop: 16, borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid #ddd" }}>
                  <th style={{ textAlign: "left", padding: "8px 0" }}>Line Item</th>
                  <th style={{ textAlign: "right", padding: "8px 0" }}>Amount</th>
                </tr>
              </thead>
              <tbody>
                {costBreakdown?.lines?.map((line: any, idx: number) => (
                  <tr key={idx} style={{ borderBottom: "1px solid #eee" }}>
                    <td style={{ padding: "8px 0" }}>
                      <div style={{ fontWeight: "500" }}>{line.label}</div>
                      {line.notes && (
                        <div style={{ fontSize: 12, color: "#666", marginTop: 2 }}>
                          {line.notes}
                        </div>
                      )}
                    </td>
                    <td style={{ textAlign: "right", padding: "8px 0", fontWeight: "500" }}>
                      ${line.amount.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: "2px solid #ddd", fontWeight: "bold" }}>
                  <td style={{ padding: "12px 0" }}>Total</td>
                  <td style={{ textAlign: "right", padding: "12px 0" }}>
                    ${costBreakdown?.total?.toFixed(2) || "0.00"}
                  </td>
                </tr>
              </tfoot>
            </table>
          </section>

          {/* Risk Factors */}
          {riskFactors.length > 0 && (
            <section style={{ marginTop: 24, padding: 16, border: "1px solid #ffa500", borderRadius: 8, backgroundColor: "#fffbf0" }}>
              <h2 style={{ color: "#d97706" }}>Risk Factors</h2>
              <div style={{ marginTop: 16 }}>
                {riskFactors.map((risk: any, idx: number) => (
                  <div
                    key={idx}
                    style={{
                      marginTop: idx > 0 ? 12 : 0,
                      padding: 12,
                      backgroundColor: "white",
                      border: "1px solid #ffa500",
                      borderRadius: 4,
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                      <div>
                        <div style={{ fontWeight: "bold", color: risk.severity === "HIGH" ? "#c00" : "#d97706" }}>
                          {risk.code} ({risk.severity})
                        </div>
                        <div style={{ marginTop: 4 }}>{risk.summary}</div>
                        {risk.details && (
                          <div style={{ marginTop: 4, fontSize: 14, color: "#666" }}>{risk.details}</div>
                        )}
                      </div>
                    </div>
                    {risk.impacts && (
                      <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
                        {risk.impacts.cost_delta && (
                          <div>Cost Impact: ${risk.impacts.cost_delta.toFixed(2)}</div>
                        )}
                        {risk.impacts.lead_time_delta_days && (
                          <div>Lead Time Impact: +{risk.impacts.lead_time_delta_days} days</div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Assumptions */}
          {quote.assumptions && Object.keys(quote.assumptions).length > 0 && (
            <section style={{ marginTop: 24, padding: 16, border: "1px solid #ddd", borderRadius: 8, backgroundColor: "#f9fafb" }}>
              <h2>Assumptions</h2>
              <div style={{ marginTop: 16, fontSize: 14 }}>
                {Object.entries(quote.assumptions).map(([key, value]) => (
                  <div key={key} style={{ marginTop: 4 }}>
                    <strong>{key}:</strong> {Array.isArray(value) ? value.join(", ") : String(value)}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Actions */}
          <section style={{ marginTop: 24 }}>
            <a
              href="/"
              style={{
                display: "inline-block",
                padding: "12px 24px",
                backgroundColor: "#0070f3",
                color: "white",
                textDecoration: "none",
                borderRadius: 4,
              }}
            >
              Create New Quote
            </a>
          </section>
        </div>
      )}
    </main>
  );
}

export default function QuotePage() {
  return (
    <Suspense fallback={<div style={{ padding: 24 }}>Loading...</div>}>
      <QuoteContent />
    </Suspense>
  );
}
