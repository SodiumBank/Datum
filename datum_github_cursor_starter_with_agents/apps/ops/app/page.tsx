"use client";

import { useState, useEffect } from "react";

const API_BASE = "http://localhost:8000";

export default function OpsConsolePage() {
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [selectedQuote, setSelectedQuote] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lockReason, setLockReason] = useState("");

  useEffect(() => {
    handleLogin();
  }, []);

  useEffect(() => {
    if (authToken) {
      fetchQuotes();
    }
  }, [authToken]);

  const handleLogin = async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
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
  };

  const fetchQuotes = async () => {
    if (!authToken) return;

    setLoading(true);
    try {
      // Get quotes needing review (status = ESTIMATED)
      const response = await fetch(`${API_BASE}/quotes?status=ESTIMATED`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (response.ok) {
        const data = await response.json();
        setQuotes(data.quotes || []);
      }
    } catch (err) {
      setError(`Error fetching quotes: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchQuoteDetails = async (quoteId: string) => {
    if (!authToken) return;

    try {
      const response = await fetch(`${API_BASE}/quotes/${quoteId}`, {
        headers: { Authorization: `Bearer ${authToken}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedQuote(data);
      }
    } catch (err) {
      setError(`Error fetching quote: ${err}`);
    }
  };

  const handleLockQuote = async (quoteId: string) => {
    if (!authToken || !lockReason.trim()) {
      setError("Lock reason required");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/quotes/${quoteId}/lock`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          lock_reason: lockReason,
          requires_contract: false,
        }),
      });

      if (response.ok) {
        setLockReason("");
        setSelectedQuote(null);
        fetchQuotes(); // Refresh list
      } else {
        const errorData = await response.json();
        setError(`Lock failed: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      setError(`Error locking quote: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const costBreakdown = selectedQuote?.cost_breakdown;
  const riskFactors = selectedQuote?.risk_factors || [];

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 1400, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 32 }}>
        <h1>Datum — Ops Console</h1>
        {authToken && (
          <div style={{ color: "green", fontSize: 14 }}>✓ Authenticated as OPS</div>
        )}
      </div>

      {error && (
        <div
          style={{
            padding: 12,
            backgroundColor: "#fee",
            border: "1px solid #fcc",
            borderRadius: 4,
            color: "#c00",
            marginBottom: 16,
          }}
        >
          {error}
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "400px 1fr", gap: 24 }}>
        {/* Quotes Queue */}
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 16 }}>
          <h2>Queue</h2>
          <div style={{ marginTop: 16, fontSize: 14, color: "#666" }}>
            {quotes.length} quote(s) needing review
          </div>
          {loading && <div style={{ marginTop: 16 }}>Loading...</div>}
          {!loading && quotes.length === 0 && (
            <div style={{ marginTop: 16, padding: 16, color: "#666", fontStyle: "italic" }}>
              No quotes pending review
            </div>
          )}
          <div style={{ marginTop: 16 }}>
            {quotes.map((quote) => (
              <div
                key={quote.id}
                onClick={() => fetchQuoteDetails(quote.id)}
                style={{
                  padding: 12,
                  marginBottom: 8,
                  border: "1px solid #ddd",
                  borderRadius: 4,
                  cursor: "pointer",
                  backgroundColor: selectedQuote?.id === quote.id ? "#f0f9ff" : "white",
                  borderColor: selectedQuote?.id === quote.id ? "#0070f3" : "#ddd",
                }}
              >
                <div style={{ fontWeight: "bold", fontSize: 14 }}>{quote.id}</div>
                <div style={{ fontSize: 12, color: "#666", marginTop: 4 }}>
                  ${quote.cost_breakdown?.total?.toFixed(2) || "0.00"} • {quote.lead_time_days || 0} days
                </div>
                <div style={{ fontSize: 11, color: "#999", marginTop: 4 }}>
                  {quote.status} • {quote.risk_factors?.length || 0} risks
                </div>
              </div>
            ))}
          </div>
          <button
            onClick={fetchQuotes}
            style={{
              marginTop: 16,
              padding: "8px 16px",
              backgroundColor: "#0070f3",
              color: "white",
              border: "none",
              borderRadius: 4,
              cursor: "pointer",
              width: "100%",
            }}
          >
            Refresh
          </button>
        </section>

        {/* Quote Review */}
        <section>
          {selectedQuote ? (
            <div>
              <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 24 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 24 }}>
                  <div>
                    <h2 style={{ margin: 0 }}>Quote Review</h2>
                    <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
                      Quote ID: <code>{selectedQuote.id}</code>
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

                {/* Quote Details */}
                <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                  <div>
                    <strong>Quantity:</strong> {selectedQuote.quantity || 1} units
                  </div>
                  <div>
                    <strong>Lead Time:</strong> {selectedQuote.lead_time_days || 0} days
                  </div>
                  <div>
                    <strong>Status:</strong> <span style={{ fontWeight: "bold" }}>{selectedQuote.status}</span>
                  </div>
                  <div>
                    <strong>Tier:</strong> {selectedQuote.tier}
                  </div>
                </div>

                {/* Cost Breakdown */}
                <div style={{ marginTop: 24 }}>
                  <h3>Cost Breakdown</h3>
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
                          <td style={{ textAlign: "right", padding: "8px 0" }}>
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
                </div>

                {/* Risk Factors */}
                {riskFactors.length > 0 && (
                  <div style={{ marginTop: 24 }}>
                    <h3 style={{ color: "#d97706" }}>Risk Factors</h3>
                    <div style={{ marginTop: 16 }}>
                      {riskFactors.map((risk: any, idx: number) => (
                        <div
                          key={idx}
                          style={{
                            marginTop: idx > 0 ? 12 : 0,
                            padding: 12,
                            backgroundColor: "#fffbf0",
                            border: "1px solid #ffa500",
                            borderRadius: 4,
                          }}
                        >
                          <div style={{ fontWeight: "bold", color: risk.severity === "HIGH" ? "#c00" : "#d97706" }}>
                            {risk.code} ({risk.severity})
                          </div>
                          <div style={{ marginTop: 4 }}>{risk.summary}</div>
                          {risk.details && (
                            <div style={{ marginTop: 4, fontSize: 14, color: "#666" }}>{risk.details}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Lock Quote */}
                {selectedQuote.status !== "LOCKED" && (
                  <div style={{ marginTop: 32, padding: 16, border: "1px solid #0070f3", borderRadius: 8, backgroundColor: "#f0f9ff" }}>
                    <h3>Approve & Lock Quote</h3>
                    <p style={{ fontSize: 14, color: "#666" }}>
                      Locking this quote makes it immutable. A new revision must be created for any changes.
                    </p>
                    <textarea
                      value={lockReason}
                      onChange={(e) => setLockReason(e.target.value)}
                      placeholder="Enter lock reason (required)"
                      style={{
                        width: "100%",
                        minHeight: 80,
                        padding: 8,
                        marginTop: 12,
                        border: "1px solid #ddd",
                        borderRadius: 4,
                        fontFamily: "inherit",
                      }}
                    />
                    <button
                      onClick={() => handleLockQuote(selectedQuote.id)}
                      disabled={!lockReason.trim() || loading}
                      style={{
                        marginTop: 12,
                        padding: "12px 24px",
                        backgroundColor: lockReason.trim() && !loading ? "#0070f3" : "#ccc",
                        color: "white",
                        border: "none",
                        borderRadius: 4,
                        cursor: lockReason.trim() && !loading ? "pointer" : "not-allowed",
                        fontWeight: "bold",
                      }}
                    >
                      {loading ? "Locking..." : "Approve & Lock Quote"}
                    </button>
                  </div>
                )}

                {selectedQuote.status === "LOCKED" && (
                  <div style={{ marginTop: 32, padding: 16, border: "1px solid #0a0", borderRadius: 8, backgroundColor: "#f0fff0" }}>
                    <div style={{ fontWeight: "bold", color: "#0a0" }}>✓ Quote Locked</div>
                    <div style={{ marginTop: 8, fontSize: 14 }}>
                      This quote is immutable. Create a new revision for changes.
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ border: "1px solid #ddd", borderRadius: 8, padding: 48, textAlign: "center", color: "#666" }}>
              <p>Select a quote from the queue to review</p>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
