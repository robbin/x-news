"""Auto-generate nav + index pages from docs/<category>/*.md (newest first).
New reports appear without editing mkdocs.yml."""
import os, re, datetime
import yaml

CATS = [
    ("Chinese-Topics", "中文 Top 20"),
    ("English-Topics", "英文 Top 20"),
    ("Daily", "X 新闻日报"),
    ("High-Traffic", "中文高流量发现"),
]
LATEST_N = 10


def _meta(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    meta = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if m:
        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except Exception:
            meta = {}
        body = text[m.end():]
    else:
        body = text
    title = meta.get("title")
    if not title:
        h = re.search(r"^#\s+(.+)$", body, re.M)
        title = h.group(1).strip() if h else os.path.splitext(os.path.basename(path))[0]
    date = meta.get("date")
    if isinstance(date, (datetime.date, datetime.datetime)):
        date = date.strftime("%Y-%m-%d %H:%M") if isinstance(date, datetime.datetime) else date.isoformat()
    if not date:
        d = re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(path))
        date = d.group(0) if d else datetime.datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")
    return str(title), str(date)


def _write(path, content):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def on_config(config):
    docs = config["docs_dir"]
    nav = [{"首页": "index.md"}]
    latest = []
    for folder, label in CATS:
        d = os.path.join(docs, folder)
        os.makedirs(d, exist_ok=True)
        reports = []
        for fn in os.listdir(d):
            if fn.endswith(".md") and fn != "index.md":
                t, dt = _meta(os.path.join(d, fn))
                reports.append((dt, fn, t))
        reports.sort(key=lambda r: (r[0], r[1]), reverse=True)
        lines = [f"# {label}\n"]
        if reports:
            lines += [f"- **{dt}** · [{t}]({fn})" for dt, fn, t in reports]
        else:
            lines.append("!!! note \"暂无报告\"\n    该分类还没有报告，主人请稍后再来。")
        _write(os.path.join(d, "index.md"), "\n".join(lines) + "\n")
        nav.append({label: [f"{folder}/index.md"] + [{t: f"{folder}/{fn}"} for dt, fn, t in reports]})
        latest += [(dt, folder, fn, t, label) for dt, fn, t in reports]
    latest.sort(reverse=True)
    home = ["# 范凯说AI · X 情报\n", "主人好，这里是每日 X 情报汇总。\n", "## 最新报告\n"]
    if latest:
        home += [f"- **{dt}** · `{label}` · [{t}]({folder}/{fn})" for dt, folder, fn, t, label in latest[:LATEST_N]]
    else:
        home.append("暂无报告。")
    home.append("\n## 分类\n")
    home += [f"- [{label}]({folder}/index.md)" for folder, label in CATS]
    _write(os.path.join(docs, "index.md"), "\n".join(home) + "\n")
    config["nav"] = nav
    return config
