"""Presentation only: no changes to report sources or the report sync process."""
import html
import re
from urllib.parse import urlencode


def is_english(config):
    return config["theme"].get("language") == "en"


def subscription_url(placement):
    return "https://fankai.me/subscribe?" + urlencode({
        "utm_source": "news.fankai.me", "utm_medium": "website",
        "utm_campaign": "personal_articles", "utm_content": placement,
    })


def on_page_markdown(markdown, page, config, files):
    en = is_english(config)
    home = page.file.src_uri in ("index.md", "index.en.md")
    if home:
        # The landing page is not a documentation page: keep the top tabs,
        # but omit the redundant left navigation and right table of contents.
        page.meta["hide"] = list(dict.fromkeys([*page.meta.get("hide", []), "navigation", "toc"]))
        description = (
            "AI news and conversations from X, with source links. Explore daily reports and Chinese- and English-language topic briefs curated with AI."
            if en else "汇集 X 上的 AI 新闻与讨论，提供日报、中英文热点简报和原始来源入口。由范凯的 AI 工作流整理，帮助你发现值得进一步阅读的话题。"
        )
    else:
        # Preserve explicitly authored descriptions; otherwise derive a page-specific one.
        headings = re.findall(r"^#{2,3}\s+(.+)$", markdown, re.M)
        topics = [re.sub(r"[\[\]*`#]", "", h).strip() for h in headings]
        description = str(page.title or "") + (" — " if en else "：") + "; ".join(topics[:4])
        description = description[:155]
    page.meta.setdefault("description", description)
    if not home:
        return markdown
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
<p class="fk-fineprint">{'Email articles are in Chinese. News reports remain freely available here.' if en else '新闻在网页上免费阅读；邮件订阅接收我的个人文章，不是每日新闻推送。'}</p>
</section>'''
    markdown = re.sub(r"^# .+\n", "", markdown, count=1)
    markdown = markdown.replace("## 最新报告", '<span id="latest-reports"></span>\n\n## 最新报告').replace("## Latest reports", '<span id="latest-reports"></span>\n\n## Latest reports')
    return hero + "\n\n" + markdown


def on_page_content(html_content, page, config, files):
    # 订阅卡片只放在报告页：首页已有顶部按钮，分类列表页不需要。
    src = page.file.src_uri
    if src in ("index.md", "index.en.md") or src.endswith("/index.md") or src.endswith("/index.en.md"):
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
<p class="fk-eyebrow">{'STAY IN TOUCH' if en else '和范凯保持联系'}</p><h2>{title}</h2>
<p>{body}</p><a class="fk-button" href="{html.escape(subscription_url('page_footer'), quote=True)}">{label}</a>
<p class="fk-fineprint">{note}</p></aside>'''
