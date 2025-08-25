#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydro 题库抓取脚本 (修复+增量合并版)
- 修复 HYDRO_SLEEP 为空字符串导致 float() 报错的问题。
- entry_paths 已精简为 ["/p"]，可抓取 H1000 等题目。
- 保存 problems.json 时自动合并旧数据，避免覆盖。
"""
import os
import re
import json
import time
import pathlib
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup

BASE = "https://hydro.ac"
HEADERS = {"User-Agent": "hydro-cxoj-pages-bot/1.0 (+GitHub Actions)"}
OUT_DIR = pathlib.Path("data")
PROB_DIR = OUT_DIR / "problems"
OUT_DIR.mkdir(parents=True, exist_ok=True)
PROB_DIR.mkdir(parents=True, exist_ok=True)

# ---- 修复这里 ----
def _env_float(key: str, default: float) -> float:
    val = os.getenv(key)
    if val is None or val.strip() == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default

SLEEP = _env_float("HYDRO_SLEEP", 0.8)
MAX_PROBLEMS = int(os.getenv("HYDRO_MAX_PROBLEMS", "300") or 300)
EXPLICIT_IDS = [s.strip() for s in os.getenv("HYDRO_PROBLEM_IDS", "").split(",") if s.strip()]

# 简易缓存，避免重复请求
CACHE_DIR = pathlib.Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

def get(url: str) -> Optional[str]:
    key = re.sub(r"[^a-zA-Z0-9]+", "_", url)
    cache_file = CACHE_DIR / f"{key}.html"
    if cache_file.exists():
        return cache_file.read_text("utf-8", errors="ignore")
    for i in range(3):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                cache_file.write_text(r.text, "utf-8")
                return r.text
        except Exception:
            pass
        time.sleep(1.2 * (i + 1))
    return None

@dataclass
class ProblemSummary:
    id: str
    title: str
    href: str
    tags: List[str]

@dataclass
class ProblemDetail:
    id: str
    title: str
    html: str
    tags: List[str]
    source: str

PROBLEM_LINK_RE = re.compile(r"/p/([A-Za-z0-9_-]+)")

def discover_problem_ids() -> List[str]:
    candidates = set()
    entry_paths = ["/p"]  # 只抓取 /p 下的题目
    for path in entry_paths:
        html = get(BASE + path)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = PROBLEM_LINK_RE.search(href)
            if m:
                candidates.add(m.group(1))
        if len(candidates) >= MAX_PROBLEMS:
            break
    ids = sorted(list(candidates))[:MAX_PROBLEMS]
    print(f"[*] Discovered {len(ids)} problem ids")
    return ids

def parse_problem(problem_id: str) -> Optional[ProblemDetail]:
    url = f"{BASE}/p/{problem_id}"
    html = get(url)
    if not html:
        print(f"[!] Failed to fetch {url}")
        return None
    soup = BeautifulSoup(html, "html.parser")

    title = None
    for sel in ["h1", "h2", ".title", "#title", ".problem-title"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break
    if not title:
        t = soup.find("title")
        title = t.get_text(strip=True) if t else f"Problem {problem_id}"

    tags = []
    for sel in [".tags a", ".tag-list a", "a.tag", ".problem-tags a"]:
        for a in soup.select(sel):
            text = a.get_text(strip=True)
            if text:
                tags.append(text)
    tags = sorted(set(tags))

    content = None
    for sel in ["#content", ".content", ".markdown-body", ".article", ".problem-content", "main", "article"]:
        el = soup.select_one(sel)
        if el and el.decode_contents().strip():
            content = el.decode_contents()
            break
    if not content:
        body = soup.find("body")
        content = body.decode_contents() if body else html

    return ProblemDetail(
        id=problem_id,
        title=title,
        html=content,
        tags=tags,
        source=url,
    )

def save_detail(detail: ProblemDetail) -> Dict:
    d = asdict(detail)
    (PROB_DIR / f"{detail.id}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), "utf-8")
    return d

def save_problem_summaries(summaries: List[ProblemSummary]):
    """
    保存 problems.json，并自动合并旧数据
    """
    PROBLEMS_JSON = OUT_DIR / "problems.json"  # 放在函数内部
    if PROBLEMS_JSON.exists():
        try:
            old_problems = json.loads(PROBLEMS_JSON.read_text("utf-8"))
            old_dict = {p["id"]: p for p in old_problems}
        except Exception:
            old_dict = {}
    else:
        old_dict = {}

    new_dict = {p.id: asdict(p) for p in summaries}
    merged = {**old_dict, **new_dict}

    PROBLEMS_JSON.write_text(
        json.dumps(list(merged.values()), ensure_ascii=False, indent=2),
        "utf-8"
    )
    print(f"[*] Wrote {len(merged)} summaries → data/problems.json")

def main():
    if EXPLICIT_IDS:
        ids = EXPLICIT_IDS[:MAX_PROBLEMS]
    else:
        ids = discover_problem_ids()
    if not ids:
        print("[!] No problems discovered; please set HYDRO_PROBLEM_IDS")
        return

    summaries: List[ProblemSummary] = []
    for pid in ids:
        print(f"[*] Fetching problem {pid}...")
        detail = parse_problem(pid)
        if not detail:
            continue
        save_detail(detail)
        summaries.append(ProblemSummary(
            id=detail.id,
            title=detail.title,
            href=f"problem.html?id={detail.id}",
            tags=detail.tags
        ))
        time.sleep(SLEEP)

    save_problem_summaries(summaries)

if __name__ == "__main__":
    main()
