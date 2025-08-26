import os, json
from pathlib import Path

OUT_DIR = Path("data")
OUT_DIR.mkdir(exist_ok=True)
PROBLEMS_JSON = OUT_DIR / "problems.json"


def save_problem_list_entry(problem: dict):
    """增量更新 problems.json 中的单个题目条目"""
    if PROBLEMS_JSON.exists():
        try:
            problems = json.loads(PROBLEMS_JSON.read_text("utf-8"))
        except Exception:
            problems = []
    else:
        problems = []

    problems_map = {p["id"]: p for p in problems if "id" in p}
    problems_map[problem["id"]] = problem

    PROBLEMS_JSON.write_text(
        json.dumps(list(problems_map.values()), ensure_ascii=False, indent=2),
        "utf-8"
    )
    print(f"✅ Updated problems.json with {problem['id']}")


def save_problem_detail(pid: str, detail: dict):
    """保存单题详情到 data/{pid}.json"""
    outfile = OUT_DIR / f"{pid}.json"
    outfile.write_text(json.dumps(detail, ensure_ascii=False, indent=2), "utf-8")
    print(f"📄 Saved detail for {pid}")


def crawl_problem(pid: str):
    """抓取单个题号（这里你可以接入真实抓取逻辑）"""
    # TODO: 替换为真实爬虫逻辑
    problem = {
        "id": pid,
        "title": f"#{pid}. Example Problem",
        "href": f"problem.html?id={pid}",
        "tags": []
    }
    detail = {
        "id": pid,
        "statement": f"This is the statement for {pid}.",
        "samples": []
    }

    save_problem_list_entry(problem)
    save_problem_detail(pid, detail)


def main():
    problem_ids = os.environ.get("PROBLEM_IDS")
    if not problem_ids:
        print("⚠️ No PROBLEM_IDS provided, exiting.")
        return

    ids = [x.strip() for x in problem_ids.split(",") if x.strip()]
    for pid in ids:
        crawl_problem(pid)


if __name__ == "__main__":
    main()
