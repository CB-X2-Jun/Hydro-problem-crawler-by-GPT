# Hydro-problem-crawler-by-GPT
Hydro 题目爬取（测试用repo）

# *这里的所有文件（包括 README）都由 GPT-5 生成。*

# Hydro → CXOJ Pages


一个可以 **直接部署到 GitHub Pages** 的仓库。通过 GitHub Actions 定时/手动爬取 https://hydro.ac 的公开题目，生成静态数据与页面，在网页端以 **CXOJ 风格** 展示题目列表与题面。支持：


- ✅ Markdown/HTML 渲染（前端渲染）
- ✅ KaTeX 数学公式
- ✅ 代码高亮（highlight.js）
- ✅ 题目列表 + 详情页面


> ⚠️ **尊重目标站点的 Robots/ToS**：本项目仅用于学习与个人使用。请合理设置抓取频率、限流与缓存。


## 一键使用


1. 点击右上角 **Use this template** 或 Fork 本仓库。
2. 进入仓库 **Settings → Pages**，将 **Source** 设置为 `GitHub Actions`。
3. 在 **Actions** 里启用工作流，或者点击 **Run workflow** 手动触发。


工作流完成后，访问：`https://<你的用户名>.github.io/<仓库名>/`。


## 自定义抓取范围


- 默认尝试从 Hydro 的题库/索引页中发现题目链接（尽力适配）。
- 你也可以显式指定题号（ID 或 slug），在仓库 **Settings → Secrets and variables → Actions → Variables** 中新增：
- `HYDRO_PROBLEM_IDS`：例如 `1000,1001,abc123`（逗号分隔）。
- 或者限制最大爬取数量：
- `HYDRO_MAX_PROBLEMS`：例如 `200`。


## 本地调试


```bash
# 可选：创建虚拟环境
python -m venv .venv && source .venv/bin/activate # Windows: .venv\\Scripts\\activate


pip install -r requirements.txt # 若无此文件，可直接用脚本中的最小依赖


python scripts/scrape_hydro.py # 抓取到 ./data/
# 用任意静态服务器预览 public/，比如：
python -m http.server -d public 5500
# 打开 http://localhost:5500
```


## 目录说明


- `scripts/scrape_hydro.py`：抓取器，解析 Hydro 题目列表与题面，生成 `data/problems.json` 与 `data/problems/<id>.json`。
- `public/`：前端站点（无需打包），直接引用 CDN：KaTeX / highlight.js。
- `.github/workflows/pages.yml`：CI 任务，顺序为 **抓取 → 复制数据 → 发布**。


## 授权协议


MIT
