import { useState } from "react";

const PRESETS = [
  "ERP server is completely down",
  "Brute force attack succeeded - admin portal compromised",
  "Payment gateway is offline",
  "Database server crashed",
  "Ransomware detected and spreading across network",
];

export default function BlastRadius({ role, api }) {
  const [incident, setIncident] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  const analyze = async (inc) => {
    const i = inc || incident.trim();
    if (!i || loading) return;
    setIncident(i);
    setLoading(true);
    setAnalysis(null);
    try {
      const res = await fetch(`${api}/blast-radius`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ incident: i, role })
      });
      const data = await res.json();
      setAnalysis(data);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: 28, maxWidth: 860 }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: "#2a5070", letterSpacing: 3, marginBottom: 6 }}>INCIDENT IMPACT ANALYZER</div>
        <h2 style={{ color: "#ff6644", fontSize: 20, margin: 0 }}>💥 Blast Radius Calculator</h2>
        <p style={{ color: "#4a6080", fontSize: 13, marginTop: 6 }}>
          Describe an incident and AI will map every downstream business impact — automatically.
        </p>
      </div>

      {/* Preset Incidents */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 11, color: "#2a5070", letterSpacing: 2, marginBottom: 8 }}>SIMULATE AN INCIDENT</div>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {PRESETS.map((p, i) => (
            <button key={i} onClick={() => analyze(p)} style={{
              background: "rgba(255,100,68,0.06)", border: "1px solid rgba(255,100,68,0.2)",
              color: "#ff8866", padding: "6px 12px", borderRadius: 20,
              cursor: "pointer", fontSize: 12, fontFamily: "'Courier New', monospace"
            }}>
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Input */}
      <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <input
          value={incident}
          onChange={e => setIncident(e.target.value)}
          onKeyDown={e => e.key === "Enter" && analyze()}
          placeholder="Or type a custom incident..."
          style={{
            flex: 1, background: "rgba(255,100,68,0.04)",
            border: "1px solid rgba(255,100,68,0.2)", borderRadius: 6,
            padding: "10px 16px", color: "#c8ddf0", fontSize: 13,
            fontFamily: "'Courier New', monospace", outline: "none"
          }}
        />
        <button onClick={() => analyze()} disabled={loading || !incident.trim()} style={{
          padding: "10px 20px", background: "rgba(255,100,68,0.12)",
          border: "1px solid rgba(255,100,68,0.3)", color: "#ff6644",
          borderRadius: 6, cursor: "pointer", fontSize: 13,
          fontFamily: "'Courier New', monospace"
        }}>
          ANALYZE →
        </button>
      </div>

      {/* Results */}
      {loading && (
        <div style={{
          background: "rgba(255,100,68,0.04)", border: "1px solid rgba(255,100,68,0.15)",
          borderRadius: 10, padding: 40, textAlign: "center"
        }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>💥</div>
          <div style={{ color: "#ff8866", fontSize: 13, letterSpacing: 2 }}>CALCULATING BLAST RADIUS...</div>
          <div style={{ color: "#4a3030", fontSize: 11, marginTop: 8 }}>Tracing downstream business impact chains</div>
        </div>
      )}

      {analysis && !loading && (
        <div style={{
          background: "rgba(255,100,68,0.04)", border: "1px solid rgba(255,100,68,0.2)",
          borderRadius: 10, padding: 28
        }}>
          <div style={{
            color: "#e8c8c0", fontSize: 13, lineHeight: 2,
            whiteSpace: "pre-wrap", fontFamily: "'Courier New', monospace"
          }}>
            {analysis.analysis}
          </div>
          <div style={{
            marginTop: 20, paddingTop: 16, borderTop: "1px solid rgba(255,100,68,0.15)",
            fontSize: 11, color: "#4a3030"
          }}>
            Analysis generated at {new Date(analysis.timestamp).toLocaleTimeString()} • Logged to audit trail
          </div>
        </div>
      )}

      {!analysis && !loading && (
        <div style={{
          background: "rgba(0,0,0,0.2)", border: "1px dashed rgba(255,100,68,0.15)",
          borderRadius: 10, padding: 40, textAlign: "center", color: "#2a4050"
        }}>
          Select a preset incident above or type your own to see the full blast radius analysis
        </div>
      )}
    </div>
  );
}