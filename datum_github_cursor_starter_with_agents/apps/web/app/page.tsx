"use client";

import { useState } from "react";

const API_BASE = "http://localhost:8000";

export default function Page() {
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [gerberFile, setGerberFile] = useState<File | null>(null);
  const [bomFile, setBomFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [gerberUpload, setGerberUpload] = useState<any>(null);
  const [bomUpload, setBomUpload] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

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
        setError(null);
      } else {
        setError("Login failed");
      }
    } catch (err) {
      setError(`Login error: ${err}`);
    }
  };

  const handleGerberUpload = async () => {
    if (!gerberFile || !authToken) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", gerberFile);

      const response = await fetch(`${API_BASE}/uploads/gerbers`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setGerberUpload(data);
      } else {
        const errorData = await response.json();
        setError(`Gerber upload failed: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      setError(`Upload error: ${err}`);
    } finally {
      setUploading(false);
    }
  };

  const handleBomUpload = async () => {
    if (!bomFile || !authToken) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append("file", bomFile);

      const response = await fetch(`${API_BASE}/uploads/bom`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${authToken}`,
        },
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        setBomUpload(data);
      } else {
        const errorData = await response.json();
        setError(`BOM upload failed: ${errorData.detail || response.statusText}`);
      }
    } catch (err) {
      setError(`Upload error: ${err}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <main style={{ padding: 24, fontFamily: "ui-sans-serif, system-ui", maxWidth: 800, margin: "0 auto" }}>
      <h1>Datum — Manufacturing Decision System</h1>
      <p>Upload your Gerber files and BOM to get a deterministic quote.</p>

      {/* Login */}
      <section style={{ marginTop: 32, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
        <h2>Authentication</h2>
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
            Login as Customer
          </button>
        ) : (
          <div style={{ color: "green" }}>
            ✓ Authenticated as Customer
          </div>
        )}
      </section>

      {/* Error Display */}
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

      {/* Gerber Upload */}
      <section style={{ marginTop: 32, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
        <h2>1. Upload Gerber Files (ZIP)</h2>
        <div style={{ marginTop: 16 }}>
          <input
            type="file"
            accept=".zip"
            onChange={(e) => setGerberFile(e.target.files?.[0] || null)}
            disabled={!authToken || uploading}
          />
        </div>
        {gerberFile && (
          <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
            Selected: {gerberFile.name} ({(gerberFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
        <button
          onClick={handleGerberUpload}
          disabled={!gerberFile || !authToken || uploading}
          style={{
            marginTop: 16,
            padding: "8px 16px",
            backgroundColor: gerberFile && authToken && !uploading ? "#0070f3" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: 4,
            cursor: gerberFile && authToken && !uploading ? "pointer" : "not-allowed",
          }}
        >
          {uploading ? "Uploading..." : "Upload Gerber ZIP"}
        </button>

        {gerberUpload && (
          <div style={{ marginTop: 16, padding: 12, backgroundColor: "#f0f9ff", borderRadius: 4 }}>
            <div style={{ fontWeight: "bold" }}>✓ Gerber Upload Successful</div>
            <div style={{ marginTop: 8, fontSize: 14 }}>
              <div>Upload ID: <code>{gerberUpload.upload_id}</code></div>
              <div>SHA256: <code style={{ fontSize: 12 }}>{gerberUpload.sha256}</code></div>
              <div>Files: {gerberUpload.files?.length || 0} files extracted</div>
            </div>
          </div>
        )}
      </section>

      {/* BOM Upload */}
      <section style={{ marginTop: 32, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
        <h2>2. Upload BOM (CSV or XLSX)</h2>
        <div style={{ marginTop: 16 }}>
          <input
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={(e) => setBomFile(e.target.files?.[0] || null)}
            disabled={!authToken || uploading}
          />
        </div>
        {bomFile && (
          <div style={{ marginTop: 8, fontSize: 14, color: "#666" }}>
            Selected: {bomFile.name} ({(bomFile.size / 1024).toFixed(1)} KB)
          </div>
        )}
        <button
          onClick={handleBomUpload}
          disabled={!bomFile || !authToken || uploading}
          style={{
            marginTop: 16,
            padding: "8px 16px",
            backgroundColor: bomFile && authToken && !uploading ? "#0070f3" : "#ccc",
            color: "white",
            border: "none",
            borderRadius: 4,
            cursor: bomFile && authToken && !uploading ? "pointer" : "not-allowed",
          }}
        >
          {uploading ? "Uploading..." : "Upload BOM"}
        </button>

        {bomUpload && (
          <div style={{ marginTop: 16, padding: 12, backgroundColor: "#f0f9ff", borderRadius: 4 }}>
            <div style={{ fontWeight: "bold" }}>✓ BOM Upload Successful</div>
            <div style={{ marginTop: 8, fontSize: 14 }}>
              <div>Upload ID: <code>{bomUpload.upload_id}</code></div>
              <div>SHA256: <code style={{ fontSize: 12 }}>{bomUpload.sha256}</code></div>
              <div>Format: {bomUpload.format}</div>
              <div>Items: {bomUpload.items?.length || 0} parts normalized</div>
            </div>
          </div>
        )}
      </section>

      {/* Next Steps / Generate Quote */}
      {gerberUpload && (
        <section style={{ marginTop: 32, padding: 16, border: "1px solid #0070f3", borderRadius: 8 }}>
          <h2>3. Generate Quote</h2>
          <p>Uploads complete! Generate a quote with your files.</p>
          <div style={{ marginTop: 16, fontSize: 14, fontFamily: "monospace", backgroundColor: "#f5f5f5", padding: 12, borderRadius: 4 }}>
            <div>Gerber Upload ID: <strong>{gerberUpload.upload_id}</strong></div>
            {bomUpload && (
              <div style={{ marginTop: 8 }}>BOM Upload ID: <strong>{bomUpload.upload_id}</strong></div>
            )}
          </div>
          <div style={{ marginTop: 16 }}>
            <input
              type="number"
              placeholder="Quantity (default: 1)"
              min="1"
              defaultValue="1"
              id="quantity-input"
              style={{ padding: "8px 12px", borderRadius: 4, border: "1px solid #ddd", marginRight: 8 }}
            />
            <a
              href={`/quote?gerber_upload_id=${gerberUpload.upload_id}${bomUpload ? `&bom_upload_id=${bomUpload.upload_id}` : ""}&quantity=1`}
              onClick={(e) => {
                const qty = (document.getElementById("quantity-input") as HTMLInputElement)?.value || "1";
                const href = `/quote?gerber_upload_id=${gerberUpload.upload_id}${bomUpload ? `&bom_upload_id=${bomUpload.upload_id}` : ""}&quantity=${qty}`;
                (e.currentTarget as HTMLAnchorElement).href = href;
              }}
              style={{
                display: "inline-block",
                padding: "12px 24px",
                backgroundColor: "#0070f3",
                color: "white",
                textDecoration: "none",
                borderRadius: 4,
                marginTop: 8,
              }}
            >
              Generate Quote
            </a>
          </div>
        </section>
      )}
    </main>
  );
}
