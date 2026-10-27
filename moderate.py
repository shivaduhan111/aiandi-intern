#!/usr/bin/env python3
"""
AI Comment Moderator Pipeline using Cloudflare Workers AI Clef API.
Processes student forum comments from comments.json or comments-v2.json,
classifies them into designated categories, and exports an interactive HTML report.

Usage:
    python moderate.py        # Process comments.json using clef-flash -> results.html
    python moderate.py --v2   # Process comments-v2.json using clef -> results-v2.html
    python moderate.py --help # View additional options
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

CATEGORIES_V1 = {
    "spam": "Promotional messages, paid assignment help services, spam links, commercial offers, or unrelated advertising.",
    "abusive": "Personal attacks, insults, harassment, disrespectful language, or hostile remarks targeting peers or instructors.",
    "off-topic": "Comments unrelated to the course topic, assignment, or technical discussion (e.g. random chatter, casual social talk).",
    "constructive": "Constructive feedback, substantive technical suggestions, identifying bugs, sharing helpful tips, or practical workflow advice.",
    "praise": "Compliments, expressions of appreciation, gratitude, or encouragement towards peers, instructors, or course material without substantive technical feedback.",
    "question/help-needed": "Asking for technical help, clarification on assignments, doubts about tools/access, or administrative queries."
}

CATEGORIES_V2 = {
    "spam": "Commercial promotions, paid assignment help, ready-made solutions for sale, fake account deals, referral links, or academic dishonesty services.",
    "abusive": "Direct insults, harassment, hostile personal attacks, mocking, toxic derogatory remarks directed at peers, teachers, or groups. Does NOT include mere self-criticism or polite disagreement.",
    "off-topic": "Discussions completely unrelated to the course, assignment, or learning material (e.g. general chit-chat, personal banter, off-topic memes).",
    "constructive": "Substantive peer feedback, sharing technical tips, suggestions for improvement, edge-case bug catches, workflow advice, or helpful answers and clarifications provided to peers.",
    "praise": "Positive feedback, compliments, words of appreciation, gratitude, or encouragement towards peers, instructors, or student artifacts.",
    "question/help-needed": "Asking for technical help, doubts about assignments, tools, APIs, deadlines, access issues, or administrative clarifications."
}


def load_credentials(creds_path="cloud-flare.local.sh"):
    if not os.path.exists(creds_path):
        raise FileNotFoundError(
            f"Credentials file '{creds_path}' not found.\n"
            f"Please run: cp cloud-flare.sh cloud-flare.local.sh\n"
            f"and insert your Cloudflare Account ID and API Token."
        )

    with open(creds_path, "r", encoding="utf-8") as f:
        content = f.read()

    creds = dict(re.findall(r'export (\w+)="([^"]*)"', content))
    account_id = creds.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    api_token = creds.get("CLOUDFLARE_API_TOKEN", "").strip()

    if not account_id or account_id.startswith("0123456789"):
        raise ValueError(
            f"Invalid CLOUDFLARE_ACCOUNT_ID in '{creds_path}'. Please set your actual Cloudflare Account ID."
        )
    if not api_token or "your-cloudflare-api-token" in api_token:
        raise ValueError(
            f"Invalid CLOUDFLARE_API_TOKEN in '{creds_path}'. Please set your actual Cloudflare API Token."
        )

    return account_id, api_token


def call_clef_api(account_id, api_token, model, comment_text, criteria, max_retries=5):
    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/cloudflare/{model}"
    
    payload = {
        "state": {
            "comment": comment_text
        },
        "questions": {
            "category": {
                "type": "choice",
                "instructions": (
                    "Classify `comment`, a message posted by a student or participant in an online computer science "
                    "course discussion forum. Select the single best matching category based on the criteria provided."
                ),
                "criteria": criteria
            }
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    )

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)

            if not data.get("success", False):
                errors = data.get("errors", [])
                raise RuntimeError(f"API Error from Cloudflare: {errors}")

            answer = data["result"]["answers"]["category"]
            return {
                "choice": answer.get("choice", "unknown"),
                "confidence": answer.get("confidence", 0.0),
                "probabilities": answer.get("probabilities", {}),
                "usage": data.get("result", {}).get("usage", {})
            }

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = (2 ** attempt) * 1.5
                print(f"    [Rate limit 429] Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            elif e.code in (500, 502, 503, 504):
                wait_time = (2 ** attempt) * 1.0
                print(f"    [Server error {e.code}] Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
                time.sleep(wait_time)
            else:
                body = e.read().decode("utf-8", errors="ignore")
                raise RuntimeError(f"HTTP {e.code} Error: {body}")
        except urllib.error.URLError as e:
            wait_time = (2 ** attempt) * 1.0
            print(f"    [Network error: {e}] Waiting {wait_time:.1f}s before retry {attempt + 1}/{max_retries}...")
            time.sleep(wait_time)

    raise RuntimeError(f"Failed to classify comment after {max_retries} attempts.")


def generate_html_report(results, output_path, dataset_name, model_name, course_info):
    total = len(results)
    cat_counts = {}
    total_conf = 0.0

    for r in results:
        cat = r["classification"]["choice"]
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        total_conf += r["classification"]["confidence"]

    avg_conf = (total_conf / total) if total > 0 else 0.0

    badge_colors = {
        "spam": {"bg": "#fee2e2", "text": "#991b1b", "border": "#f87171"},
        "abusive": {"bg": "#ffe4e6", "text": "#881337", "border": "#fb7185"},
        "off-topic": {"bg": "#f3f4f6", "text": "#374151", "border": "#9ca3af"},
        "constructive": {"bg": "#dcfce7", "text": "#166534", "border": "#4ade80"},
        "praise": {"bg": "#e0e7ff", "text": "#3730a3", "border": "#818cf8"},
        "question/help-needed": {"bg": "#fef3c7", "text": "#92400e", "border": "#fbbf24"},
        "unknown": {"bg": "#e5e7eb", "text": "#1f2937", "border": "#d1d5db"}
    }

    cards_html = []
    for r in results:
        cid = r["id"]
        author = html.escape(str(r.get("author", "Anonymous")))
        thread = html.escape(str(r.get("thread", "General")))
        posted_at = html.escape(str(r.get("posted_at", "")))
        comment_text = html.escape(str(r.get("comment", "")))
        
        c_info = r["classification"]
        choice = c_info.get("choice", "unknown")
        confidence = c_info.get("confidence", 0.0)
        probs = c_info.get("probabilities", {})
        
        badge_style = badge_colors.get(choice, badge_colors["unknown"])
        
        prob_pills = []
        for p_cat, p_val in sorted(probs.items(), key=lambda x: x[1], reverse=True):
            pct = p_val * 100
            prob_pills.append(
                f'<span class="prob-pill" title="{pct:.1f}%">{html.escape(p_cat)}: {pct:.1f}%</span>'
            )
        prob_html = " ".join(prob_pills)
        
        cards_html.append(f"""
        <div class="comment-card" data-category="{html.escape(choice)}" data-confidence="{confidence:.4f}" data-id="{cid}">
            <div class="card-header">
                <div class="meta-left">
                    <span class="comment-id">#{cid}</span>
                    <strong class="author-name">{author}</strong>
                    <span class="thread-badge">{thread}</span>
                    <span class="timestamp">{posted_at}</span>
                </div>
                <div class="meta-right">
                    <span class="category-badge" style="background:{badge_style['bg']}; color:{badge_style['text']}; border: 1px solid {badge_style['border']};">
                        {html.escape(choice)}
                    </span>
                    <span class="confidence-tag">Conf: {(confidence * 100):.1f}%</span>
                </div>
            </div>
            <div class="comment-body">
                {comment_text}
            </div>
            <div class="card-footer">
                <div class="confidence-bar-bg">
                    <div class="confidence-bar-fill" style="width: {min(100, max(5, int(confidence * 100)))}%;"></div>
                </div>
                <div class="prob-distribution">
                    <small><strong>Distribution:</strong></small> {prob_html}
                </div>
            </div>
        </div>
        """)

    metric_pills = [f'<span class="stat-pill"><strong>Total:</strong> {total}</span>',
                    f'<span class="stat-pill"><strong>Avg Conf:</strong> {(avg_conf * 100):.1f}%</span>']
    for cat, count in sorted(cat_counts.items(), key=lambda x: x[1], reverse=True):
        metric_pills.append(f'<span class="stat-pill"><strong>{html.escape(cat)}:</strong> {count}</span>')

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clef Moderation Report - {html.escape(dataset_name)}</title>
    <style>
        :root {{
            --bg-color: #f8fafc;
            --card-bg: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --primary: #2563eb;
            --primary-light: #dbeafe;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-color);
            color: var(--text-main);
            padding: 24px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1040px;
            margin: 0 auto;
        }}
        header {{
            margin-bottom: 24px;
            background: var(--card-bg);
            padding: 24px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        h1 {{
            font-size: 1.6rem;
            font-weight: 700;
            color: #1e293b;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: var(--text-muted);
            font-size: 0.95rem;
            margin-bottom: 16px;
        }}
        .stats-bar {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin-top: 12px;
        }}
        .stat-pill {{
            background: #f1f5f9;
            border: 1px solid var(--border-color);
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.82rem;
            color: #334155;
        }}
        .controls-sticky {{
            position: sticky;
            top: 12px;
            z-index: 100;
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(8px);
            padding: 16px;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);
            margin-bottom: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .controls-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            align-items: center;
            justify-content: space-between;
        }}
        .filter-buttons {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        .btn {{
            background: #ffffff;
            border: 1px solid var(--border-color);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 0.82rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s ease;
        }}
        .btn:hover {{
            background: #f1f5f9;
        }}
        .btn.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary);
        }}
        .search-input {{
            padding: 7px 12px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            font-size: 0.85rem;
            width: 240px;
            outline: none;
        }}
        .search-input:focus {{
            border-color: var(--primary);
            box-shadow: 0 0 0 2px var(--primary-light);
        }}
        .comment-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 14px;
            transition: transform 0.1s ease, box-shadow 0.1s ease;
        }}
        .comment-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
        }}
        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            flex-wrap: wrap;
            gap: 8px;
        }}
        .meta-left {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.88rem;
        }}
        .comment-id {{
            font-weight: 700;
            color: var(--text-muted);
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        .author-name {{
            color: #1e293b;
        }}
        .thread-badge {{
            background: #f1f5f9;
            color: #475569;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.78rem;
        }}
        .timestamp {{
            color: #94a3b8;
            font-size: 0.8rem;
        }}
        .meta-right {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .category-badge {{
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }}
        .confidence-tag {{
            font-size: 0.8rem;
            font-weight: 600;
            color: #475569;
        }}
        .comment-body {{
            font-size: 0.95rem;
            color: #1e293b;
            margin-bottom: 14px;
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        .card-footer {{
            border-top: 1px solid #f1f5f9;
            padding-top: 10px;
            display: flex;
            flex-direction: column;
            gap: 6px;
        }}
        .confidence-bar-bg {{
            height: 4px;
            background: #e2e8f0;
            border-radius: 2px;
            overflow: hidden;
            width: 100%;
        }}
        .confidence-bar-fill {{
            height: 100%;
            background: var(--primary);
            border-radius: 2px;
        }}
        .prob-distribution {{
            font-size: 0.78rem;
            color: var(--text-muted);
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            align-items: center;
        }}
        .prob-pill {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 1px 6px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI Comment Moderation Audit</h1>
            <p class="subtitle">
                Dataset: <strong>{html.escape(dataset_name)}</strong> &bull; 
                Model: <strong>{html.escape(model_name)}</strong> &bull; 
                Course: <em>{html.escape(course_info.get("course", "N/A"))}</em>
            </p>
            <div class="stats-bar">
                {''.join(metric_pills)}
            </div>
        </header>

        <div class="controls-sticky">
            <div class="controls-row">
                <div class="filter-buttons" id="filter-buttons">
                    <button class="btn active" data-filter="all">All</button>
                    <button class="btn" data-filter="spam">Spam</button>
                    <button class="btn" data-filter="abusive">Abusive</button>
                    <button class="btn" data-filter="off-topic">Off-Topic</button>
                    <button class="btn" data-filter="constructive">Constructive</button>
                    <button class="btn" data-filter="praise">Praise</button>
                    <button class="btn" data-filter="question/help-needed">Question/Help</button>
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="btn" id="sort-conf-btn">Sort: Lowest Confidence First</button>
                    <input type="text" id="search-box" class="search-input" placeholder="Search comments / authors...">
                </div>
            </div>
        </div>

        <div id="comments-container">
            {''.join(cards_html)}
        </div>
    </div>

    <script>
        const cards = Array.from(document.querySelectorAll('.comment-card'));
        const container = document.getElementById('comments-container');
        const filterBtns = document.querySelectorAll('.filter-buttons .btn');
        const searchBox = document.getElementById('search-box');
        const sortConfBtn = document.getElementById('sort-conf-btn');

        let activeFilter = 'all';
        let isSortedLowConf = false;

        function updateView() {{
            const query = searchBox.value.toLowerCase().trim();

            cards.forEach(card => {{
                const cat = card.getAttribute('data-category');
                const text = card.textContent.toLowerCase();

                const matchesFilter = (activeFilter === 'all' || cat === activeFilter);
                const matchesSearch = (!query || text.includes(query));

                card.style.display = (matchesFilter && matchesSearch) ? 'block' : 'none';
            }});
        }}

        filterBtns.forEach(btn => {{
            btn.addEventListener('click', () => {{
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                activeFilter = btn.getAttribute('data-filter');
                updateView();
            }});
        }});

        searchBox.addEventListener('input', updateView);

        sortConfBtn.addEventListener('click', () => {{
            isSortedLowConf = !isSortedLowConf;
            if (isSortedLowConf) {{
                sortConfBtn.textContent = 'Sort: Reset Natural Order';
                sortConfBtn.classList.add('active');
                cards.sort((a, b) => parseFloat(a.dataset.confidence) - parseFloat(b.dataset.confidence));
            }} else {{
                sortConfBtn.textContent = 'Sort: Lowest Confidence First';
                sortConfBtn.classList.remove('active');
                cards.sort((a, b) => parseInt(a.dataset.id) - parseInt(b.dataset.id));
            }}
            cards.forEach(card => container.appendChild(card));
        }});
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)


def main():
    parser = argparse.ArgumentParser(description="Classify forum comments with Cloudflare Workers AI Clef.")
    parser.add_argument("--v2", action="store_true", help="Process comments-v2.json using the larger clef model.")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of comments to process (useful for testing).")
    parser.add_argument("--force", action="store_true", help="Ignore cached API results and re-run all calls.")
    parser.add_argument("--creds", default="cloud-flare.local.sh", help="Path to credentials file.")
    args = parser.parse_args()

    if args.v2:
        input_file = "comments-v2.json"
        output_html = "results-v2.html"
        cache_file = "cache_results_v2.json"
        model = "clef"
        criteria = CATEGORIES_V2
        dataset_name = "comments-v2.json (Harder Evaluation)"
    else:
        input_file = "comments.json"
        output_html = "results.html"
        cache_file = "cache_results_v1.json"
        model = "clef-flash"
        criteria = CATEGORIES_V1
        dataset_name = "comments.json (Baseline Evaluation)"

    print("=" * 65)
    print(f"  AI Comment Moderator: {dataset_name}")
    print(f"  Model: @cf/cloudflare/{model}")
    print(f"  Input: {input_file}  -->  Output: {output_html}")
    print("=" * 65)

    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found in current directory.", file=sys.stderr)
        sys.exit(1)

    account_id, api_token = load_credentials(args.creds)

    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    comments = data.get("comments", [])
    if args.limit:
        comments = comments[:args.limit]
        print(f"[*] Processing limited subset of {len(comments)} comments.")

    cache = {}
    if os.path.exists(cache_file) and not args.force:
        try:
            with open(cache_file, "r", encoding="utf-8") as cf:
                cache = json.load(cf)
            print(f"[*] Loaded {len(cache)} cached classifications from {cache_file}.")
        except Exception:
            cache = {}

    processed_results = []
    total = len(comments)

    for idx, c in enumerate(comments, 1):
        cid = str(c["id"])
        c_text = c.get("comment", "")

        if cid in cache and not args.force:
            classification = cache[cid]
        else:
            print(f"[{idx}/{total}] Classifying comment #{cid} via {model}...")
            classification = call_clef_api(account_id, api_token, model, c_text, criteria)
            cache[cid] = classification
            if idx % 5 == 0 or idx == total:
                with open(cache_file, "w", encoding="utf-8") as cf:
                    json.dump(cache, cf, indent=2)
            time.sleep(0.1)

        processed_results.append({
            "id": c["id"],
            "author": c.get("author", "Anonymous"),
            "thread": c.get("thread", "General"),
            "posted_at": c.get("posted_at", ""),
            "comment": c_text,
            "classification": classification
        })

    with open(cache_file, "w", encoding="utf-8") as cf:
        json.dump(cache, cf, indent=2)

    print(f"[*] Generating interactive HTML report at {output_html}...")
    generate_html_report(processed_results, output_html, dataset_name, model, data)

    print(f"\n[✓] Completed! Open {output_html} in your browser to inspect Clef's work.")
    print("=" * 65)


if __name__ == "__main__":
    main()
