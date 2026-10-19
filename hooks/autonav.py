"""Auto-generate nav + index pages (zh + en) from docs/<category>/*.md (newest first).
Bilingual (mkdocs-static-i18n, suffix structure): `foo.md` = Chinese (default), `foo.en.md` = English.
New reports appear without editing mkdocs.yml. Nav report entries carry no explicit title, so each
language shows the page's own title; section labels are translated via i18n nav_translations."""
import os, re, datetime
import yaml

CATS = [
    ("Chinese-Topics", "中文选题", "Chinese Topics"),
    ("English-Topics", "英文选题", "English Topics"),
    ("Daily", "X AI 日报", "X AI Daily"),
]
LATEST_N = 10
LANG_SUFFIX = re.compile(r"\.([a-z]{2})\.md$")


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
    for folder, label, label_en in CATS:
        d = os.path.join(docs, folder)
        os.makedirs(d, exist_ok=True)
        reports = []  # (date, zh_fn, zh_title, en_title or None)
        for fn in os.listdir(d):
            if not fn.endswith(".md") or LANG_SUFFIX.search(fn) or fn == "index.md":
                continue
            t, dt = _meta(os.path.join(d, fn))
            en = os.path.join(d, fn[:-3] + ".en.md")
            t_en = _meta(en)[0] if os.path.exists(en) else None
            reports.append((dt, fn, t, t_en))
        reports.sort(key=lambda r: (r[0], r[1]), reverse=True)
        zh = [f"# {label}\n"]
        en = [f"# {label_en}\n"]
        if reports:
            zh += [f"- **{dt}** · [{t}]({fn})" for dt, fn, t, _ in reports]
            en += [f"- **{dt}** · [{te or t}]({fn})" + ("" if te else " *(Chinese only)*") for dt, fn, t, te in reports]
        else:
            zh.append("!!! note \"暂无报告\"\n    该分类还没有报告，主人请稍后再来。")
            en.append("!!! note \"No reports yet\"\n    Nothing in this section yet. Please check back later.")
        _write(os.path.join(d, "index.md"), "\n".join(zh) + "\n")
        _write(os.path.join(d, "index.en.md"), "\n".join(en) + "\n")
        nav.append({label: [f"{folder}/index.md"] + [f"{folder}/{fn}" for _, fn, _, _ in reports]})
        latest += [(dt, folder, fn, t, te, label, label_en) for dt, fn, t, te in reports]
    latest.sort(reverse=True)
    top = latest[:LATEST_N]
    home = ["# 范凯说AI · X 情报\n", "## 最新报告\n"]
    home_en = ["# Fan Kai on AI · X Intel\n", "## Latest reports\n"]
    if top:
        home += [f"- **{dt}** · `{l}` · [{t}]({f}/{fn})" for dt, f, fn, t, te, l, le in top]
        home_en += [f"- **{dt}** · `{le}` · [{te or t}]({f}/{fn})" for dt, f, fn, t, te, l, le in top]
    else:
        home.append("暂无报告。")
        home_en.append("No reports yet.")
    home.append("\n## 分类\n")
    home_en.append("\n## Sections\n")
    home += [f"- [{l}]({f}/index.md)" for f, l, _ in CATS]
    home_en += [f"- [{le}]({f}/index.md)" for f, _, le in CATS]
    _write(os.path.join(docs, "index.md"), "\n".join(home) + "\n")
    _write(os.path.join(docs, "index.en.md"), "\n".join(home_en) + "\n")
    config["nav"] = nav
    return config
