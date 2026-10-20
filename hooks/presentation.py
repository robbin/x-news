"""Presentation only: no changes to report sources or the report sync process."""
import datetime
import html
import re
from urllib.parse import urlencode

SECTIONS = {
    "Chinese-Topics": ("中文选题", "Chinese Topics"),
    "English-Topics": ("英文选题", "English Topics"),
    "Daily": ("X AI 日报", "X AI Daily"),
}
WEEKDAYS_ZH = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
WEEKDAYS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
COVERAGE = {
    "complete": ("完整", "Complete"),
    "partial": ("部分", "Partial"),
}
# "- 发生了什么：…" / "- What happened: …" → the label becomes a quiet kicker,
# which gives the long report bullets an editorial rhythm. Links, dates and other
# list items (they start with "[", a digit, etc.) are left untouched.
LABEL = re.compile(
    r"^(\s*)- ((?:[\u4e00-\u9fff]|[A-Za-z])[^：:\[\]()\n]{0,38})(：|:)", re.M
)


def on_config(config):
    # 给 extra.css 加内容哈希做版本号：样式一改，浏览器就会拉新文件，不会出现新页面配旧样式。
    import hashlib, os
    css = os.path.join(config["docs_dir"], "stylesheets", "extra.css")
    if os.path.exists(css):
        v = hashlib.md5(open(css, "rb").read()).hexdigest()[:8]
        config["extra_css"] = [
            f"stylesheets/extra.css?v={v}" if str(x).split("?")[0] == "stylesheets/extra.css" else x
            for x in config["extra_css"]
        ]
    js = os.path.join(config["docs_dir"], "javascripts", "header-links.js")
    if os.path.exists(js):
        v = hashlib.md5(open(js, "rb").read()).hexdigest()[:8]
        config["extra_javascript"] = [
            f"javascripts/header-links.js?v={v}" if str(x).split("?")[0] == "javascripts/header-links.js" else x
            for x in config["extra_javascript"]
        ]
    return config


def is_english(config):
    return config["theme"].get("language") == "en"


def subscription_url(placement):
    return "https://fankai.me/subscribe?" + urlencode({
        "utm_source": "news.fankai.me", "utm_medium": "website",
        "utm_campaign": "personal_articles", "utm_content": placement,
    })


def _date_parts(value):
    if isinstance(value, datetime.datetime):
        value = value.date()
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def _display_title(markdown):
    """Report H1 without the date suffix — the date is shown in the fact row."""
    m = re.search(r"^#\s+(.+?)\s*$", markdown, re.M)
    if not m:
        return None
    title = m.group(1)
    cleaned = re.sub(r"\s*[（(]\s*\d{4}-\d{2}-\d{2}\s*[)）]\s*$", "", title)
    cleaned = re.sub(r"^\d{4}-\d{2}-\d{2}\s*[-–—]?\s*", "", cleaned).strip()
    return cleaned or title.strip()


def _clean_heading(markdown):
    """Drop the date from the rendered H1 (the fact row already carries it)."""
    title = _display_title(markdown)
    if not title:
        return markdown
    m = re.search(r"^#\s+(.+?)\s*$", markdown, re.M)
    return markdown[: m.start(1)] + title + markdown[m.end(1):]


def _report_head(page, config, en, label):
    src = page.file.src_uri
    meta = page.meta
    date = _date_parts(meta.get("date"))
    facts = []
    if date:
        if en:
            value = f"{date.day} {date.strftime('%B %Y')} · {WEEKDAYS_EN[date.weekday()]}"
            date_label = "Date"
        else:
            value = f"{date.year} 年 {date.month} 月 {date.day} 日 · {WEEKDAYS_ZH[date.weekday()]}"
            date_label = "日期"
        facts.append(f'<span class="fk-fact"><span class="fk-fact__label">{date_label}</span>{value}</span>')
    window = meta.get("window")
    if window:
        facts.append(
            '<span class="fk-fact"><span class="fk-fact__label">'
            + ("Window" if en else "时间窗口")
            + f"</span>{html.escape(str(window))}</span>"
        )
    coverage = COVERAGE.get(str(meta.get("coverage", "")).lower())
    if coverage:
        facts.append(
            '<span class="fk-fact"><span class="fk-fact__label">'
            + ("Coverage" if en else "覆盖")
            + f"</span>{coverage[1] if en else coverage[0]}</span>"
        )
    root = "./" if config.get("use_directory_urls", True) is False else "../"
    back = f'<a class="fk-report-back" href="{root}">← {html.escape(label)}</a>'
    facts_html = (
        '<div class="fk-report-facts">' + "".join(facts) + "</div>" if facts else ""
    )
    return f'<p class="fk-report-back-row">{back}</p>', facts_html


def on_page_markdown(markdown, page, config, files):
    en = is_english(config)
    src = page.file.src_uri
    home = src in ("index.md", "index.en.md")
    section = src.split("/")[0] if "/" in src else ""
    is_report = section in SECTIONS and not home and not src.endswith("/index.md") and not src.endswith("/index.en.md")
    if home:
        # The landing page is not a documentation page: keep the top tabs,
        # but omit the redundant left navigation and right table of contents.
        page.meta["hide"] = list(dict.fromkeys([*page.meta.get("hide", []), "navigation", "toc"]))
        description = (
            "AI news and conversations from X, with source links. Explore daily reports and Chinese- and English-language topic briefs curated with AI."
            if en else "汇集 X 上的 AI 新闻与讨论，提供日报、中英文热点简报和原始来源入口。由范凯的 AI 工作流整理，帮助你发现值得进一步阅读的话题。"
        )
    else:
        # Report pages get a readable browser/search title such as
        # "X AI 日报 · 2026-10-20"; the nav labels stay date-only.
        report_title = _display_title(markdown) if is_report else None
        date = _date_parts(page.meta.get("date")) if is_report else None
        if report_title:
            page.meta["title"] = report_title + (f" · {date.isoformat()}" if date else "")
        # Preserve explicitly authored descriptions; otherwise derive a page-specific one.
        headings = re.findall(r"^#{2,3}\s+(.+)$", markdown, re.M)
        topics = [re.sub(r"[\[\]*`#]", "", h).strip() for h in headings]
        # 跳过“1. AI 模型、产品与应用”这类分区标题，只留具体条目。
        topics = [t for t in topics if not re.match(r"^\d+[.、]\s", t)] or topics
        label = report_title or str(page.title or "")
        if date:
            label += (" · " if en else " · ") + date.isoformat()
        # 按整条新闻截断，不在词中间断开。
        description = label + (" — " if en else "：")
        sep = "; " if en else "；"
        picked = []
        for t in topics[:4]:
            if len(description + sep.join(picked + [t])) > 155:
                break
            picked.append(t)
        description += sep.join(picked) if picked else ""
        if not picked and topics:
            description += topics[0][:150 - len(description)].rstrip() + "…"
        if date:
            # sitemap 的 lastmod 用报告日期，而不是构建日期。
            page.update_date = date.isoformat()
    page.meta.setdefault("description", description)
    if not home and (src.endswith("/index.md") or src.endswith("/index.en.md")):
        # 分类列表页：顶部标签已经是导航，左侧导航和右侧目录都是重复的。
        page.meta["hide"] = list(dict.fromkeys([*page.meta.get("hide", []), "navigation", "toc"]))
    if home:
        title = "AI news worth exploring." if en else "看懂 AI，选对下一步。"
        kicker = "FAN KAI · AI NEWS" if en else "范凯说AI · 看懂 · 选对 · 用起来"
        subtitle = (
            "Follow the news on X, then go deeper. Daily reports and topic briefs link back to sources; my personal site is where I share practice and reflection."
            if en else "在这里发现 X 上的 AI 动态与讨论，再沿着来源深入阅读。想看我的亲身实践与完整思考，欢迎到个人主站继续读。"
        )
        browse = "Browse the latest" if en else "阅读最新报告"
        subscribe = "Subscribe to my articles" if en else "免费订阅我的文章"
        hero = f'''<section class="fk-hero" aria-label="{'Introduction' if en else '网站介绍'}">
<p class="fk-eyebrow">{kicker}</p>
<h1>{title}</h1>
<p class="fk-intro">{subtitle}</p>
<div class="fk-actions"><a class="fk-button" href="#latest-reports">{browse}</a><a class="fk-button fk-button-secondary" href="{html.escape(subscription_url('home_hero'), quote=True)}">{subscribe}</a></div>
</section>'''
        markdown = re.sub(r"^# .+\n", "", markdown, count=1)
        markdown = markdown.replace("## 最新报告", "## 最新报告 {#latest-reports}").replace("## Latest reports", "## Latest reports {#latest-reports}")
        return hero + "\n\n" + markdown
    if is_report:
        label = SECTIONS[section][1 if en else 0]
        back_row, facts = _report_head(page, config, en, label)
        markdown = _clean_heading(markdown)
        m = re.search(r"^#\s+.+$", markdown, re.M)
        if m:
            markdown = markdown[: m.end()] + "\n\n" + facts + markdown[m.end():]
        markdown = back_row + "\n\n" + markdown
    markdown = LABEL.sub(
        lambda m: f'{m.group(1)}- <span class="fk-label">{html.escape(m.group(2))}</span>{m.group(3)}',
        markdown,
    )
    return markdown


def on_page_content(html_content, page, config, files):
    # 订阅卡片只放在报告页和分类列表页：首页已有顶部按钮，不再重复。
    if page.file.src_uri in ("index.md", "index.en.md"):
        return html_content
    en = is_english(config)
    title = "Beyond the headlines" if en else "新闻之外，读一点亲身实践。"
    body = (
        "I’m Fan Kai. I share hands-on AI workflows, reading notes and personal reflections. Subscribe free to receive new articles in Chinese, at my writing pace."
        if en else "我是范凯。除了关注 AI 动态，我也分享亲自用过的工具、真实工作流，以及读书与生活中的思考。免费订阅，在我发送新文章时通过邮件收到。"
    )
    label = "Subscribe free · Chinese articles" if en else "免费邮件订阅"
    note = (
        "No fixed schedule. Unsubscribe anytime. This is not a daily or weekly news email."
        if en else "按实际创作节奏更新，随时退订。这不是日报或周报邮件订阅。"
    )
    return html_content + f'''<aside class="fk-subscribe" aria-label="{'Email subscription' if en else '邮件订阅'}">
<p class="fk-eyebrow">{'PERSONAL WRITING' if en else '个人写作'}</p><h2>{title}</h2>
<p>{body}</p><a class="fk-button" href="{html.escape(subscription_url('page_footer'), quote=True)}">{label}</a>
<p class="fk-fineprint">{note}</p></aside>'''
