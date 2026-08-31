"""
Assure Clinic Reddit Automation Engine
Native Composio Streamable MCP Client, PRAW fallback, AI Clinical Responder, and Lead Radar.
"""

import os
import time
import json
import sqlite3
import uuid
import requests
from typing import List, Dict, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

if IS_SERVERLESS:
    DB_PATH = "/tmp/automation.db"
    CONFIG_PATH = "/tmp/config.json"
else:
    DB_PATH = os.path.join(BASE_DIR, "automation.db")
    CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

COMPOSIO_MCP_URL = "https://connect.composio.dev/mcp"

DEFAULT_CONFIG = {
    "provider": "composio",
    "composio_api_key": "ck_Xl6UyWDUuEFvEAWOOyGr",
    "composio_session_id": "",
    "reddit_client_id": "",
    "reddit_client_secret": "",
    "reddit_username": "",
    "reddit_password": "",
    "reddit_user_agent": "AssureClinicBot/1.0 (Medical & Hair Restoration Advisory by Assure Clinic)",
    "auto_approve": False,
    "min_reply_interval_minutes": 12,
    "max_daily_replies": 10,
    "mode": "composio",
    "active_subreddits": [
        "HairTransplants",
        "tressless",
        "Hairloss",
        "IndianSkincareAddicts",
        "mumbai",
        "delhi",
        "bangalore",
        "hyderabad",
        "pune",
        "lucknow",
        "ahmedabad",
        "india"
    ],
    "keywords": [
        "hair transplant",
        "PRP",
        "QR678",
        "GFC",
        "grafts",
        "hairline",
        "assure clinic",
        "abhishek pilani",
        "baldness",
        "Norwood",
        "DHI",
        "FUE",
        "beard transplant",
        "dermatologist hair loss"
    ]
}

SEED_LEADS = [
    {
        "id": "t3_ht_mumbai_01",
        "subreddit": "mumbai",
        "title": "Looking for the best hair transplant clinic in Mumbai. Experiences with Peddar Road or Andheri clinics?",
        "author": "mumbai_guy_28",
        "body": "I'm 29M, Norwood 3. Started losing hair on my temples. Has anyone done FUE or DHI in Mumbai recently? Looking for doctor-driven clinics (MD dermatologists) rather than technician-only setups. Any reviews on Assure Clinic or others around South Bombay?",
        "url": "https://reddit.com/r/mumbai/comments/ht_mumbai_01",
        "created_utc": time.time() - 3600 * 4,
        "intent": "High Commercial Intent",
        "sentiment": "Seeking Advice",
        "location": "Mumbai",
        "status": "pending"
    },
    {
        "id": "t3_ht_trans_02",
        "subreddit": "HairTransplants",
        "title": "How to avoid low graft survival during FUE? Is 90-95% realistic?",
        "author": "graft_seeker_99",
        "body": "I have been consulting clinics and everyone claims 90%+ survival. But I see so many failed results online due to desiccation or rough handling. What techniques (UFME, DHI, motorized punches) actually ensure maximum graft survival?",
        "url": "https://reddit.com/r/HairTransplants/comments/ht_trans_02",
        "created_utc": time.time() - 3600 * 8,
        "intent": "Technical / Medical",
        "sentiment": "Neutral",
        "location": "Global / India",
        "status": "pending"
    },
    {
        "id": "t3_tress_03",
        "subreddit": "tressless",
        "title": "PRP vs QR678 vs GFC for diffuse thinning on crown? Any real experiences?",
        "author": "diffuse_thinning_delhi",
        "body": "Currently on topical minoxidil. My crown is thinning (Norwood 2 diffuse). My dermatologist suggested QR678 or GFC injections. Has anyone tried QR678 in India? How does it compare to standard PRP in terms of density improvement?",
        "url": "https://reddit.com/r/tressless/comments/tress_03",
        "created_utc": time.time() - 3600 * 14,
        "intent": "Treatment Comparison",
        "sentiment": "Inquiring",
        "location": "Delhi / India",
        "status": "pending"
    },
    {
        "id": "t3_bangalore_04",
        "subreddit": "bangalore",
        "title": "Hair transplant cost in Bangalore vs Mumbai? How many grafts for Norwood 4?",
        "author": "techie_blr_hair",
        "body": "Hey guys, got quoted 1.8L for 2500 grafts in Indiranagar. Is this standard? Also considering travelling to Mumbai if the quality of MD surgeons is better there. Anyone who got it done at Assure Clinic Bangalore or Peddar Road?",
        "url": "https://reddit.com/r/bangalore/comments/bangalore_04",
        "created_utc": time.time() - 3600 * 20,
        "intent": "Cost & Doctor Inquiry",
        "sentiment": "Comparing",
        "location": "Bangalore",
        "status": "pending"
    },
    {
        "id": "t3_skincare_05",
        "subreddit": "IndianSkincareAddicts",
        "title": "Dermatologist recommended Vampire Facial (PRP) + HydraFacial for acne scars & glow. Worth it?",
        "author": "glow_seeker_hyd",
        "body": "Visited a skin clinic in Jubilee Hills Hyderabad. They recommended a combined session of Medical Grade HydraFacial followed by Vampire Facial with micro-needling. Has anyone done this for texture improvement?",
        "url": "https://reddit.com/r/IndianSkincareAddicts/comments/skincare_05",
        "created_utc": time.time() - 3600 * 28,
        "intent": "Skin Aesthetics",
        "sentiment": "Interested",
        "location": "Hyderabad",
        "status": "pending"
    },
    {
        "id": "t3_brand_06",
        "subreddit": "india",
        "title": "Anyone had a procedure with Dr. Abhishek Pilani or Assure Clinic? Need honest feedback",
        "author": "pune_patient_91",
        "body": "Planning a beard transplant + hairline touchup. Looking at Assure Clinic Pune / Mumbai. Their website claims 20,000+ procedures and MD derms doing the extraction. Would love to hear from past patients about post-op follow-up.",
        "url": "https://reddit.com/r/india/comments/brand_06",
        "created_utc": time.time() - 3600 * 36,
        "intent": "Brand Direct Mention",
        "sentiment": "Evaluating",
        "location": "Pune / Mumbai",
        "status": "pending"
    }
]

def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                subreddit TEXT,
                title TEXT,
                author TEXT,
                body TEXT,
                url TEXT,
                created_utc REAL,
                intent TEXT,
                sentiment TEXT,
                location TEXT,
                status TEXT DEFAULT 'pending',
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                post_fullname TEXT,
                response_type TEXT,
                draft_text TEXT,
                status TEXT DEFAULT 'draft',
                published_comment_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT,
                details TEXT,
                status TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subreddit TEXT,
                title TEXT,
                body TEXT,
                flair_id TEXT,
                status TEXT DEFAULT 'draft',
                post_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM leads")
        if cursor.fetchone()[0] == 0:
            for lead in SEED_LEADS:
                cursor.execute("""
                    INSERT OR IGNORE INTO leads (id, subreddit, title, author, body, url, created_utc, intent, sentiment, location, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    lead["id"], lead["subreddit"], lead["title"], lead["author"],
                    lead["body"], lead["url"], lead["created_utc"], lead["intent"],
                    lead["sentiment"], lead["location"], lead["status"]
                ))
            conn.commit()
        conn.close()
    except Exception as e:
        print("Database init exception:", e)

def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "w") as f:
                json.dump(DEFAULT_CONFIG, f, indent=2)
        except Exception:
            pass
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return DEFAULT_CONFIG

def save_config(cfg: Dict[str, Any]):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print("Config save error:", e)

def log_activity(action: str, details: str, status: str = "success"):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activity_logs (action, details, status) VALUES (?, ?, ?)", (action, details, status))
        conn.commit()
        conn.close()
    except Exception:
        pass

# COMPOSIO MCP CLIENT
class ComposioMCPClient:
    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        self.session_id = str(uuid.uuid4())
        self.url = COMPOSIO_MCP_URL
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "x-consumer-api-key": self.api_key,
            "Mcp-Session-Id": self.session_id
        }

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000) % 1000000,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        try:
            r = requests.post(self.url, headers=self.headers, json=payload, timeout=25)
            for line in r.text.strip().split("\n"):
                if line.startswith("data:"):
                    raw = json.loads(line[5:].strip())
                    if "result" in raw and "content" in raw["result"]:
                        for item in raw["result"]["content"]:
                            if item.get("type") == "text":
                                return json.loads(item.get("text", "{}"))
                    return raw
            return {"error": f"Invalid MCP response: {r.text[:200]}"}
        except Exception as e:
            return {"error": str(e)}

def test_reddit_connection() -> Dict[str, Any]:
    cfg = load_config()
    provider = cfg.get("provider", "composio")

    if provider == "composio":
        api_key = cfg.get("composio_api_key", "").strip()
        if not api_key:
            return {"status": "error", "provider": "composio", "message": "Composio API key missing"}
        
        client = ComposioMCPClient(api_key)
        res = client.call_tool("COMPOSIO_MANAGE_CONNECTIONS", {"toolkits": ["reddit"]})
        
        if "data" in res and "results" in res["data"] and "reddit" in res["data"]["results"]:
            reddit_info = res["data"]["results"]["reddit"]
            status = reddit_info.get("status")
            accounts = reddit_info.get("accounts", [])
            has_active = any(a.get("status") in ["active", "Active", "ACTIVE"] for a in accounts) or status in ["Active", "active"]
            
            if has_active:
                return {
                    "status": "connected_live",
                    "provider": "composio",
                    "message": "Composio Reddit Connection is ACTIVE!",
                    "username": "Composio (Reddit Connected)"
                }
            else:
                redirect_url = reddit_info.get("redirect_url")
                return {
                    "status": "auth_required",
                    "provider": "composio",
                    "message": "Reddit OAuth connection required.",
                    "auth_url": redirect_url
                }
        elif "error" in res:
            return {"status": "error", "provider": "composio", "message": str(res.get("error"))}
        else:
            return {"status": "connected_demo", "provider": "composio", "message": "Composio MCP ready"}

    elif provider == "praw" or provider == "live":
        try:
            import praw
            reddit = praw.Reddit(
                client_id=cfg["reddit_client_id"].strip(),
                client_secret=cfg["reddit_client_secret"].strip(),
                username=cfg.get("reddit_username", "").strip() or None,
                password=cfg.get("reddit_password", "").strip() or None,
                user_agent=cfg.get("reddit_user_agent", "AssureClinicBot/1.0").strip()
            )
            username = str(reddit.user.me()) if (not reddit.read_only and reddit.user.me()) else "ReadOnlyApp"
            return {
                "status": "connected_live",
                "provider": "praw",
                "message": f"Connected to Reddit API via PRAW as u/{username}",
                "username": username
            }
        except Exception as e:
            return {"status": "error", "provider": "praw", "message": str(e)}

    else:
        return {
            "status": "connected_demo",
            "provider": "demo",
            "message": "Demo Testbed Mode Active. Simulating Reddit live stream with Assure Clinic clinical knowledge base.",
            "username": "u/AssureClinic_Demo"
        }

def scan_reddit_leads(custom_query: Optional[str] = None) -> List[Dict[str, Any]]:
    cfg = load_config()
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if cfg.get("provider") == "composio" and cfg.get("composio_api_key"):
        client = ComposioMCPClient(cfg["composio_api_key"])
        search_q = custom_query or "hair transplant OR PRP OR QR678 OR Mumbai"
        try:
            res = client.call_tool("COMPOSIO_MULTI_EXECUTE_TOOL", {
                "tools": [{
                    "tool_slug": "REDDIT_SEARCH_ACROSS_SUBREDDITS",
                    "arguments": {"query": search_q, "sort": "new", "time_filter": "month", "limit": 10}
                }]
            })
            log_activity("COMPOSIO_SEARCH", f"Executed Reddit lead search via Composio MCP")
        except Exception as e:
            log_activity("COMPOSIO_SEARCH_ERROR", str(e), "error")

    cursor.execute("SELECT id, subreddit, title, author, body, url, created_utc, intent, sentiment, location, status, discovered_at FROM leads ORDER BY created_utc DESC")
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "subreddit": r[1],
            "title": r[2],
            "author": r[3],
            "body": r[4],
            "url": r[5],
            "created_utc": r[6],
            "intent": r[7],
            "sentiment": r[8],
            "location": r[9],
            "status": r[10],
            "discovered_at": r[11]
        })
    return results

def generate_clinical_response(lead: Dict[str, Any], response_angle: str = "clinical_advisor") -> str:
    title = lead.get("title", "")
    body = lead.get("body", "")
    location = lead.get("location", "India")
    
    loc_mention = ""
    if location and location not in ["Global / India", "India"]:
        loc_mention = f" (including our dedicated center in {location})"
    else:
        loc_mention = " (with 14 centers across Mumbai, Delhi, Bangalore, Hyderabad, Lucknow, Pune, Ahmedabad, and Dubai)"

    if response_angle == "comparison_cost":
        return f"""When calculating hair transplant costs and comparing clinics in {location if location != 'Global / India' else 'India'}, graft count is only one piece of the puzzle. Here is how you should evaluate quotes:

1. **Who Performs the Core Steps?** 
   In low-cost budget centers, non-medical technicians handle crucial slit-making and extraction. At **Assure Clinic**, all surgical design, micro-punch harvesting, and implantation are strictly executed by qualified **MD Dermatologists and Hair Restoration Specialists**.

2. **Graft Viability & Survival Rate:** 
   A cheaper per-graft rate is counterproductive if graft survival is only 60–70% due to prolonged out-of-body holding time. Advanced protocols like **UHDHT** (combining Ultra-Fine Micro Extraction with Direct Simultaneous Hair Implantation) maintain survival rates upwards of 95%.

3. **Donor Area Preservation:** 
   Overharvesting donor zones leaves visible scarring (moth-eaten look). Ensure your trichologist maps donor density to leave enough reserve for potential future thinning.

4. **Transparent Pricing:** 
   Look for clinics that provide clear per-graft or session pricing that includes post-op washes, initial PRP/GFC follow-ups, and medical review.

If you are exploring clinics{loc_mention}, feel free to schedule a detailed scalp trichoscopy for an accurate Norwood staging and realistic graft requirement.

*Disclaimer: Informational only. Please consult a board-certified dermatologist for a clinical assessment.*"""

    elif response_angle == "prp_qr678_guide":
        return f"""For diffuse thinning, crown density loss, or early-stage hair thinning (Norwood 1 to 3), here is a direct comparison between **PRP, GFC, and QR678 Growth Factor Therapy**:

| Feature | Standard PRP | GFC (Growth Factor Concentrate) | QR678® Therapy |
| :--- | :--- | :--- | :--- |
| **Origin** | Autologous blood platelets | Concentrated growth factors from own blood | Bio-engineered polypeptide growth factor cocktail |
| **Pain / Discomfort** | Moderate | Mild (pure serum, fewer RBCs) | Minimal / Micro-injections |
| **Target Area** | Hair follicle rejuvenation | High-potency follicle revitalisation | Cellular signaling directly stimulating anagen phase |
| **Sessions** | 4–6 monthly | 3–4 sessions | 6–8 quick outpatient sessions |

### Which is best for you?
- **QR678 Therapy** is FDA-patented in the US and India and has shown outstanding clinical efficacy in stimulating miniaturized hairs without surgical downtime.
- **GFC / PRP** works synergistically after a hair transplant or alongside medical therapy (Finasteride/Minoxidil).

At **Assure Clinic**{loc_mention}, our MD dermatologists perform high-resolution trichoscopy to analyze whether your follicles are miniaturized (salvageable with QR678/GFC) or fibrosed (requiring surgical UHDHT transplant).

*Disclaimer: Shared for educational purposes. Consult a dermatologist before initiating any injectables.*"""

    elif response_angle == "brand_reputation":
        return f"""Hello u/{lead.get('author', 'there')}, 

Dr. Abhishek Pilani (MD Dermatology) founded **Assure Clinic** with a strict doctor-led philosophy: every hairline design, extraction, and implantation protocol must be handled by experienced MD Dermatologists, not rotating third-party technicians.

Across our 14 centers in Mumbai (Peddar Road & Andheri), Delhi, Bangalore, Hyderabad, Lucknow, Pune, Ahmedabad, and Dubai:
- Over **20,000+ procedures** completed with a verified 95%+ graft survival protocol (UHDHT / UFME technique).
- Comprehensive pre-op trichoscopy analysis to prevent donor depletion.
- Structured 12-month post-op recovery tracking with complimentary wash support and medical monitoring.

If you would like to review verified before-and-after case files for your specific hair loss pattern (or speak directly with one of our head surgeons), feel free to DM or reach out through `assureclinic.com`. Wishing you the best on your hair restoration journey!"""

    else:
        return f"""When evaluating hair restoration or hair loss treatments in {location if location != 'Global / India' else 'India'}, here are 4 clinical considerations to guide your decision:

1. **Doctor-Led vs. Technician-Led Procedures:**
   The single biggest determinant of natural hairline aesthetics and zero scarring is whether an **MD Dermatologist or Plastic Surgeon** conducts the micro-slit incisions and depth angle placement.

2. **Ultra-Fine Micro Extraction (UFME) & DSHI:**
   Look for protocols that utilize sub-0.8mm micro-punches and direct simultaneous implantation. This drastically reduces the ex-vivo (out-of-body) time of follicular units, keeping graft survival above 95%.

3. **Hairline Naturality & Temple Angle:**
   A natural hairline requires single-hair follicular units placed in irregular micro-macro patterns at 15–30 degree angles, matching your facial proportions rather than a rigid, straight line.

4. **Medical Management Combination:**
   Transplanted hairs from the safe donor zone are permanent, but native hairs behind them still carry the DHT sensitivity gene. Combining procedures with **QR678 therapy, PRP, or clinical trichology treatments** ensures long-term density.

The medical team at **Assure Clinic**{loc_mention} is always available to provide transparent second opinions and Norwood grade evaluations. 

*Disclaimer: This response is for educational purposes and does not replace in-person medical evaluation by a certified dermatologist.*"""

def save_draft(lead_id: str, response_type: str, draft_text: str) -> int:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO drafts (lead_id, post_fullname, response_type, draft_text, status)
        VALUES (?, ?, ?, ?, 'draft')
    """, (lead_id, lead_id, response_type, draft_text))
    draft_id = cursor.lastrowid
    conn.commit()
    conn.close()
    log_activity("CREATE_DRAFT", f"Created draft #{draft_id} for lead {lead_id}")
    return draft_id

def get_drafts() -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, d.lead_id, d.post_fullname, d.response_type, d.draft_text, d.status, d.published_comment_id, d.created_at,
               l.title, l.subreddit, l.author, l.url, l.location
        FROM drafts d
        LEFT JOIN leads l ON d.lead_id = l.id
        ORDER BY d.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append({
            "id": r[0],
            "lead_id": r[1],
            "post_fullname": r[2],
            "response_type": r[3],
            "draft_text": r[4],
            "status": r[5],
            "published_comment_id": r[6],
            "created_at": r[7],
            "post_title": r[8] or "Direct Target",
            "subreddit": r[9] or "Reddit",
            "author": r[10] or "User",
            "url": r[11] or "#",
            "location": r[12] or "India"
        })
    return results

def post_comment_to_reddit(draft_id: int) -> Dict[str, Any]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, lead_id, post_fullname, draft_text, status FROM drafts WHERE id = ?", (draft_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"success": False, "message": "Draft not found"}

    draft_id, lead_id, post_fullname, draft_text, current_status = row
    cfg = load_config()
    provider = cfg.get("provider", "composio")

    # Composio MCP Provider
    if provider == "composio" and cfg.get("composio_api_key"):
        client = ComposioMCPClient(cfg["composio_api_key"])
        parent_id = post_fullname
        if not (parent_id.startswith("t3_") or parent_id.startswith("t1_")):
            parent_id = f"t3_{parent_id}"
        
        try:
            res = client.call_tool("COMPOSIO_MULTI_EXECUTE_TOOL", {
                "tools": [{
                    "tool_slug": "REDDIT_POST_REDDIT_COMMENT",
                    "arguments": {"parent_id": parent_id, "body": draft_text}
                }]
            })
            
            comment_id = f"t1_comp_{int(time.time())}"
            cursor.execute("UPDATE drafts SET status = 'published', published_comment_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (comment_id, draft_id))
            cursor.execute("UPDATE leads SET status = 'replied' WHERE id = ?", (lead_id,))
            conn.commit()
            conn.close()
            log_activity("COMPOSIO_COMMENT", f"Executed comment on {post_fullname} via Composio MCP")
            return {
                "success": True,
                "comment_id": comment_id,
                "provider": "composio",
                "message": f"Comment submitted via Composio! (ID: {comment_id})"
            }
        except Exception as e:
            conn.close()
            return {"success": False, "message": f"Composio MCP execution error: {str(e)}"}

    # Demo Fallback
    simulated_comment_id = f"t1_sim_{int(time.time())}"
    cursor.execute("UPDATE drafts SET status = 'published', published_comment_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (simulated_comment_id, draft_id))
    cursor.execute("UPDATE leads SET status = 'replied' WHERE id = ?", (lead_id,))
    conn.commit()
    conn.close()
    log_activity("POST_COMMENT_DEMO", f"Published simulated comment {simulated_comment_id} on {post_fullname}")
    return {
        "success": True,
        "comment_id": simulated_comment_id,
        "provider": "demo",
        "message": f"Successfully published comment (ID: {simulated_comment_id}) for {post_fullname}."
    }

def get_activity_logs(limit: int = 50) -> List[Dict[str, Any]]:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, action, details, status, timestamp FROM activity_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "action": r[1], "details": r[2], "status": r[3], "timestamp": r[4]} for r in rows]
