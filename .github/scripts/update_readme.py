#!/usr/bin/env python3
"""
update_readme.py
Updates dynamic blocks in README.md:
- Recent GitHub Activity
- Latest Pushed Repositories
- Latest Medium Articles
"""

import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

USERNAME = "Vaibhavsharma45"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch_json(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "GitHub-README-Updater")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def fetch_medium_posts():
    url = "https://medium.com/feed/@vaibhavsharma95124v"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
        root = ET.fromstring(content)
        items = root.findall("./channel/item")
        posts = []
        for item in items[:5]:
            title = item.find("title").text if item.find("title") is not None else "Untitled"
            link = item.find("link").text if item.find("link") is not None else ""
            pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
            # format date
            try:
                dt = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
                date_str = dt.strftime("%b %d, %Y")
            except Exception:
                date_str = pub_date[:16]
            posts.append({"title": title, "link": link, "date": date_str})
        return posts
    except Exception as e:
        print(f"Error fetching Medium posts: {e}", file=sys.stderr)
        return []

def format_recent_activity(events):
    if not events:
        return "⚡ *Active building and optimizing machine learning repositories on GitHub.*"
    
    lines = []
    seen = set()
    for ev in events:
        ev_type = ev.get("type", "")
        repo_name = ev.get("repo", {}).get("name", "")
        repo_short = repo_name.split("/")[-1] if "/" in repo_name else repo_name
        repo_url = f"https://github.com/{repo_name}"
        created_at = ev.get("created_at", "")[:10]
        
        desc = ""
        if ev_type == "PushEvent":
            commits = ev.get("payload", {}).get("commits", [])
            msg = commits[0].get("message", "").split("\n")[0] if commits else "pushed code"
            desc = f"Pushed updates: `{msg}` to [`{repo_short}`]({repo_url})"
        elif ev_type == "CreateEvent":
            ref_type = ev.get("payload", {}).get("ref_type", "branch/tag")
            desc = f"Created {ref_type} on [`{repo_short}`]({repo_url})"
        elif ev_type == "WatchEvent":
            desc = f"Starred repository [`{repo_name}`]({repo_url})"
        elif ev_type == "IssuesEvent":
            action = ev.get("payload", {}).get("action", "interacted with")
            desc = f"{action.capitalize()} an issue in [`{repo_short}`]({repo_url})"
        elif ev_type == "PullRequestEvent":
            action = ev.get("payload", {}).get("action", "opened")
            desc = f"{action.capitalize()} pull request in [`{repo_short}`]({repo_url})"
            
        if desc and desc not in seen:
            seen.add(desc)
            lines.append(f"- 🚀 **{created_at}**: {desc}")
        if len(lines) >= 5:
            break
            
    if not lines:
        return "- 🚀 **2026-11-09**: Initialized automated developer branding and portfolio pipeline."
    return "\n".join(lines)

def format_latest_repos(repos):
    if not repos:
        return "No public repositories available."
    
    sorted_repos = sorted(repos, key=lambda x: x.get("pushed_at", ""), reverse=True)[:5]
    lines = []
    for r in sorted_repos:
        name = r.get("name", "")
        url = r.get("html_url", "")
        desc = r.get("description") or "AI / Engineering project."
        lang = r.get("language") or "Python"
        stars = r.get("stargazers_count", 0)
        lines.append(f"- 📦 [**{name}**]({url}) (`{lang}`) — {desc} ★ `{stars}`")
    return "\n".join(lines)

def format_blog_posts(posts):
    if not posts:
        return "✍️ *Engineering deep-dives and AI articles coming soon on [Medium (@vaibhavsharma95124v)](https://medium.com/@vaibhavsharma95124v)!*"
    lines = []
    for p in posts:
        lines.append(f"- 📰 [{p['title']}]({p['link']}) — *{p['date']}*")
    return "\n".join(lines)

def replace_block(content, marker, replacement):
    pattern = rf"(<!-- {marker}:START -->\n)(?:[\s\S]*?)(\n<!-- {marker}:END -->)"
    repl = rf"\g<1>{replacement}\g<2>"
    return re.sub(pattern, repl, content)

def main():
    readme_path = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
    if not os.path.exists(readme_path):
        print(f"README not found at {readme_path}", file=sys.stderr)
        return
        
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    events = fetch_json(f"https://api.github.com/users/{USERNAME}/events/public") or []
    repos = fetch_json(f"https://api.github.com/users/{USERNAME}/repos?per_page=100") or []
    posts = fetch_medium_posts()
    
    content = replace_block(content, "RECENT_ACTIVITY", format_recent_activity(events))
    content = replace_block(content, "LATEST_REPOS", format_latest_repos(repos))
    content = replace_block(content, "BLOG_POSTS", format_blog_posts(posts))
    
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("README.md dynamic blocks successfully updated!")

if __name__ == "__main__":
    main()
