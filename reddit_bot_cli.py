#!/usr/bin/env python3
"""
Standalone CLI Runner for Assure Clinic Reddit Automation
Can be executed via terminal, background worker, or cron.
"""

import sys
import time
import argparse
import reddit_engine

def run_scan():
    print("==================================================")
    print("  ASSURE CLINIC REDDIT AUTOMATION ENGINE (CLI)")
    print("==================================================")
    cfg = reddit_engine.load_config()
    print(f"[*] Operating Mode: {cfg.get('mode', 'demo').upper()}")
    print("[*] Scanning target subreddits for high-intent hair & aesthetic discussions...")
    
    leads = reddit_engine.scan_reddit_leads()
    print(f"[+] Total Leads Found: {len(leads)}")
    print("--------------------------------------------------")
    for i, lead in enumerate(leads[:5], 1):
        print(f"[{i}] r/{lead['subreddit']} | {lead['location']} | {lead['intent']}")
        print(f"    Title: {lead['title']}")
        print(f"    Fullname: {lead['id']} | Author: u/{lead['author']}")
        print("--------------------------------------------------")

def run_auto_responder():
    print("[*] Checking for unanswered leads to draft responses...")
    leads = reddit_engine.scan_reddit_leads()
    unanswered = [l for l in leads if l.get('status') == 'pending']
    
    print(f"[*] Found {len(unanswered)} unanswered leads.")
    for lead in unanswered:
        print(f"\n[+] Generating clinical response for: {lead['title'][:50]}...")
        reply_text = reddit_engine.generate_clinical_response(lead, "clinical_advisor")
        draft_id = reddit_engine.save_draft(lead['id'], "clinical_advisor", reply_text)
        print(f"    -> Saved as Draft #{draft_id}")
        
        cfg = reddit_engine.load_config()
        if cfg.get('auto_approve'):
            print(f"    -> Auto-approve enabled. Submitting response to Reddit...")
            res = reddit_engine.post_comment_to_reddit(draft_id)
            print(f"    -> Result: {res.get('message')}")
            time.sleep(cfg.get('min_reply_interval_minutes', 12) * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Assure Clinic Reddit Automation CLI")
    parser.add_argument("--scan", action="store_true", help="Scan subreddits for leads")
    parser.add_argument("--respond", action="store_true", help="Generate drafts / auto-respond to leads")
    parser.add_argument("--test", action="store_true", help="Test Reddit API connection")
    
    args = parser.parse_args()
    
    if args.test:
        res = reddit_engine.test_reddit_connection()
        print("[*] Connection Status:", res)
    elif args.respond:
        run_auto_responder()
    else:
        run_scan()
