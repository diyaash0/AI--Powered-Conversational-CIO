from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import json, os, urllib.request, urllib.error

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ── LOAD .env FILE IF PRESENT ──────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── AI CONFIG ──────────────────────────────────────────────────────────────────
#
#  PRIMARY   → Ollama (local, zero rate limits, no API key needed)
#              Install: https://ollama.com  then run: ollama pull llama3.2
#              Ollama must be running in background before you start this server.
#
#  FALLBACK  → Google Gemini (if Ollama is not running)
#              Set GEMINI_API_KEY in a .env file or as environment variable
#
#  LAST RESORT → Smart mock (if both above fail — still shows real enterprise data)
#
OLLAMA_URL   = os.environ.get("OLLAMA_URL", "http://localhost:11434")   # default Ollama port
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")              # change to llama3.2:1b for weak laptops
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── ENTERPRISE DATA ────────────────────────────────────────────────────────────
ENTERPRISE_DATA = {
    "infrastructure": {
        "servers": [
            {"id": "SVR-001", "name": "Primary Web Server",    "cpu": 34, "memory": 45, "status": "HEALTHY"},
            {"id": "SVR-002", "name": "Database Server",       "cpu": 58, "memory": 71, "status": "WARNING"},
            {"id": "SVR-003", "name": "ERP Application Server","cpu": 91, "memory": 88, "status": "CRITICAL"},
            {"id": "SVR-004", "name": "Backup Server",         "cpu": 22, "memory": 38, "status": "WARNING"},
            {"id": "SVR-005", "name": "Payment Gateway Server","cpu": 44, "memory": 52, "status": "HEALTHY"},
        ],
        "network": {"bandwidth_usage": 67, "latency_ms": 18, "status": "HEALTHY"}
    },
    "erp_system": {
        "status": "DEGRADED", "response_time_ms": 3400, "baseline_ms": 800,
        "pending_orders": 847, "orders_at_risk": 47,
        "errors": [
            {"time": "02:15 AM", "error": "Database connection pool exhausted",     "severity": "HIGH"},
            {"time": "03:45 AM", "error": "Order sync timeout - Mumbai warehouse",   "severity": "MEDIUM"},
            {"time": "05:00 AM", "error": "Memory allocation failure on ERP server", "severity": "HIGH"},
        ]
    },
    "security": {
        "threat_level": "HIGH",
        "alerts": [
            {"id": "SOC-2201", "type": "Brute Force Attack",    "severity": "CRITICAL",
             "source": "185.220.101.47", "target": "Admin Login Portal", "attempts": 847, "status": "ACTIVE",
             "business_risk": "Unauthorized admin access could expose all customer data"},
            {"id": "SOC-2202", "type": "Unusual Data Export",   "severity": "HIGH",
             "user": "john.smith@nexacorp.com", "exported_mb": 2400, "baseline_mb": 50,
             "status": "UNDER INVESTIGATION",
             "business_risk": "Potential insider threat or compromised credentials"},
            {"id": "SOC-2203", "type": "Malware Detection",     "severity": "HIGH",
             "machine": "LAPTOP-HR-042", "malware": "Ransomware Dropper", "status": "CONTAINED",
             "business_risk": "If spread, could encrypt critical business files"},
            {"id": "SOC-2204", "type": "SSL Certificate Expiry","severity": "MEDIUM",
             "domain": "payments.nexacorp.com", "expires_in_days": 6, "status": "OPEN",
             "business_risk": "Payment portal goes offline in 6 days if not renewed"},
        ],
        "failed_logins_24h": 870, "patches_pending": 14
    },
    "production": {
        "applications": [
            {"name": "Customer Web Portal",       "status": "HEALTHY",  "uptime": 99.7,  "error_rate": 0.8},
            {"name": "Mobile App",                "status": "HEALTHY",  "uptime": 99.2,  "error_rate": 1.2},
            {"name": "Payment Gateway API",       "status": "HEALTHY",  "uptime": 99.98, "error_rate": 0.1},
            {"name": "Inventory Sync Service",    "status": "DEGRADED", "uptime": 97.1,  "error_rate": 8.4},
            {"name": "Order Notification Service","status": "DOWN",     "uptime": 95.0,  "error_rate": 100},
        ]
    },
    "logistics": {
        "shipments_today": 284, "dispatched": 121, "delayed": 47,
        "delay_reason": "ERP system slowdown causing manual processing",
        "warehouses": [
            {"location": "Chennai",   "status": "OPERATIONAL", "pending": 134},
            {"location": "Mumbai",    "status": "BUSY",        "pending": 89, "note": "Manual processing due to ERP"},
            {"location": "Bangalore", "status": "OPERATIONAL", "pending": 61},
        ]
    },
    "business_kpis": {
        "revenue_today_usd": 1200000, "revenue_yesterday_usd": 1450000,
        "revenue_change_percent": -17.2, "monthly_target_usd": 32000000,
        "monthly_achieved_usd": 14800000, "estimated_loss_today_usd": 87500,
        "support_tickets_open": 287, "critical_tickets": 12,
    }
}

ROLE_ACCESS = {
    "CIO":              ["infrastructure","erp_system","security","production","logistics","business_kpis"],
    "Security_Manager": ["security"],
    "Operations_Head":  ["erp_system","logistics","production"],
    "Finance_Head":     ["business_kpis","erp_system"],
    "IT_Manager":       ["infrastructure","production"]
}

audit_trail = []

def log_audit(user_role, action_type, question, response_summary):
    audit_trail.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_role": user_role, "action_type": action_type, "question": question,
        "response_summary": response_summary[:150] + "..." if len(response_summary) > 150 else response_summary,
        "id": f"AUD-{len(audit_trail)+1:04d}"
    })

def detect_anomalies():
    anomalies = []
    for s in ENTERPRISE_DATA["infrastructure"]["servers"]:
        if s["cpu"] > 85:   anomalies.append({"type":"Server CPU Critical","detail":f"{s['name']} CPU at {s['cpu']}%","severity":"CRITICAL"})
        elif s["cpu"] > 70: anomalies.append({"type":"Server CPU Warning", "detail":f"{s['name']} CPU at {s['cpu']}%","severity":"WARNING"})
    erp = ENTERPRISE_DATA["erp_system"]
    sd  = erp["response_time_ms"] / erp["baseline_ms"]
    if sd > 2: anomalies.append({"type":"ERP Performance Degradation","detail":f"ERP is {sd:.1f}x slower ({erp['response_time_ms']}ms vs {erp['baseline_ms']}ms)","severity":"CRITICAL"})
    for a in ENTERPRISE_DATA["security"]["alerts"]:
        if a["severity"] in ["CRITICAL","HIGH"]: anomalies.append({"type":f"Security: {a['type']}","detail":a["business_risk"],"severity":a["severity"]})
    k = ENTERPRISE_DATA["business_kpis"]
    if k["revenue_change_percent"] < -10: anomalies.append({"type":"Revenue Drop","detail":f"Revenue down {abs(k['revenue_change_percent'])}% (${k['estimated_loss_today_usd']:,} loss)","severity":"HIGH"})
    return anomalies

def get_data_for_role(role):
    return {k: ENTERPRISE_DATA[k] for k in ROLE_ACCESS.get(role, []) if k in ENTERPRISE_DATA}


# ══════════════════════════════════════════════════════════════════════════════
#  AI PROVIDER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _call_ollama(system_prompt: str, user_message: str) -> str:
    """
    Calls local Ollama server. No key, no limit, no internet.
    Ollama must be installed and running: https://ollama.com
    Model must be pulled first: ollama pull llama3.2
    """
    url = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "stream": False,   # get full response at once, not streamed chunks
        "options": {
            "temperature": 0.7,
            "num_predict": 1024   # max tokens to generate
        }
    }
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:   # 120s timeout — local models can be slow on first call
        result = json.loads(r.read().decode())
    return result["message"]["content"]


def _call_gemini(system_prompt: str, user_message: str) -> str:
    """
    Fallback: Google Gemini API. Set GEMINI_API_KEY in .env
    """
    full_prompt = f"{system_prompt}\n\n{user_message}"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"maxOutputTokens": 1024, "temperature": 0.7}
    }
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        result = json.loads(r.read().decode())
    return result["candidates"][0]["content"]["parts"][0]["text"]


def call_claude(system_prompt: str, user_message: str) -> str:
    """
    Main AI dispatcher. Priority order:
      1. Ollama (local, unlimited) — always tried first
      2. Gemini  (cloud, if key is set) — tried if Ollama fails
      3. Smart mock — always works, no AI needed
    """
    # ── Try Ollama first ──────────────────────────────────────────────────────
    try:
        response = _call_ollama(system_prompt, user_message)
        print(f"[AI] Ollama ({OLLAMA_MODEL}) responded OK")
        return response
    except urllib.error.URLError:
        # Ollama not running — this is the most common case when not started
        print("[AI] Ollama not reachable (is it running? run: ollama serve)")
    except Exception as e:
        print(f"[AI] Ollama error: {e}")

    # ── Try Gemini as fallback ────────────────────────────────────────────────
    if GEMINI_API_KEY:
        try:
            response = _call_gemini(system_prompt, user_message)
            print("[AI] Gemini fallback responded OK")
            return response
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            print(f"[AI] Gemini error {e.code}: {body}")
        except Exception as e:
            print(f"[AI] Gemini error: {e}")

    # ── Smart mock as last resort ─────────────────────────────────────────────
    print("[AI] Using smart mock — start Ollama for live AI")
    return _smart_mock(system_prompt, user_message)


# ── SMART MOCK (always works, uses real enterprise data) ───────────────────────
def _smart_mock(sys_p: str, user_p: str) -> str:
    k   = ENTERPRISE_DATA["business_kpis"]
    erp = ENTERPRISE_DATA["erp_system"]
    sec = ENTERPRISE_DATA["security"]
    note = "\n\n[Running in mock mode — start Ollama for live AI: ollama serve]"

    if "briefing" in sys_p.lower() or "morning" in sys_p.lower():
        return f"""GOOD MORNING. Here is your briefing for {datetime.now().strftime('%A, %B %d, %Y')}.

🔴 CRITICAL ITEMS:
• ERP Application Server (SVR-003) at 91% CPU — system degraded 4.25x
• Active brute force attack on Admin Portal — 847 attempts from 185.220.101.47
• Revenue down 17.2% — estimated loss today: ${k['estimated_loss_today_usd']:,}

🟡 WATCH LIST:
• 47 shipments delayed, Mumbai warehouse on manual processing
• SSL cert for payments.nexacorp.com expires in 6 days
• Unusual 2400MB data export under investigation (john.smith@nexacorp.com)

💰 REVENUE SNAPSHOT:
${k['revenue_today_usd']:,} today vs ${k['revenue_yesterday_usd']:,} yesterday (-17.2%). Monthly: ${k['monthly_achieved_usd']:,} / ${k['monthly_target_usd']:,}.

✅ RECOMMENDED FIRST ACTION:
Restart ERP Application Server (SVR-003) after scaling DB connection pool. Fixes logistics delay cascade and stops revenue bleed.{note}"""

    elif "blast" in sys_p.lower():
        inc = user_p.split("Incident reported:")[-1].split("Current Enterprise")[0].strip() if "Incident reported:" in user_p else "the reported incident"
        return f"""🎯 INCIDENT: {inc}

📊 BLAST RADIUS ANALYSIS:

TIER 1 - IMMEDIATE IMPACT (0-1 hours):
→ Direct system failure — affected services go offline
→ {erp['orders_at_risk']} orders at risk, processing halts immediately
→ Customer-facing errors surface within minutes

TIER 2 - SHORT TERM (1-8 hours):
→ {ENTERPRISE_DATA['logistics']['delayed']} shipments shift to manual processing
→ Mumbai warehouse backlog grows (currently {ENTERPRISE_DATA['logistics']['warehouses'][1]['pending']} pending)
→ Support tickets spike — {k['support_tickets_open']} open, {k['critical_tickets']} critical

TIER 3 - BUSINESS IMPACT (8-24 hours):
→ Revenue impact compounds — already -17.2% vs yesterday
→ Customer SLA breaches if not communicated proactively
→ Potential regulatory exposure depending on data affected

💰 ESTIMATED FINANCIAL EXPOSURE: ${k['estimated_loss_today_usd']:,} - ${k['estimated_loss_today_usd']*3:,}

🚨 CONTAINMENT PRIORITY:
1. Isolate affected component immediately
2. Activate on-call runbook and notify stakeholders
3. Enable manual fallback for critical order flows

⏱️ RECOVERY ESTIMATE: 2-4 hours with immediate escalation{note}"""

    else:
        q = user_p.lower()
        if "erp" in q or "shipment" in q or "order" in q:
            return f"""ERP is DEGRADED — {erp['response_time_ms']}ms response (4.25x above {erp['baseline_ms']}ms baseline).

Business Impact: {erp['orders_at_risk']} of {erp['pending_orders']} orders at risk. Mumbai warehouse on manual processing. Revenue already -17.2% to ${k['revenue_today_usd']:,}.

Root Cause: SVR-003 at 91% CPU; memory allocation failures logged at 05:00 AM.

Recommended Action: Scale DB connection pool and restart ERP service on SVR-003. Assign Mumbai ops a direct line to process 89 pending orders manually in parallel.{note}"""

        elif "security" in q or "threat" in q or "attack" in q:
            return f"""Security threat level is HIGH with {len(sec['alerts'])} active alerts.

CRITICAL — Brute Force (SOC-2201): {sec['alerts'][0]['attempts']} attempts from {sec['alerts'][0]['source']} on Admin Portal. ACTIVE.
HIGH — Data Export (SOC-2202): john.smith exported 2400MB vs 50MB baseline. Under investigation.
HIGH — Malware (SOC-2203): Ransomware dropper on LAPTOP-HR-042. Currently CONTAINED.

Recommended Action: Block 185.220.101.47 at firewall NOW and force MFA reset for all admin accounts.{note}"""

        else:
            return f"""Current enterprise snapshot:
• ERP: DEGRADED (4.25x slowdown) — {erp['orders_at_risk']} orders at risk
• Security: HIGH threat — active brute force + data export investigation
• Revenue: -17.2% vs yesterday — estimated loss ${k['estimated_loss_today_usd']:,}
• Logistics: {ENTERPRISE_DATA['logistics']['delayed']} shipments delayed

Top Priority: Restore ERP on SVR-003. This fixes logistics, revenue bleed, and reduces overall risk.{note}"""


# ── REQUEST MODELS ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    role: str

class BlastRadiusRequest(BaseModel):
    incident: str
    role: str

# ── ROUTES ─────────────────────────────────────────────────────────────────────
@app.get("/morning-briefing/{role}")
def morning_briefing(role: str):
    data = get_data_for_role(role)
    anomalies = detect_anomalies()
    sys_p = """You are an AI Chief of Staff. Prepare a concise executive morning briefing.
Format EXACTLY like this:
GOOD MORNING [ROLE]. Here is your briefing for today.
🔴 CRITICAL ITEMS: (critical issues only)
🟡 WATCH LIST: (warnings)
💰 REVENUE SNAPSHOT: (one line on financials)
✅ RECOMMENDED FIRST ACTION: (one specific action)
Under 200 words. Be direct. No fluff."""
    user_p = f"Role: {role}\nData: {json.dumps(data)}\nAnomalies: {json.dumps(anomalies)}\nTime: {datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}\nGenerate briefing now."
    response = call_claude(sys_p, user_p)
    log_audit(role, "MORNING_BRIEFING", "Auto-generated morning briefing", response)
    return {"briefing": response, "anomaly_count": len(anomalies), "timestamp": datetime.now().isoformat()}

@app.post("/chat")
def chat(req: ChatRequest):
    data = get_data_for_role(req.role)
    anomalies = detect_anomalies()
    sys_p = f"""You are an AI-powered CIO Assistant for NexaCorp Industries. Role: {req.role}
- Translate technical metrics into BUSINESS impact
- Mention dollar/revenue impact when relevant
- Give ONE clear recommended action at the end
- Speak to a senior executive — no jargon, concise
- If something critical is unasked, add it under "⚠️ Also Note:" """
    user_p = f"Data: {json.dumps(data)}\nAnomalies: {json.dumps(anomalies)}\nQuestion from {req.role}: {req.question}"
    response = call_claude(sys_p, user_p)
    log_audit(req.role, "CHAT_QUERY", req.question, response)
    return {"answer": response, "role": req.role, "timestamp": datetime.now().isoformat()}

@app.post("/blast-radius")
def blast_radius(req: BlastRadiusRequest):
    data = get_data_for_role(req.role)
    sys_p = """You are an AI incident impact analyzer. Map the FULL downstream business impact chain.
Format EXACTLY:
🎯 INCIDENT: [restate]
📊 BLAST RADIUS ANALYSIS:
TIER 1 - IMMEDIATE IMPACT (0-1 hours): → impact1 → impact2
TIER 2 - SHORT TERM (1-8 hours): → impact1 → impact2
TIER 3 - BUSINESS IMPACT (8-24 hours): → impact1 → impact2
💰 ESTIMATED FINANCIAL EXPOSURE: $X - $Y
🚨 CONTAINMENT PRIORITY: 1. action 2. action 3. action
⏱️ RECOVERY ESTIMATE: [time]
Be specific with numbers from data."""
    user_p = f"Incident reported: {req.incident}\nCurrent Enterprise Data: {json.dumps(data)}\nCalculate full blast radius."
    response = call_claude(sys_p, user_p)
    log_audit(req.role, "BLAST_RADIUS", req.incident, response)
    return {"analysis": response, "timestamp": datetime.now().isoformat()}

@app.get("/audit-trail")
def get_audit_trail():
    return {"trail": list(reversed(audit_trail)), "total": len(audit_trail)}

@app.get("/dashboard-status")
def dashboard_status():
    anomalies = detect_anomalies()
    k = ENTERPRISE_DATA["business_kpis"]
    return {
        "anomaly_count": len(anomalies), "anomalies": anomalies,
        "critical_count": len([a for a in anomalies if a["severity"]=="CRITICAL"]),
        "revenue_today": k["revenue_today_usd"], "revenue_change": k["revenue_change_percent"],
        "servers": ENTERPRISE_DATA["infrastructure"]["servers"],
        "security_threat_level": ENTERPRISE_DATA["security"]["threat_level"],
        "erp_status": ENTERPRISE_DATA["erp_system"]["status"],
        "shipments_delayed": ENTERPRISE_DATA["logistics"]["delayed"],
    }

@app.get("/health")
def health():
    # Check if Ollama is actually running right now
    ollama_status = "not running"
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            tags = json.loads(r.read().decode())
            models = [m["name"] for m in tags.get("models", [])]
            ollama_status = f"running — models: {', '.join(models) if models else 'none pulled yet'}"
    except Exception:
        pass

    if "running" in ollama_status:
        provider = f"Ollama local ({OLLAMA_MODEL}) — unlimited, no rate limits"
    elif GEMINI_API_KEY:
        provider = "Gemini fallback (Ollama not running)"
    else:
        provider = "Smart mock (start Ollama: ollama serve)"

    return {
        "status": "running",
        "time": datetime.now().isoformat(),
        "ai_provider": provider,
        "ollama": ollama_status,
        "ollama_url": OLLAMA_URL,
        "ollama_model": OLLAMA_MODEL,
    }