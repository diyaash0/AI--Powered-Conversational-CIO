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
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

# ── AI CONFIG ──────────────────────────────────────────────────────────────────
OLLAMA_URL     = os.environ.get("OLLAMA_URL",    "http://localhost:11434")
OLLAMA_MODEL   = os.environ.get("OLLAMA_MODEL",  "llama3.2:1b")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# ── POSTGRESQL CONFIG ──────────────────────────────────────────────────────────
#
#  Set these in your .env file:
#    DIRECT_URL  = postgresql://...
#    DATABASE_URL = postgresql://...
#
#  Required tables (run /seed-database once to populate):
#    - servers          (id, name, cpu, memory, status)
#    - network_status   (bandwidth_usage, latency_ms, status)
#    - erp_system       (status, response_time_ms, baseline_ms, pending_orders, orders_at_risk)
#    - erp_errors       (time, error, severity)
#    - security_meta    (threat_level, failed_logins_24h, patches_pending)
#    - security_alerts  (alert_id, type, severity, source, target, attempts, status, business_risk,
#                        user_email, exported_mb, baseline_mb, machine, malware, domain, expires_in_days)
#    - applications     (name, status, uptime, error_rate)
#    - logistics        (shipments_today, dispatched, delayed, delay_reason)
#    - warehouses       (location, status, pending, note)
#    - business_kpis    (revenue_today_usd, revenue_yesterday_usd, revenue_change_percent,
#                        monthly_target_usd, monthly_achieved_usd, estimated_loss_today_usd,
#                        support_tickets_open, critical_tickets)
#
import psycopg2
import psycopg2.extras

DB_URL = os.environ.get("DIRECT_URL") or os.environ.get("DATABASE_URL")


# ══════════════════════════════════════════════════════════════════════════════
#  POSTGRESQL HELPER
# ══════════════════════════════════════════════════════════════════════════════

def _pg_select(table: str) -> list:
    """Convenience: SELECT * from a PostgreSQL table, returns list of dicts."""
    if not DB_URL:
        raise RuntimeError("DIRECT_URL / DATABASE_URL not set")

    conn = None
    try:
        conn = psycopg2.connect(dsn=DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        with conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {table};")
                rows = cur.fetchall()
                # Parse objects to simple dicts
                return [dict(r) for r in rows]
    finally:
        if conn:
            conn.close()

def _pg_upsert(table: str, rows: list):
    """Insert a list of dicts into a PostgreSQL table."""
    if not DB_URL:
        raise RuntimeError("DIRECT_URL / DATABASE_URL not set")
    
    if not rows:
        return
    
    conn = None
    try:
        conn = psycopg2.connect(dsn=DB_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        with conn:
            with conn.cursor() as cur:
                keys = list(rows[0].keys())
                columns = ", ".join(keys)
                values_template = ", ".join(["%s"] * len(keys))
                insert_query = f"INSERT INTO {table} ({columns}) VALUES %s"
                
                # Simple insert for seed
                data = [tuple(row[k] for k in keys) for row in rows]
                psycopg2.extras.execute_values(cur, insert_query, data)
    finally:
        if conn:
            conn.close()


# ══════════════════════════════════════════════════════════════════════════════
#  ENTERPRISE DATA LOADER (fetches live from Supabase)
# ══════════════════════════════════════════════════════════════════════════════

def load_enterprise_data() -> dict:
    """
    Assembles the ENTERPRISE_DATA dict by fetching all tables from Supabase.
    Returns the same nested structure the rest of the app already expects,
    so zero changes are needed downstream.
    Falls back to hardcoded defaults if Supabase is not configured.
    """
    if not DB_URL:
        print("[DB] PostgreSQL not configured — using hardcoded fallback data")
        return _hardcoded_fallback()

    try:
        servers      = _pg_select("servers")
        network_rows = _pg_select("network_status")
        network      = network_rows[0] if network_rows else {}

        erp_rows  = _pg_select("erp_system")
        erp_meta  = erp_rows[0] if erp_rows else {}
        erp_errors = _pg_select("erp_errors")

        sec_rows   = _pg_select("security_meta")
        sec_meta   = sec_rows[0] if sec_rows else {}
        sec_alerts = _pg_select("security_alerts")

        # Normalise alert shape coming from DB → original dict shape
        normalised_alerts = []
        for a in sec_alerts:
            alert = {
                "id":            a.get("alert_id"),
                "type":          a.get("type"),
                "severity":      a.get("severity"),
                "status":        a.get("status"),
                "business_risk": a.get("business_risk"),
            }
            # Optional fields depending on alert type
            for opt in ("source","target","attempts","user_email","exported_mb",
                        "baseline_mb","machine","malware","domain","expires_in_days"):
                if a.get(opt) is not None:
                    # keep original key names consistent with old code
                    dest_key = "user" if opt == "user_email" else opt
                    alert[dest_key] = a[opt]
            normalised_alerts.append(alert)

        apps       = _pg_select("applications")
        logistics_rows = _pg_select("logistics")
        logistics  = logistics_rows[0] if logistics_rows else {}
        warehouses = _pg_select("warehouses")

        kpi_rows   = _pg_select("business_kpis")
        kpis       = kpi_rows[0] if kpi_rows else {}

        print("[DB] PostgreSQL data loaded successfully")
        return {
            "infrastructure": {
                "servers": servers,
                "network": network,
            },
            "erp_system": {
                **erp_meta,
                "errors": erp_errors,
            },
            "security": {
                "threat_level":      sec_meta.get("threat_level", "UNKNOWN"),
                "failed_logins_24h": sec_meta.get("failed_logins_24h", 0),
                "patches_pending":   sec_meta.get("patches_pending", 0),
                "alerts":            normalised_alerts,
            },
            "production": {
                "applications": apps,
            },
            "logistics": {
                **logistics,
                "warehouses": warehouses,
            },
            "business_kpis": kpis,
        }

    except Exception as e:
        print(f"[DB] PostgreSQL error ({e}) — falling back to hardcoded data")
        return _hardcoded_fallback()


def _hardcoded_fallback() -> dict:
    """Original hardcoded data — used when Supabase is unavailable."""
    return {
        "infrastructure": {
            "servers": [
                {"id": "SVR-001", "name": "Primary Web Server",     "cpu": 34, "memory": 45, "status": "HEALTHY"},
                {"id": "SVR-002", "name": "Database Server",        "cpu": 58, "memory": 71, "status": "WARNING"},
                {"id": "SVR-003", "name": "ERP Application Server", "cpu": 91, "memory": 88, "status": "CRITICAL"},
                {"id": "SVR-004", "name": "Backup Server",          "cpu": 22, "memory": 38, "status": "WARNING"},
                {"id": "SVR-005", "name": "Payment Gateway Server", "cpu": 44, "memory": 52, "status": "HEALTHY"},
            ],
            "network": {"bandwidth_usage": 67, "latency_ms": 18, "status": "HEALTHY"}
        },
        "erp_system": {
            "status": "DEGRADED", "response_time_ms": 3400, "baseline_ms": 800,
            "pending_orders": 847, "orders_at_risk": 47,
            "errors": [
                {"time": "02:15 AM", "error": "Database connection pool exhausted",      "severity": "HIGH"},
                {"time": "03:45 AM", "error": "Order sync timeout - Mumbai warehouse",   "severity": "MEDIUM"},
                {"time": "05:00 AM", "error": "Memory allocation failure on ERP server", "severity": "HIGH"},
            ]
        },
        "security": {
            "threat_level": "HIGH", "failed_logins_24h": 870, "patches_pending": 14,
            "alerts": [
                {"id": "SOC-2201", "type": "Brute Force Attack",   "severity": "CRITICAL",
                 "source": "185.220.101.47", "target": "Admin Login Portal", "attempts": 847,
                 "status": "ACTIVE", "business_risk": "Unauthorized admin access could expose all customer data"},
                {"id": "SOC-2202", "type": "Unusual Data Export",  "severity": "HIGH",
                 "user": "john.smith@nexacorp.com", "exported_mb": 2400, "baseline_mb": 50,
                 "status": "UNDER INVESTIGATION", "business_risk": "Potential insider threat or compromised credentials"},
                {"id": "SOC-2203", "type": "Malware Detection",    "severity": "HIGH",
                 "machine": "LAPTOP-HR-042", "malware": "Ransomware Dropper",
                 "status": "CONTAINED", "business_risk": "If spread, could encrypt critical business files"},
                {"id": "SOC-2204", "type": "SSL Certificate Expiry","severity": "MEDIUM",
                 "domain": "payments.nexacorp.com", "expires_in_days": 6,
                 "status": "OPEN", "business_risk": "Payment portal goes offline in 6 days if not renewed"},
            ],
        },
        "production": {
            "applications": [
                {"name": "Customer Web Portal",        "status": "HEALTHY",  "uptime": 99.7,  "error_rate": 0.8},
                {"name": "Mobile App",                 "status": "HEALTHY",  "uptime": 99.2,  "error_rate": 1.2},
                {"name": "Payment Gateway API",        "status": "HEALTHY",  "uptime": 99.98, "error_rate": 0.1},
                {"name": "Inventory Sync Service",     "status": "DEGRADED", "uptime": 97.1,  "error_rate": 8.4},
                {"name": "Order Notification Service", "status": "DOWN",     "uptime": 95.0,  "error_rate": 100},
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


# ── ROLE ACCESS CONTROL ────────────────────────────────────────────────────────
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
        "timestamp":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_role":       user_role,
        "action_type":     action_type,
        "question":        question,
        "response_summary": response_summary[:150] + "..." if len(response_summary) > 150 else response_summary,
        "id":              f"AUD-{len(audit_trail)+1:04d}"
    })

def detect_anomalies(data: dict) -> list:
    anomalies = []
    for s in data.get("infrastructure", {}).get("servers", []):
        cpu = s.get("cpu", 0)
        if cpu > 85:
            anomalies.append({"type": "Server CPU Critical", "detail": f"{s.get('name','Unknown')} CPU at {cpu}%", "severity": "CRITICAL"})
        elif cpu > 70:
            anomalies.append({"type": "Server CPU Warning",  "detail": f"{s.get('name','Unknown')} CPU at {cpu}%", "severity": "WARNING"})
    erp = data.get("erp_system", {})
    rt  = erp.get("response_time_ms", 0)
    bl  = erp.get("baseline_ms", 1)
    if bl and rt / bl > 2:
        anomalies.append({"type": "ERP Performance Degradation",
                           "detail": f"ERP is {rt/bl:.1f}x slower ({rt}ms vs {bl}ms baseline)",
                           "severity": "CRITICAL"})
    for a in data.get("security", {}).get("alerts", []):
        if a.get("severity") in ["CRITICAL", "HIGH"]:
            anomalies.append({"type": f"Security: {a.get('type','Unknown')}", "detail": a.get("business_risk",""), "severity": a.get("severity")})
    k = data.get("business_kpis", {})
    rev_change = k.get("revenue_change_percent", 0)
    loss       = k.get("estimated_loss_today_usd", 0)
    if rev_change < -10:
        anomalies.append({"type": "Revenue Drop",
                           "detail": f"Revenue down {abs(rev_change)}% (${loss:,} loss)",
                           "severity": "HIGH"})
    return anomalies

def get_data_for_role(role: str, data: dict) -> dict:
    return {k: data[k] for k in ROLE_ACCESS.get(role, []) if k in data}


# ══════════════════════════════════════════════════════════════════════════════
#  AI PROVIDER FUNCTIONS  (unchanged)
# ══════════════════════════════════════════════════════════════════════════════

def _call_ollama(system_prompt: str, user_message: str) -> str:
    url     = f"{OLLAMA_URL}/api/chat"
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message}
        ],
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 1024}
    }
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        result = json.loads(r.read().decode())
    return result["message"]["content"]


def _call_gemini(system_prompt: str, user_message: str) -> str:
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
    try:
        response = _call_ollama(system_prompt, user_message)
        print(f"[AI] Ollama ({OLLAMA_MODEL}) responded OK")
        return response
    except urllib.error.URLError:
        print("[AI] Ollama not reachable (is it running? run: ollama serve)")
    except Exception as e:
        print(f"[AI] Ollama error: {e}")

    if GEMINI_API_KEY:
        try:
            response = _call_gemini(system_prompt, user_message)
            print("[AI] Gemini fallback responded OK")
            return response
        except urllib.error.HTTPError as e:
            print(f"[AI] Gemini error {e.code}: {e.read().decode()}")
        except Exception as e:
            print(f"[AI] Gemini error: {e}")

    print("[AI] Using smart mock — start Ollama for live AI")
    return _smart_mock(system_prompt, user_message)


def _smart_mock(sys_p: str, user_p: str) -> str:
    # Load fresh data for mock responses too
    data = load_enterprise_data()
    k    = data["business_kpis"]
    erp  = data["erp_system"]
    sec  = data["security"]
    note = "\n\n[Running in mock mode — start Ollama for live AI: ollama serve]"

    if "briefing" in sys_p.lower() or "morning" in sys_p.lower():
        return f"""GOOD MORNING. Here is your briefing for {datetime.now().strftime('%A, %B %d, %Y')}.

🔴 CRITICAL ITEMS:
• ERP Application Server at critical CPU — system degraded
• Active brute force attack on Admin Portal — {sec['alerts'][0]['attempts'] if sec['alerts'] else 'N/A'} attempts
• Revenue down {abs(k['revenue_change_percent'])}% — estimated loss today: ${k['estimated_loss_today_usd']:,}

🟡 WATCH LIST:
• {data['logistics']['delayed']} shipments delayed, Mumbai warehouse on manual processing
• SSL cert expiry and unusual data export under investigation

💰 REVENUE SNAPSHOT:
${k['revenue_today_usd']:,} today vs ${k['revenue_yesterday_usd']:,} yesterday ({k['revenue_change_percent']}%). Monthly: ${k['monthly_achieved_usd']:,} / ${k['monthly_target_usd']:,}.

✅ RECOMMENDED FIRST ACTION:
Restart ERP Application Server after scaling DB connection pool.{note}"""

    elif "blast" in sys_p.lower():
        inc = user_p.split("Incident reported:")[-1].split("Current Enterprise")[0].strip() if "Incident reported:" in user_p else "the reported incident"
        return f"""🎯 INCIDENT: {inc}

📊 BLAST RADIUS ANALYSIS:

TIER 1 - IMMEDIATE IMPACT (0-1 hours):
→ Direct system failure — affected services go offline
→ {erp['orders_at_risk']} orders at risk, processing halts immediately

TIER 2 - SHORT TERM (1-8 hours):
→ {data['logistics']['delayed']} shipments shift to manual processing
→ Support tickets spike — {k['support_tickets_open']} open, {k['critical_tickets']} critical

TIER 3 - BUSINESS IMPACT (8-24 hours):
→ Revenue impact compounds — already {k['revenue_change_percent']}% vs yesterday
→ Customer SLA breaches if not communicated proactively

💰 ESTIMATED FINANCIAL EXPOSURE: ${k['estimated_loss_today_usd']:,} - ${k['estimated_loss_today_usd']*3:,}

🚨 CONTAINMENT PRIORITY:
1. Isolate affected component immediately
2. Activate on-call runbook and notify stakeholders
3. Enable manual fallback for critical order flows

⏱️ RECOVERY ESTIMATE: 2-4 hours with immediate escalation{note}"""

    else:
        return f"""Current enterprise snapshot:
• ERP: {erp['status']} — {erp['orders_at_risk']} orders at risk
• Security: {sec['threat_level']} threat — {len(sec['alerts'])} active alerts
• Revenue: {k['revenue_change_percent']}% vs yesterday — estimated loss ${k['estimated_loss_today_usd']:,}
• Logistics: {data['logistics']['delayed']} shipments delayed

Top Priority: Restore ERP server. This fixes logistics, revenue bleed, and reduces overall risk.{note}"""


# ── REQUEST MODELS ─────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str
    role: str

class BlastRadiusRequest(BaseModel):
    incident: str
    role: str


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/morning-briefing/{role}")
def morning_briefing(role: str):
    data      = load_enterprise_data()
    role_data = get_data_for_role(role, data)
    anomalies = detect_anomalies(data)
    sys_p = """You are an AI Chief of Staff. Prepare a concise executive morning briefing.
Format EXACTLY like this:
GOOD MORNING [ROLE]. Here is your briefing for today.
🔴 CRITICAL ITEMS: (critical issues only)
🟡 WATCH LIST: (warnings)
💰 REVENUE SNAPSHOT: (one line on financials)
✅ RECOMMENDED FIRST ACTION: (one specific action)
Under 200 words. Be direct. No fluff."""
    user_p = f"Role: {role}\nData: {json.dumps(role_data)}\nAnomalies: {json.dumps(anomalies)}\nTime: {datetime.now().strftime('%A, %B %d, %Y - %I:%M %p')}\nGenerate briefing now."
    response = call_claude(sys_p, user_p)
    log_audit(role, "MORNING_BRIEFING", "Auto-generated morning briefing", response)
    return {"briefing": response, "anomaly_count": len(anomalies), "timestamp": datetime.now().isoformat()}


@app.post("/chat")
def chat(req: ChatRequest):
    data      = load_enterprise_data()
    role_data = get_data_for_role(req.role, data)
    anomalies = detect_anomalies(data)
    sys_p = f"""You are an AI-powered CIO Assistant for NexaCorp Industries. Role: {req.role}
- Translate technical metrics into BUSINESS impact
- Mention dollar/revenue impact when relevant
- Give ONE clear recommended action at the end
- Speak to a senior executive — no jargon, concise
- If something critical is unasked, add it under "⚠️ Also Note:" """
    user_p = f"Data: {json.dumps(role_data)}\nAnomalies: {json.dumps(anomalies)}\nQuestion from {req.role}: {req.question}"
    response = call_claude(sys_p, user_p)
    log_audit(req.role, "CHAT_QUERY", req.question, response)
    return {"answer": response, "role": req.role, "timestamp": datetime.now().isoformat()}


@app.post("/blast-radius")
def blast_radius(req: BlastRadiusRequest):
    data      = load_enterprise_data()
    role_data = get_data_for_role(req.role, data)
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
    user_p = f"Incident reported: {req.incident}\nCurrent Enterprise Data: {json.dumps(role_data)}\nCalculate full blast radius."
    response = call_claude(sys_p, user_p)
    log_audit(req.role, "BLAST_RADIUS", req.incident, response)
    return {"analysis": response, "timestamp": datetime.now().isoformat()}


@app.get("/audit-trail")
def get_audit_trail():
    return {"trail": list(reversed(audit_trail)), "total": len(audit_trail)}

# ══════════════════════════════════════════════════════════════════════════════
#  AUTOMATED EMAIL ALERTS (Runs every 60 seconds)
# ══════════════════════════════════════════════════════════════════════════════
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Put your email credentials in backend/.env
ALERT_EMAIL_SENDER = os.environ.get("ALERT_EMAIL_SENDER", "")
ALERT_EMAIL_PASSWORD = os.environ.get("ALERT_EMAIL_PASSWORD", "")  # Use an App Password!
ALERT_EMAIL_RECIPIENT = os.environ.get("ALERT_EMAIL_RECIPIENT", "")

# Keep track of what we've alerted so we don't spam
_alerted_anomalies = set()

async def background_alert_monitor():
    """Checks for CRITICAL anomalies every 60 seconds and emails the CIO."""
    print("[Alerts] Background monitor started. Waiting for database connection...")
    while True:
        await asyncio.sleep(60)
        
        # Skip if emails aren't configured
        if not ALERT_EMAIL_SENDER or not ALERT_EMAIL_PASSWORD or not ALERT_EMAIL_RECIPIENT:
            continue
            
        try:
            data = load_enterprise_data()
            anomalies = detect_anomalies(data)
            
            for a in anomalies:
                if a["severity"] == "CRITICAL":
                    # Create a unique key for this anomaly so we only alert once per restart
                    incident_key = f"{a['type']}-{a['detail']}"
                    
                    if incident_key not in _alerted_anomalies:
                        _send_critical_email_alert(a, data)
                        _alerted_anomalies.add(incident_key)
                        
                        log_audit("SYSTEM_MONITOR", "EMAIL_ALERT_SENT", "Critical Anomaly Detected", f"Alert sent for: {a['type']}")
        except Exception as e:
            print(f"[Alerts] Monitor error: {e}")

def _send_critical_email_alert(anomaly, data: dict):
    print(f"[Alerts] Attempting to send critical email for: {anomaly['type']}")
    
    # ── AI-GENERATED NATURAL LANGUAGE EMAIL BODY ──────────
    sys_p = """You are an expert AI Chief Information Officer Assistant.
A critical anomaly has just occurred in the enterprise system. 
Write an urgent, concise, natural-language email (3-4 sentences max) to the human CIO explaining what exactly is failing and what the immediate business impact is based on the data.
Format it clearly. Do not use generic greetings like "Dear CIO", start directly with the alert. Use bullet points if helpful."""

    user_p = f"Anomaly Detected: {anomaly['type']} - {anomaly['detail']}\nContext: {json.dumps(anomaly)}\nCurrent KPIS and System Data: {json.dumps(data)}"
    
    try:
        natural_language_body = call_claude(sys_p, user_p)
    except Exception as e:
        print(f"[Alerts] AI generation failed, using fallback text. {e}")
        natural_language_body = f"Incident Detected: {anomaly['type']}. Details: {anomaly['detail']}. Please login to the dashboard immediately to resolve this."

    # Parse newlines to HTML breaks so the AI formatting looks good in email
    html_ai_body = natural_language_body.replace('\n', '<br>')

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚨 URGENT: NEXACORP CIO ALERT - {anomaly['type']}"
    msg["From"] = ALERT_EMAIL_SENDER
    msg["To"] = ALERT_EMAIL_RECIPIENT

    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
        <div style="max-width: 600px; margin: auto; background: white; padding: 30px; border-top: 5px solid #ff4444; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
          <h2 style="color: #ff4444; margin-top: 0;">⚠️ CRITICAL ENTERPRISE ALERT</h2>
          <p><strong>Time:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
          <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
          
          <h3 style="color: #333;">Incident Type</h3>
          <p style="font-size: 16px; font-weight: bold; color: #ff0000; background: #ffeeee; padding: 10px; border-radius: 4px;">{anomaly['type']}</p>
          
          <h3 style="color: #333;">Details</h3>
          <p style="font-size: 15px; color: #555;">{anomaly['detail']}</p>
          
          <br>
          <a href="http://localhost:3001" style="display: 100%; background: #00d4ff; color: #000; text-decoration: none; padding: 12px 20px; font-weight: bold; border-radius: 4px; text-align: center;">ACCESS CIO DASHBOARD</a>
        </div>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, "html"))

    try:
        # Connect to Gmail SMTP (change if using Outlook/etc)
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(ALERT_EMAIL_SENDER, ALERT_EMAIL_PASSWORD)
        server.sendmail(ALERT_EMAIL_SENDER, ALERT_EMAIL_RECIPIENT, msg.as_string())
        server.quit()
        print(f"[Alerts] Email successfully sent to {ALERT_EMAIL_RECIPIENT}")
    except Exception as e:
        print(f"[Alerts] Failed to send email: {e}")

@app.on_event("startup")
async def startup_event():
    # Start the monitor when the server boots
    asyncio.create_task(background_alert_monitor())




@app.get("/dashboard-status")
def dashboard_status():
    data      = load_enterprise_data()
    anomalies = detect_anomalies(data)
    k         = data["business_kpis"]
    return {
        "anomaly_count":          len(anomalies),
        "anomalies":              anomalies,
        "critical_count":         len([a for a in anomalies if a["severity"] == "CRITICAL"]),
        "revenue_today":          k["revenue_today_usd"],
        "revenue_change":         k["revenue_change_percent"],
        "servers":                data["infrastructure"]["servers"],
        "security_threat_level":  data["security"]["threat_level"],
        "erp_status":             data["erp_system"]["status"],
        "shipments_delayed":      data["logistics"]["delayed"],
    }


@app.get("/health")
def health():
    ollama_status = "not running"
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            tags   = json.loads(r.read().decode())
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

    postgres_ok = bool(DB_URL)
    cleaned_url = "configured" if DB_URL else "not set"
    return {
        "status":        "running",
        "time":          datetime.now().isoformat(),
        "ai_provider":   provider,
        "ollama":        ollama_status,
        "ollama_url":    OLLAMA_URL,
        "ollama_model":  OLLAMA_MODEL,
        "postgres":      "connected" if postgres_ok else "not configured (using hardcoded fallback)",
        "postgres_url":  cleaned_url,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  ONE-TIME SEED ROUTE  —  POST /seed-database
#  Run this ONCE after creating your Supabase tables to populate them.
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/seed-database")
def seed_database():
    """
    Pushes the original hardcoded data into PostgreSQL.
    Run once: POST http://localhost:8000/seed-database
    Requires DIRECT_URL or DATABASE_URL to be set.
    """
    if not DB_URL:
        raise HTTPException(status_code=400, detail="DIRECT_URL or DATABASE_URL must be set in .env")

    seed = _hardcoded_fallback()
    results = {}

    try:
        # servers
        _pg_upsert("servers", seed["infrastructure"]["servers"])
        results["servers"] = "seeded"

        # network_status
        _pg_upsert("network_status", [seed["infrastructure"]["network"]])
        results["network_status"] = "seeded"

        # erp_system (without errors key)
        erp = {k: v for k, v in seed["erp_system"].items() if k != "errors"}
        _pg_upsert("erp_system", [erp])
        results["erp_system"] = "seeded"

        # erp_errors
        _pg_upsert("erp_errors", seed["erp_system"]["errors"])
        results["erp_errors"] = "seeded"

        # security_meta
        sec_meta = {
            "threat_level":      seed["security"]["threat_level"],
            "failed_logins_24h": seed["security"]["failed_logins_24h"],
            "patches_pending":   seed["security"]["patches_pending"],
        }
        _pg_upsert("security_meta", [sec_meta])
        results["security_meta"] = "seeded"

        # security_alerts — remap keys to DB column names
        alerts_db = []
        for a in seed["security"]["alerts"]:
            row = {
                "alert_id":      a["id"],
                "type":          a["type"],
                "severity":      a["severity"],
                "status":        a["status"],
                "business_risk": a["business_risk"],
                "source":        a.get("source"),
                "target":        a.get("target"),
                "attempts":      a.get("attempts"),
                "user_email":    a.get("user"),
                "exported_mb":   a.get("exported_mb"),
                "baseline_mb":   a.get("baseline_mb"),
                "machine":       a.get("machine"),
                "malware":       a.get("malware"),
                "domain":        a.get("domain"),
                "expires_in_days": a.get("expires_in_days"),
            }
            alerts_db.append(row)
        _pg_upsert("security_alerts", alerts_db)
        results["security_alerts"] = "seeded"

        # applications
        _pg_upsert("applications", seed["production"]["applications"])
        results["applications"] = "seeded"

        # logistics
        logistics = {k: v for k, v in seed["logistics"].items() if k != "warehouses"}
        _pg_upsert("logistics", [logistics])
        results["logistics"] = "seeded"

        # warehouses
        _pg_upsert("warehouses", seed["logistics"]["warehouses"])
        results["warehouses"] = "seeded"

        # business_kpis
        _pg_upsert("business_kpis", [seed["business_kpis"]])
        results["business_kpis"] = "seeded"

        return {"status": "success", "tables_seeded": results}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seed failed: {e}")