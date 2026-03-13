import { useState, useRef, useEffect } from "react";

const SUGGESTED = [
  "Will ERP issues affect today's shipments?",
  "Is the security alert a real business threat?",
  "Why is revenue down today?",
  "What's our biggest risk right now?",
  "Prepare a board statement for today's incidents",
];

export default function Chat({ role, api }) {
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: `AI CIO Assistant active. You are logged in as **${role.replace("_"," ")}**. Ask me anything about your enterprise systems, risks, or operational status.`,
      time: new Date().toLocaleTimeString()
    }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async (question) => {
    const q = question || input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", text: q, time: new Date().toLocaleTimeString() }]);
    setLoading(true);

    try {
      const res = await fetch(`${api}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q, role })
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "ai", text: data.answer, time: new Date().toLocaleTimeString() }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "ai", text: "⚠️ Connection error. Make sure the backend is running.", time: new Date().toLocaleTimeString() }]);
    }
    setLoading(false);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
        {/* Suggested questions */}
        {messages.length === 1 && (
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 11, color: "#2a5070", letterSpacing: 2, marginBottom: 10 }}>SUGGESTED QUESTIONS</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {SUGGESTED.map((s, i) => (
                <button key={i} onClick={() => send(s)} style={{
                  background: "rgba(0,212,255,0.05)", border: "1px solid rgba(0,212,255,0.2)",
                  color: "#6a9abf", padding: "6px 12px", borderRadius: 20,
                  cursor: "pointer", fontSize: 12, fontFamily: "'Courier New', monospace"
                }}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{
            marginBottom: 20, display: "flex",
            flexDirection: m.role === "user" ? "row-reverse" : "row", gap: 12
          }}>
            <div style={{
              width: 32, height: 32, borderRadius: "50%", flexShrink: 0,
              background: m.role === "user" ? "rgba(0,212,255,0.2)" : "rgba(0,255,136,0.1)",
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14
            }}>
              {m.role === "user" ? "👤" : "⚡"}
            </div>
            <div style={{ maxWidth: "75%" }}>
              <div style={{
                background: m.role === "user" ? "rgba(0,212,255,0.08)" : "rgba(0,255,136,0.04)",
                border: `1px solid ${m.role === "user" ? "rgba(0,212,255,0.2)" : "rgba(0,255,136,0.15)"}`,
                borderRadius: 8, padding: "12px 16px",
                color: "#c8ddf0", fontSize: 13, lineHeight: 1.8,
                whiteSpace: "pre-wrap", fontFamily: "'Courier New', monospace"
              }}>
                {m.text}
              </div>
              <div style={{ fontSize: 10, color: "#2a4060", marginTop: 4, textAlign: m.role === "user" ? "right" : "left" }}>
                {m.time}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
            <div style={{ width: 32, height: 32, borderRadius: "50%", background: "rgba(0,255,136,0.1)", display: "flex", alignItems: "center", justifyContent: "center" }}>⚡</div>
            <div style={{ background: "rgba(0,255,136,0.04)", border: "1px solid rgba(0,255,136,0.15)", borderRadius: 8, padding: "12px 16px", color: "#4a6080", fontSize: 13 }}>
              Analyzing enterprise data...
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "16px 24px", borderTop: "1px solid rgba(0,212,255,0.1)", background: "rgba(0,0,0,0.3)" }}>
        <div style={{ display: "flex", gap: 10 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Ask about risks, revenue, security, operations..."
            style={{
              flex: 1, background: "rgba(0,212,255,0.05)",
              border: "1px solid rgba(0,212,255,0.2)", borderRadius: 6,
              padding: "10px 16px", color: "#c8ddf0", fontSize: 13,
              fontFamily: "'Courier New', monospace", outline: "none"
            }}
          />
          <button onClick={() => send()} disabled={loading || !input.trim()} style={{
            padding: "10px 20px", background: loading ? "rgba(0,212,255,0.05)" : "rgba(0,212,255,0.15)",
            border: "1px solid rgba(0,212,255,0.3)", color: "#00d4ff",
            borderRadius: 6, cursor: "pointer", fontSize: 13,
            fontFamily: "'Courier New', monospace"
          }}>
            SEND →
          </button>
        </div>
      </div>
    </div>
  );
}