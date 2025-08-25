#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hydro 题库抓取脚本

目标：
- 生成 data/problems.json (题目列表)
- 生成 data/problems/<id>.json (详情，含 HTML 内容)

说明：
- 由于 Hydro 可能会调整页面结构，本脚本以 "尽量健壮" 的方式抓取。
- 优先使用显式变量 HYDRO_PROBLEM_IDS；若未提供，则尝试从索引页自动发现题目链接。
- 尊重站点：添加 UA，设置轻量限流，失败自动重试，写入缓存避免重复请求。
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

SLEEP = float(os.getenv("HYDRO_SLEEP", "0.8"))
MAX_PROBLEMS = int(os.getenv("HYDRO_MAX_PROBLEMS", "300"))
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
    html: str  # 题面 HTML（保留 KaTeX 符号，前端再渲染）
    tags: List[str]
    source: str

PROBLEM_LINK_RE = re.compile(r"/problem/([A-Za-z0-9_-]+)")


def discover_problem_ids() -> List[str]:
    """尽力从若干入口页发现题目链接。根据 Hydro 的常见导航尝试多个候选路径。"""
    candidates = set()
    entry_paths = [
        "/p",
    ]
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
    url = f"{BASE}/problem/{problem_id}"
    html = get(url)
    if not html:
        print(f"[!] Failed to fetch {url}")
        return None
    soup = BeautifulSoup(html, "html.parser")

    # 标题（多策略容错）
    title = None
    for sel in ["h1", "h2", ".title", "#title", ".problem-title"]:
        el = soup.select_one(sel)
        if el and el.get_text(strip=True):
            title = el.get_text(strip=True)
            break
    if not title:
        # 退化：从 <title>
        t = soup.find("title")
        title = t.get_text(strip=True) if t else f"Problem {problem_id}"

    # 标签（可选）
    tags = []
    for sel in [".tags a", ".tag-list a", "a.tag", ".problem-tags a"]:
        for a in soup.select(sel):
            text = a.get_text(strip=True)
            if text:
                tags.append(text)
    tags = sorted(set(tags))

    # 题面主体（优先常见容器，找不到就退化为主要内容片段）
    content = None
    for sel in [
        "#content", ".content", ".markdown-body", ".article", ".problem-content", "main", "article",
    ]:
        el = soup.select_one(sel)
        if el and el.decode_contents().strip():
            content = el.decode_contents()
            break
    if not content:
        # 如果没有明确容器，尝试 body 内主要 section
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
        summaries.append(ProblemSummary(id=detail.id, title=detail.title, href=f"problem.html?id={detail.id}", tags=detail.tags))
        time.sleep(SLEEP)

    problems = [asdict(x) for x in summaries]
    (OUT_DIR / "problems.json").write_text(json.dumps(problems, ensure_ascii=False, indent=2), "utf-8")
    print(f"[*] Wrote {len(problems)} summaries → data/problems.json")

if __name__ == "__main__":
    main()
