import { useState, useEffect } from "react";
import Chat from "./Chat";
import BlastRadius from "./BlastRadius";
import AuditTrail from "./AuditTrail";
import MorningBriefing from "./MorningBriefing";

const API = "http://localhost:8000";

const TAB_STYLE = (active) => ({
  padding: "10px 20px", cursor: "pointer", fontSize: 13,
  fontFamily: "'Courier New', monospace", letterSpacing: 1,
  background: active ? "rgba(0,212,255,0.15)" : "transparent",
  color: active ? "#00d4ff" : "#4a6080",
  border: "none", borderBottom: active ? "2px solid #00d4ff" : "2px solid transparent",
  transition: "all 0.2s"
});

const STATUS_COLOR = { HEALTHY: "#00ff88", WARNING: "#ffaa00", CRITICAL: "#ff4444", DEGRADED: "#ff8800", DOWN: "#ff0000", HIGH: "#ff4444" };

export default function Dashboard({ role, onLogout }) {
  const [tab, setTab] = useState("briefing");
  const [status, setStatus] = useState(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API}/dashboard-status`);
      const data = await res.json();
      setStatus(data);
    } catch (e) { console.error(e); }
  };

  return (
    <div style={{
      minHeight: "100vh", background: "#0a0f1e",
      fontFamily: "'Courier New', monospace", color: "white"
    }}>
      {/* Top Bar */}
      <div style={{
        background: "rgba(0,0,0,0.6)", borderBottom: "1px solid rgba(0,212,255,0.2)",
        padding: "0 24px", display: "flex", alignItems: "center", justifyContent: "space-between", height: 56
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ color: "#00d4ff", fontSize: 18, letterSpacing: 3 }}>⚡ CIO.AI</span>
          <span style={{ background: "rgba(0,212,255,0.1)", color: "#00d4ff", padding: "3px 10px", borderRadius: 4, fontSize: 11, border: "1px solid rgba(0,212,255,0.3)" }}>
            {role.replace("_", " ")}
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          {status && (
            <>
              <span style={{ fontSize: 12, color: STATUS_COLOR[status.security_threat_level] }}>
                🛡️ THREAT: {status.security_threat_level}
              </span>
              <span style={{ fontSize: 12, color: status.revenue_change < 0 ? "#ff4444" : "#00ff88" }}>
                💰 {status.revenue_change > 0 ? "+" : ""}{status.revenue_change?.toFixed(1)}% Revenue
              </span>
              <span style={{ fontSize: 12, color: status.critical_count > 0 ? "#ff4444" : "#00ff88" }}>
                🚨 {status.critical_count} Critical
              </span>
            </>
          )}
          <button onClick={onLogout} style={{
            background: "transparent", border: "1px solid #2a3a4a",
            color: "#4a6080", padding: "4px 12px", borderRadius: 4,
            cursor: "pointer", fontSize: 12
          }}>LOGOUT</button>
        </div>
      </div>

      <div style={{ display: "flex", height: "calc(100vh - 56px)" }}>
        {/* Left Panel - Server Status */}
        <div style={{
          width: 220, background: "rgba(0,0,0,0.4)",
          borderRight: "1px solid rgba(0,212,255,0.1)", padding: 16, overflowY: "auto"
        }}>
          <div style={{ fontSize: 10, color: "#2a4060", letterSpacing: 2, marginBottom: 12 }}>SYSTEM STATUS</div>
          {status?.servers?.map(s => (
            <div key={s.id} style={{
              marginBottom: 8, padding: "8px 10px",
              background: "rgba(255,255,255,0.02)", borderRadius: 6,
              borderLeft: `3px solid ${STATUS_COLOR[s.status] || "#4a6080"}`
            }}>
              <div style={{ fontSize: 11, color: "#8aa0b8" }}>{s.name}</div>
              <div style={{ fontSize: 10, color: STATUS_COLOR[s.status], marginTop: 2 }}>
                CPU: {s.cpu}% | MEM: {s.memory}%
              </div>
            </div>
          ))}

          <div style={{ fontSize: 10, color: "#2a4060", letterSpacing: 2, margin: "16px 0 8px" }}>ANOMALIES</div>
          {status?.anomalies?.slice(0, 4).map((a, i) => (
            <div key={i} style={{
              marginBottom: 6, padding: "6px 8px",
              background: "rgba(255,68,68,0.05)", borderRadius: 4,
              borderLeft: `2px solid ${STATUS_COLOR[a.severity] || "#ff8800"}`
            }}>
              <div style={{ fontSize: 10, color: STATUS_COLOR[a.severity] }}>{a.type}</div>
            </div>
          ))}
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {/* Tabs */}
          <div style={{ display: "flex", borderBottom: "1px solid rgba(0,212,255,0.1)", background: "rgba(0,0,0,0.3)" }}>
            {[
              { id: "briefing", label: "☀️ MORNING BRIEFING" },
              { id: "chat", label: "💬 ASK CIO AI" },
              { id: "blast", label: "💥 BLAST RADIUS" },
              { id: "audit", label: "📋 AUDIT TRAIL" },
            ].map(t => (
              <button key={t.id} style={TAB_STYLE(tab === t.id)} onClick={() => setTab(t.id)}>
                {t.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ flex: 1, overflow: "auto" }}>
            {tab === "briefing" && <MorningBriefing role={role} api={API} />}
            {tab === "chat" && <Chat role={role} api={API} />}
            {tab === "blast" && <BlastRadius role={role} api={API} />}
            {tab === "audit" && <AuditTrail api={API} />}
          </div>
        </div>
      </div>
    </div>
  );
}