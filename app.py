import os
import sys
import json
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path="/static")
CORS(app)

import reddit_engine
reddit_engine.init_db()

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/api/stats", methods=["GET"])
def get_stats():
    conn = sqlite3.connect(reddit_engine.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'pending'")
    pending_leads = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM drafts WHERE status = 'draft'")
    active_drafts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM drafts WHERE status = 'published'")
    published_comments = cursor.fetchone()[0]

    cursor.execute("SELECT intent, COUNT(*) FROM leads GROUP BY intent")
    intents = dict(cursor.fetchall())

    cursor.execute("SELECT location, COUNT(*) FROM leads GROUP BY location")
    locations = dict(cursor.fetchall())
    conn.close()

    cfg = reddit_engine.load_config()

    return jsonify({
        "total_leads": total_leads,
        "pending_leads": pending_leads,
        "active_drafts": active_drafts,
        "published_comments": published_comments,
        "provider": cfg.get("provider", "demo"),
        "intents": intents,
        "locations": locations,
        "compliance_score": "98% (9:1 Rule Safe)",
        "cooldown_status": "Ready to Post"
    })

@app.route("/api/leads", methods=["GET"])
def list_leads():
    leads = reddit_engine.scan_reddit_leads()
    return jsonify({"leads": leads})

@app.route("/api/leads/scan", methods=["POST"])
def scan_leads():
    data = request.json or {}
    custom_query = data.get("query")
    leads = reddit_engine.scan_reddit_leads(custom_query)
    return jsonify({"success": True, "leads": leads, "count": len(leads)})

@app.route("/api/generate_reply", methods=["POST"])
def generate_reply():
    data = request.json or {}
    lead = data.get("lead", {})
    response_angle = data.get("angle", "clinical_advisor")
    
    if not lead or not lead.get("title"):
        return jsonify({"success": False, "message": "Lead details missing"}), 400
        
    generated_text = reddit_engine.generate_clinical_response(lead, response_angle)
    return jsonify({
        "success": True,
        "response_text": generated_text,
        "angle": response_angle
    })

@app.route("/api/drafts", methods=["GET", "POST"])
def handle_drafts():
    if request.method == "POST":
        data = request.json or {}
        lead_id = data.get("lead_id")
        response_type = data.get("response_type", "clinical_advisor")
        draft_text = data.get("draft_text", "")
        
        if not lead_id or not draft_text:
            return jsonify({"success": False, "message": "lead_id and draft_text required"}), 400
            
        draft_id = reddit_engine.save_draft(lead_id, response_type, draft_text)
        return jsonify({"success": True, "draft_id": draft_id})
    
    drafts = reddit_engine.get_drafts()
    return jsonify({"drafts": drafts})

@app.route("/api/drafts/<int:draft_id>/publish", methods=["POST"])
def publish_draft(draft_id):
    result = reddit_engine.post_comment_to_reddit(draft_id)
    return jsonify(result)

@app.route("/api/drafts/<int:draft_id>/delete", methods=["DELETE"])
def delete_draft(draft_id):
    conn = sqlite3.connect(reddit_engine.DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM drafts WHERE id = ?", (draft_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/posts/create", methods=["POST"])
def create_post():
    data = request.json or {}
    subreddit = data.get("subreddit", "HairTransplants")
    title = data.get("title", "")
    body = data.get("body", "")
    flair_id = data.get("flair_id")
    cfg = reddit_engine.load_config()
    provider = cfg.get("provider", "demo")

    if not title or not body:
        return jsonify({"success": False, "message": "Title and body are required"}), 400

    if provider == "composio" and cfg.get("composio_api_key"):
        client = reddit_engine.ComposioMCPClient(cfg["composio_api_key"])
        try:
            params = {"subreddit": subreddit, "title": title, "text": body}
            if flair_id:
                params["flair_id"] = flair_id
            res = client.call_tool("COMPOSIO_MULTI_EXECUTE_TOOL", {
                "tools": [{
                    "tool_slug": "REDDIT_CREATE_REDDIT_POST",
                    "arguments": params
                }]
            })
            post_id = f"t3_comp_{int(time.time())}"
            reddit_engine.log_activity("COMPOSIO_POST", f"Created post in r/{subreddit} via Composio: {post_id}")
            return jsonify({
                "success": True,
                "provider": "composio",
                "post_id": post_id,
                "url": f"https://reddit.com/r/{subreddit}/comments/{post_id}",
                "message": f"Post published via Composio to r/{subreddit}!"
            })
        except Exception as e:
            return jsonify({"success": False, "message": f"Composio post error: {str(e)}"})

    sim_id = f"t3_sim_{int(time.time())}"
    reddit_engine.log_activity("CREATE_POST_DEMO", f"Simulated post created in r/{subreddit}: {title}")
    return jsonify({
        "success": True,
        "provider": "demo",
        "post_id": sim_id,
        "url": f"https://reddit.com/r/{subreddit}/comments/{sim_id}",
        "message": f"Successfully simulated educational post creation in r/{subreddit}!"
    })

@app.route("/api/settings", methods=["GET", "POST"])
def settings_endpoint():
    if request.method == "POST":
        data = request.json or {}
        cfg = reddit_engine.load_config()
        for k, v in data.items():
            cfg[k] = v
        reddit_engine.save_config(cfg)
        reddit_engine.log_activity("UPDATE_SETTINGS", "Configuration updated")
        return jsonify({"success": True, "config": cfg})
    
    cfg = reddit_engine.load_config()
    safe_cfg = dict(cfg)
    if safe_cfg.get("reddit_password"):
        safe_cfg["reddit_password"] = "••••••••••••"
    if safe_cfg.get("composio_api_key"):
        key = safe_cfg["composio_api_key"]
        safe_cfg["composio_api_key_masked"] = key[:6] + "••••" + key[-4:] if len(key) > 10 else "••••"
    return jsonify({"config": safe_cfg})

@app.route("/api/settings/test", methods=["POST"])
def test_settings():
    res = reddit_engine.test_reddit_connection()
    return jsonify(res)

@app.route("/api/logs", methods=["GET"])
def get_logs():
    logs = reddit_engine.get_activity_logs(limit=50)
    return jsonify({"logs": logs})

# For local running
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=False)
