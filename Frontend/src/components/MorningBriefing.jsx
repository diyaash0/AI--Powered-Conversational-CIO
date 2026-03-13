import { useState, useEffect } from "react";

export default function MorningBriefing({ role, api }) {
  const [briefing, setBriefing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState(false);

  useEffect(() => {
    if (!fetched) fetchBriefing();
  }, []);

  const fetchBriefing = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${api}/morning-briefing/${role}`);
      const data = await res.json();
      setBriefing(data);
      setFetched(true);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const now = new Date();
  const timeStr = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  const dateStr = now.toLocaleDateString("en-IN", { weekday: "long", year: "numeric", month: "long", day: "numeric" });

  return (
    <div style={{ padding: 32, maxWidth: 820 }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 11, color: "#2a5070", letterSpacing: 3, marginBottom: 6 }}>
          DAILY INTELLIGENCE BRIEFING
        </div>
        <h2 style={{ color: "#00d4ff", fontSize: 22, margin: 0 }}>Good Morning, {role.replace("_", " ")}</h2>
        <div style={{ color: "#4a6080", fontSize: 13, marginTop: 4 }}>
          {dateStr} • {timeStr} IST
        </div>
      </div>

      {/* Briefing Box */}
      <div style={{
        background: "rgba(0,212,255,0.04)",
        border: "1px solid rgba(0,212,255,0.15)",
        borderRadius: 10, padding: 28, minHeight: 300,
        position: "relative"
      }}>
        {loading && (
          <div style={{ textAlign: "center", paddingTop: 60 }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>☀️</div>
            <div style={{ color: "#4a6080", fontSize: 13, letterSpacing: 2 }}>
              GENERATING YOUR BRIEFING...
            </div>
            <div style={{ color: "#2a4060", fontSize: 11, marginTop: 8 }}>
              Scanning all enterprise systems
            </div>
          </div>
        )}

        {!loading && briefing && (
          <>
            <div style={{
              color: "#c8ddf0", fontSize: 14, lineHeight: 1.9,
              whiteSpace: "pre-wrap", fontFamily: "'Courier New', monospace"
            }}>
              {briefing.briefing}
            </div>

            <div style={{
              marginTop: 24, paddingTop: 16,
              borderTop: "1px solid rgba(0,212,255,0.1)",
              display: "flex", gap: 24, fontSize: 12
            }}>
              <span style={{ color: "#ff4444" }}>
                🚨 {briefing.anomaly_count} Anomalies Detected
              </span>
              <span style={{ color: "#4a6080" }}>
                Auto-generated at {new Date(briefing.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </>
        )}

        {!loading && !briefing && (
          <div style={{ textAlign: "center", paddingTop: 60, color: "#4a6080" }}>
            Click refresh to generate your briefing
          </div>
        )}
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchBriefing}
        disabled={loading}
        style={{
          marginTop: 16, padding: "10px 24px",
          background: loading ? "rgba(0,212,255,0.05)" : "rgba(0,212,255,0.1)",
          border: "1px solid rgba(0,212,255,0.3)",
          color: loading ? "#2a5070" : "#00d4ff",
          borderRadius: 6, cursor: loading ? "default" : "pointer",
          fontSize: 12, letterSpacing: 2,
          fontFamily: "'Courier New', monospace"
        }}
      >
        {loading ? "GENERATING..." : "🔄 REFRESH BRIEFING"}
      </button>

      <p style={{ color: "#1a3050", fontSize: 11, marginTop: 12 }}>
        Briefing auto-generates on login. Refresh to get latest intelligence.
      </p>
    </div>
  );
}