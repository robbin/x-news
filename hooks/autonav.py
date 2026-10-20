"""Auto-generate nav + editorial index pages (zh + en) from docs/<category>/*.md.

Bilingual (mkdocs-static-i18n, suffix structure): `foo.md` = Chinese (default),
`foo.en.md` = English. New reports appear without editing mkdocs.yml.

The report files are only read. This hook renders their index pages as issue
cards / dated ledger entries (instead of plain Markdown lists); every report is
still listed in the nav and on its category page.
"""
import datetime
import html
import os
import re
from urllib.parse import quote

import yaml

CATS = [
    {
        "folder": "Chinese-Topics",
        "zh": "中文选题",
        "en": "Chinese Topics",
        "badge_zh": "中文选题",
        "badge_en": "Chinese",
        "desc_zh": "从中文 X 圈层里挑出值得写的话题：热度、可写角度与核验状态都在这里。",
        "desc_en": "Story ideas worth pursuing from Chinese-language X, with traction, angles and verification notes.",
    },
    {
        "folder": "English-Topics",
        "zh": "英文选题",
        "en": "English Topics",
        "badge_zh": "英文选题",
        "badge_en": "English",
        "desc_zh": "追踪英文 X 上的 AI 热点，把讨论整理成可操作的选题与来源。",
        "desc_en": "AI conversations trending in English on X, turned into actionable briefs with sources.",
    },
    {
        "folder": "Daily",
        "zh": "X AI 日报",
        "en": "X AI Daily",
        "badge_zh": "日报",
        "badge_en": "Daily",
        "desc_zh": "每天一份 AI 动态摘要：模型、产品、研究，以及为什么值得关注。",
        "desc_en": "A daily digest of AI news on X: models, products, research — and why it matters.",
    },
]

LANG_SUFFIX = re.compile(r"\.([a-z]{2})\.md$")
WEEKDAYS_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
KEYS = {"Chinese-Topics": "cn", "English-Topics": "en", "Daily": "daily"}


def _read(path):
    """Return (frontmatter, body) for a report file."""
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
    return meta, body


def _clip(text, limit):
    text = text.strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip("，,。.;；、 ") + "…"


def _plain(text):
    """Strip the small amount of inline Markdown used in headings."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_~]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _display_title(title):
    """Turn the report's H1 into a periodical-style title (the date is shown separately)."""
    t = re.sub(r"\s*[（(]\s*\d{4}-\d{2}-\d{2}\s*[)）]\s*$", "", title)
    t = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[-–—]?\s*", "", t)
    return t.strip() or title.strip()


def _report(path, en=False):
    meta, body = _read(path)
    h1 = re.search(r"^#\s+(.+?)\s*$", body, re.M)
    title = h1.group(1) if h1 else meta.get("title")
    if not title:
        title = os.path.splitext(os.path.basename(path))[0]
    title = _display_title(_plain(str(title)))

    date = meta.get("date")
    if isinstance(date, datetime.datetime):
        date = date.date().isoformat()
    elif isinstance(date, datetime.date):
        date = date.isoformat()
    if not date:
        d = re.search(r"\d{4}-\d{2}-\d{2}", os.path.basename(path))
        date = d.group(0) if d else datetime.date.fromtimestamp(
            os.path.getmtime(path)
        ).isoformat()
    date = str(date).strip()

    headings = []
    for h in re.findall(r"^###\s+(.+?)\s*$", body, re.M):
        h = _plain(re.sub(r"^\d+[.、)]\s*", "", h))
        if h:
            headings.append(h)
    limit = 58 if en else 34
    lead = " · ".join(_clip(h, limit) for h in headings[:2]) if headings else ""
    return {
        "title": title,
        "date": date,
        "headings": len(headings),
        "lead": lead,
    }


def _date_part(date):
    m = re.match(r"(\d{4}-\d{2}-\d{2})", date)
    return m.group(1) if m else date


def _date_label(date_part, en):
    try:
        d = datetime.date.fromisoformat(date_part)
    except ValueError:
        return date_part, ""
    if en:
        return f"{d.day} {d.strftime('%B %Y')}", d.strftime("%A")
    return f"{d.year} 年 {d.month} 月 {d.day} 日", WEEKDAYS_ZH[d.weekday()]


def _url(config, target_src, base_dir=""):
    """URL for a docs source path, relative to base_dir (a section folder)."""
    stem = target_src[:-3] if target_src.endswith(".md") else target_src
    if base_dir and stem.startswith(base_dir + "/"):
        stem = stem[len(base_dir) + 1:]
    if config.get("use_directory_urls", True):
        if stem == "index":
            stem = ""
        elif stem.endswith("/index"):
            stem = stem[: -len("/index")]
        url = stem + "/" if stem else "./"
    else:
        url = stem + ".html"
    # Keep ASCII path characters readable, percent-encode the Chinese file names
    # exactly like MkDocs does for regular Markdown links.
    return quote(url, safe="/-._~")


def _write(path, content):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)


def _card(report, cat, config, en):
    href = _url(config, f"{cat['folder']}/{report['file']}", "")
    title = html.escape(report["title_en"] if en and report["title_en"] else report["title"])
    lead = report["lead_en"] if en and report["lead_en"] else report["lead"]
    badge = cat["badge_en"] if en else cat["badge_zh"]
    count = report["headings"]
    count_label = f"{count} 条" if not en else f"{count} item" + ("" if count == 1 else "s")
    more = "Read" if en else "阅读"
    flag = ""
    if en and not report["title_en"]:
        flag = '<span class="fk-card__flag">Chinese only</span>'
    lead_html = (
        f'<span class="fk-card__lead">{html.escape(lead)}</span>' if lead else ""
    )
    count_html = (
        f'<span class="fk-card__count">{html.escape(count_label)}</span>' if count else ""
    )
    return (
        f'<a class="fk-card" data-cat="{cat["key"]}" href="{html.escape(href, quote=True)}">'
        f'<span class="fk-card__top"><span class="fk-badge">{html.escape(badge)}</span>{flag}</span>'
        f'<span class="fk-card__title">{title}</span>'
        f"{lead_html}"
        f'<span class="fk-card__foot">{count_html}<span class="fk-card__more">{more} <span aria-hidden="true">→</span></span></span>'
        "</a>"
    )


def _home(config, latest, day_limit, en):
    groups = []
    for report in latest:
        part = _date_part(report["date"])
        if not groups or groups[-1][0] != part:
            groups.append((part, []))
        groups[-1][1].append(report)
    groups = groups[:day_limit]
    if not groups:
        return (
            '<p class="fk-empty">'
            + ("No reports yet. Please check back later." if en else "暂无报告，请稍后再来。")
            + "</p>"
        )
    out = ['<div class="fk-days">']
    for part, reports in groups:
        date_label, weekday = _date_label(part, en)
        out.append('<section class="fk-day">')
        out.append(
            f'<h3 class="fk-day__label"><time datetime="{html.escape(part)}">{html.escape(date_label)}</time>'
            f'<span class="fk-day__weekday">{html.escape(weekday)}</span></h3>'
        )
        out.append('<div class="fk-cards">')
        for report in reports:
            out.append(_card(report, report["cat"], config, en))
        out.append("</div></section>")
    out.append("</div>")
    return "\n".join(out)


def _sections(config, cats, en):
    cards = []
    for cat in cats:
        href = _url(config, f"{cat['folder']}/index.md", "")
        reports = cat["reports"]
        count = len(reports)
        latest = reports[0]["date"][:10] if reports else ""
        meta = (
            f"{count} issue" + ("" if count == 1 else "s")
            if en
            else f"{count} 期"
        )
        if latest:
            meta += f" · {latest}"
        cards.append(
            f'<a class="fk-section" data-cat="{cat["key"]}" href="{html.escape(href, quote=True)}">'
            f'<span class="fk-section__name">{html.escape(cat["en"] if en else cat["zh"])}</span>'
            f'<span class="fk-section__desc">{html.escape(cat["desc_en"] if en else cat["desc_zh"])}</span>'
            f'<span class="fk-section__meta">{html.escape(meta)}<span class="fk-section__arrow" aria-hidden="true">→</span></span>'
            "</a>"
        )
    return '<div class="fk-sections">' + "".join(cards) + "</div>"


def _section_page(cat, config, en):
    label = cat["en"] if en else cat["zh"]
    items = []
    for report in cat["reports"]:
        href = _url(config, f"{cat['folder']}/{report['file']}", cat["folder"])
        part = _date_part(report["date"])
        title = report["title_en"] if en and report["title_en"] else report["title"]
        lead = report["lead_en"] if en and report["lead_en"] else report["lead"]
        count = report["headings"]
        count_label = f"{count} 条" if not en else f"{count} item" + ("" if count == 1 else "s")
        try:
            d = datetime.date.fromisoformat(part)
            day, month = str(d.day).zfill(2), (
                d.strftime("%Y.%m") if not en else d.strftime("%b %Y")
            )
            weekday = "" if en else WEEKDAYS_ZH[d.weekday()]
        except ValueError:
            day, month, weekday = part, "", ""
        flag = ""
        if en and not report["title_en"]:
            flag = '<span class="fk-entry__flag">Chinese only</span>'
        lead_html = f'<span class="fk-entry__lead">{html.escape(lead)}</span>' if lead else ""
        count_html = f'<span class="fk-entry__count">{html.escape(count_label)}</span>' if count else ""
        weekday_html = (
            f'<span class="fk-entry__weekday">{weekday}</span>' if weekday else ""
        )
        items.append(
            f'<a class="fk-entry" href="{html.escape(href, quote=True)}">'
            f'<time class="fk-entry__date" datetime="{html.escape(part)}">'
            f'<span class="fk-entry__day">{html.escape(day)}</span>'
            f'<span class="fk-entry__month">{html.escape(month)}</span>'
            f"{weekday_html}"
            "</time>"
            '<span class="fk-entry__main">'
            f'<span class="fk-entry__title">{html.escape(title)}</span>'
            f"{flag}"
            f"{lead_html}"
            f'<span class="fk-entry__meta">{count_html}</span>'
            "</span>"
            '<span class="fk-entry__arrow" aria-hidden="true">→</span>'
            "</a>"
        )
    if not items:
        items.append(
            '<p class="fk-empty">'
            + ("Nothing in this section yet. Please check back later." if en else "该分类还没有报告，请稍后再来。")
            + "</p>"
        )
    count = len(cat["reports"])
    latest = cat["reports"][0]["date"][:10] if cat["reports"] else ""
    if en:
        meta = f"{count} issue" + ("" if count == 1 else "s")
        meta += f" · Latest {latest}" if latest else ""
        eyebrow = "SECTION"
    else:
        meta = f"共 {count} 期"
        meta += f" · 最近更新 {latest}" if latest else ""
        eyebrow = "栏目"
    desc = cat["desc_en"] if en else cat["desc_zh"]
    front = yaml.safe_dump(
        {"title": label, "description": desc}, allow_unicode=True, sort_keys=False
    ).strip()
    return "\n".join([
        f"---\n{front}\n---\n",
        f'<p class="fk-eyebrow">{eyebrow}</p>',
        f"# {label}",
        f'<p class="fk-section__intro">{html.escape(desc)}</p>',
        f'<p class="fk-section-line">{html.escape(meta)}</p>',
        '<div class="fk-ledger">',
        *items,
        "</div>",
    ])


def on_config(config):
    docs = config["docs_dir"]
    nav = [{"首页": "index.md"}]
    cats = []
    latest = []
    for order, cat in enumerate(CATS):
        cat = dict(cat, key=KEYS[cat["folder"]], order=order, reports=[])
        d = os.path.join(docs, cat["folder"])
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            if not fn.endswith(".md") or LANG_SUFFIX.search(fn) or fn == "index.md":
                continue
            zh = _report(os.path.join(d, fn))
            en_path = os.path.join(d, fn[:-3] + ".en.md")
            en = _report(en_path, en=True) if os.path.exists(en_path) else None
            rec = {
                "file": fn,
                "cat": cat,
                "date": zh["date"],
                "title": zh["title"],
                "title_en": en["title"] if en else None,
                "lead": zh["lead"],
                "lead_en": en["lead"] if en else None,
                "headings": zh["headings"],
            }
            cat["reports"].append(rec)
            latest.append(rec)
        cat["reports"].sort(key=lambda r: (r["date"], r["file"]), reverse=True)
        _write(
            os.path.join(d, "index.md"),
            _section_page(cat, config, en=False) + "\n",
        )
        _write(
            os.path.join(d, "index.en.md"),
            _section_page(cat, config, en=True) + "\n",
        )
        # Date-only nav labels read like an archive and work in both languages.
        seen = {}
        entries = []
        for report in cat["reports"]:
            label = report["date"][:10]
            seen[label] = seen.get(label, 0) + 1
            if seen[label] > 1:
                label = f"{label} ({seen[label]})"
            entries.append({label: f"{cat['folder']}/{report['file']}"})
        nav.append({cat["zh"]: [{cat["zh"]: f"{cat['folder']}/index.md"}] + entries})
        cats.append(cat)

    latest.sort(key=lambda r: (r["date"], -r["cat"]["order"]), reverse=True)
    home = ["# 范凯说AI · X 新闻\n", "## 最新报告\n", _home(config, latest, 4, False), "\n## 分类\n", _sections(config, cats, False)]
    home_en = ["# Fan Kai on AI · X News\n", "## Latest reports\n", _home(config, latest, 4, True), "\n## Sections\n", _sections(config, cats, True)]
    _write(os.path.join(docs, "index.md"), "\n".join(home) + "\n")
    _write(os.path.join(docs, "index.en.md"), "\n".join(home_en) + "\n")
    config["nav"] = nav
    return config
