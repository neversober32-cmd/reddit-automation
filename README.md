# Assure Clinic — Reddit Automation & Lead Command Center

A full-stack, doctor-led Reddit automation and patient discovery engine tailored specifically for **Assure Clinic** (`assureclinic.com`).

---

## 🌟 Overview & Capabilities

1. **Lead Radar & Discovery**:
   - Continuously scans target hair restoration and city subreddits (`r/HairTransplants`, `r/tressless`, `r/IndianSkincareAddicts`, `r/mumbai`, `r/delhi`, `r/bangalore`, `r/hyderabad`, `r/pune`, `r/lucknow`, `r/ahmedabad`, `r/Dubai`).
   - Classifies post intent (High Commercial Intent, Cost & Doctor Inquiry, Treatment Comparison, Brand Mentions, Skin Aesthetics).
   
2. **AI Medical Response Studio**:
   - Generates contextual, dermatologically verified responses anchored in Assure Clinic’s clinical USPs:
     - **MD Dermatologist Leadership**: Surgeries performed strictly by qualified MD doctors, not technicians.
     - **UHDHT Protocol**: Combining sub-0.8mm Ultra-Fine Micro Extraction (UFME) with Direct Simultaneous Hair Implantation (DSHI).
     - **95%+ Graft Survival Safeguard**: Minimizing out-of-body holding time.
     - **Full Clinic Network**: 14 centers across Mumbai (Peddar Road & Andheri), Delhi, Bangalore, Hyderabad, Lucknow, Pune, Ahmedabad, and Dubai.
     - **Non-Surgical Treatments**: Patented QR678® Therapy, Autologous PRP, GFC, Beard & Eyebrow restoration.
   - 4 pre-configured response angles: *MD Doctor Advice*, *Cost & Quality Matrix*, *QR678 vs PRP / GFC*, and *Assure Brand Verification*.

3. **Publishing Queue & Rate Limiting Guard**:
   - Enforces Reddit's **9:1 Value-to-Promotion Rule**.
   - Supports both one-click approval and automated scheduling.
   - Resolves Reddit Fullnames (`t3_...` for posts, `t1_...` for comments).

4. **Educational Post Builder**:
   - Pre-loaded with long-form guides on *Graft Survival Math* and *Hairline Aesthetic Design Rules*.

---

## 🚀 How to Run & Operate

### 1. Interactive Live Web Dashboard (Active)
The Web UI is running live on port `8000`:
- Open the live preview panel in your browser.
- Browse live leads, generate replies, test publishing, and configure Reddit credentials.

### 2. Standalone CLI Runner
You can also run automated scans or response jobs via the terminal:

```bash
# Scan subreddits for high-intent discussions
python3 reddit_bot_cli.py --scan

# Test Reddit API connection
python3 reddit_bot_cli.py --test

# Generate response drafts and auto-respond (if enabled)
python3 reddit_bot_cli.py --respond
```

---

## ⚙️ Connecting to Live Reddit API or Rube MCP

### Option A: Reddit Official API (PRAW)
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) and create a "script" application.
2. Open the **API & Rube MCP Settings** tab in the dashboard.
3. Enter your `client_id`, `client_secret`, `username`, and `password`.
4. Toggle mode to **Live Reddit API** and click **Save Configuration**.

### Option B: Rube MCP / Composio Endpoint
If using Claude Desktop, Cursor, Cline, or Windsurf:
1. Add `https://rube.app/mcp` to your MCP configuration file.
2. Connect Reddit via `RUBE_MANAGE_CONNECTIONS` with toolkit slug `reddit`.
3. Use the standardized tool calls (`REDDIT_SEARCH_ACROSS_SUBREDDITS`, `REDDIT_POST_REDDIT_COMMENT`, `REDDIT_CREATE_REDDIT_POST`).
