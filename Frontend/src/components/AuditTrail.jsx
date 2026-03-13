import { useState, useEffect } from "react";

const ACTION_COLOR = {
  MORNING_BRIEFING: "#00d4ff",
  CHAT_QUERY: "#00ff88",
  BLAST_RADIUS: "#ff6644",
};

const ACTION_ICON = {
  MORNING_BRIEFING: "☀️",
  CHAT_QUERY: "💬",
  BLAST_RADIUS: "💥",
};

export default function AuditTrail({ api }) {
  const [trail, setTrail] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrail();
    const interval = setInterval(fetchTrail, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchTrail = async () => {
    try {
      const res = await fetch(`${api}/audit-trail`);
      const data = await res.json();
      setTrail(data.trail);
    } catch (e) { console.error(e); }
    setLoading(false);
  };

  return (
    <div style={{ padding: 28, maxWidth: 900 }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 11, color: "#2a5070", letterSpacing: 3, marginBottom: 6 }}>ACCOUNTABILITY SYSTEM</div>
        <h2 style={{ color: "#00d4ff", fontSize: 20, margin: 0 }}>📋 Audit Trail</h2>
        <p style={{ color: "#4a6080", fontSize: 13, marginTop: 6 }}>
          Every query, briefing, and blast radius analysis is logged here with user, time, and action type.
        </p>
      </div>

      {/* Stats bar */}
      <div style={{ display: "flex", gap: 16, marginBottom: 20 }}>
        {Object.entries(ACTION_ICON).map(([type, icon]) => {
          const count = trail.filter(t => t.action_type === type).length;
          return (
            <div key={type} style={{
              background: "rgba(0,212,255,0.04)", border: "1px solid rgba(0,212,255,0.1)",
              borderRadius: 8, padding: "10px 16px", minWidth: 120
            }}>
              <div style={{ fontSize: 18 }}>{icon}</div>
              <div style={{ fontSize: 20, color: ACTION_COLOR[type], fontWeight: "bold" }}>{count}</div>
              <div style={{ fontSize: 10, color: "#2a5070", letterSpacing: 1 }}>{type.replace("_", " ")}</div>
            </div>
          );
        })}
        <div style={{
          background: "rgba(0,212,255,0.04)", border: "1px solid rgba(0,212,255,0.1)",
          borderRadius: 8, padding: "10px 16px", minWidth: 120
        }}>
          <div style={{ fontSize: 18 }}>📊</div>
          <div style={{ fontSize: 20, color: "#ffffff", fontWeight: "bold" }}>{trail.length}</div>
          <div style={{ fontSize: 10, color: "#2a5070", letterSpacing: 1 }}>TOTAL EVENTS</div>
        </div>
      </div>

      {/* Trail Entries */}
      {loading && <div style={{ color: "#4a6080", textAlign: "center", padding: 40 }}>Loading audit trail...</div>}

      {!loading && trail.length === 0 && (
        <div style={{
          background: "rgba(0,0,0,0.2)", border: "1px dashed rgba(0,212,255,0.1)",
          borderRadius: 10, padding: 40, textAlign: "center", color: "#2a4050"
        }}>
          No audit entries yet. Start interacting with the system to generate entries.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {trail.map((entry, i) => (
          <div key={i} style={{
            background: "rgba(0,0,0,0.3)", border: "1px solid rgba(0,212,255,0.08)",
            borderRadius: 8, padding: "12px 16px",
            borderLeft: `3px solid ${ACTION_COLOR[entry.action_type] || "#4a6080"}`
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
              <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span style={{ fontSize: 14 }}>{ACTION_ICON[entry.action_type] || "📌"}</span>
                <span style={{
                  fontSize: 11, color: ACTION_COLOR[entry.action_type],
                  background: `${ACTION_COLOR[entry.action_type]}15`,
                  padding: "2px 8px", borderRadius: 4, letterSpacing: 1
                }}>
                  {entry.action_type.replace("_", " ")}
                </span>
                <span style={{
                  fontSize: 11, color: "#6a9abf",
                  background: "rgba(106,154,191,0.1)",
                  padding: "2px 8px", borderRadius: 4
                }}>
                  {entry.user_role.replace("_", " ")}
                </span>
              </div>
              <div style={{ fontSize: 11, color: "#2a5070" }}>
                {entry.id} • {entry.timestamp}
              </div>
            </div>
            <div style={{ fontSize: 12, color: "#8aa0b8", marginBottom: 4 }}>
              <strong style={{ color: "#6a9abf" }}>Query:</strong> {entry.question}
            </div>
            <div style={{ fontSize: 11, color: "#4a6080" }}>
              <strong>Response preview:</strong> {entry.response_summary}
            </div>
          </div>
        ))}
      </div>

      <button onClick={fetchTrail} style={{
        marginTop: 16, padding: "8px 20px",
        background: "rgba(0,212,255,0.06)", border: "1px solid rgba(0,212,255,0.2)",
        color: "#00d4ff", borderRadius: 6, cursor: "pointer",
        fontSize: 12, letterSpacing: 2, fontFamily: "'Courier New', monospace"
      }}>
        🔄 REFRESH
      </button>
    </div>
  );
}