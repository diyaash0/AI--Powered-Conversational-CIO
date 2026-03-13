const ROLES = [
  { id: "CIO", label: "Chief Information Officer", icon: "👔", desc: "Full access — all systems, all data" },
  { id: "Security_Manager", label: "Security Manager", icon: "🛡️", desc: "Security alerts and threat data only" },
  { id: "Operations_Head", label: "Operations Head", icon: "⚙️", desc: "ERP, logistics and production data" },
  { id: "Finance_Head", label: "Finance Head", icon: "💰", desc: "Revenue, KPIs and financial data" },
  { id: "IT_Manager", label: "IT Manager", icon: "🖥️", desc: "Infrastructure and production systems" },
];

export default function Login({ onLogin }) {
  return (
    <div style={{
      minHeight: "100vh", background: "#0a0f1e",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontFamily: "'Courier New', monospace"
    }}>
      <div style={{ width: 480, padding: 40 }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 40 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>⚡</div>
          <h1 style={{ color: "#00d4ff", fontSize: 28, margin: 0, letterSpacing: 4 }}>
            CIO.AI
          </h1>
          <p style={{ color: "#4a5568", margin: "8px 0 0", fontSize: 13, letterSpacing: 2 }}>
            AI CONVERSATIONAL CIO — SELECT YOUR ROLE
          </p>
        </div>

        {/* Role Cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {ROLES.map(r => (
            <button
              key={r.id}
              onClick={() => onLogin(r.id)}
              style={{
                background: "rgba(0,212,255,0.05)",
                border: "1px solid rgba(0,212,255,0.2)",
                borderRadius: 8, padding: "16px 20px",
                display: "flex", alignItems: "center", gap: 16,
                cursor: "pointer", textAlign: "left",
                transition: "all 0.2s",
                color: "white"
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = "rgba(0,212,255,0.12)";
                e.currentTarget.style.borderColor = "#00d4ff";
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = "rgba(0,212,255,0.05)";
                e.currentTarget.style.borderColor = "rgba(0,212,255,0.2)";
              }}
            >
              <span style={{ fontSize: 28 }}>{r.icon}</span>
              <div>
                <div style={{ fontWeight: "bold", fontSize: 14, color: "#00d4ff" }}>{r.label}</div>
                <div style={{ fontSize: 12, color: "#4a6080", marginTop: 2 }}>{r.desc}</div>
              </div>
            </button>
          ))}
        </div>

        <p style={{ color: "#2a3a4a", textAlign: "center", fontSize: 11, marginTop: 32, letterSpacing: 1 }}>
          CIO.AI — INTERNAL AI SYSTEM v1.0
        </p>
      </div>
    </div>
  );
}