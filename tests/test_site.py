"""Run after mkdocs build; validate the rendered bilingual subscription paths."""
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse, parse_qs


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.links = []
        self.descriptions = []
        self.canonicals = []
        self.h1 = 0
        self.hidden_sidebars = []
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('data-md-component') == 'sidebar' and 'hidden' in a:
            self.hidden_sidebars.append(a.get('data-md-type'))
        if tag == 'a':
            self.links.append(a.get('href', ''))
        if tag == 'meta' and a.get('name') == 'description':
            self.descriptions.append(a.get('content', ''))
        if tag == 'link' and a.get('rel') == 'canonical':
            self.canonicals.append(a.get('href', ''))
        if tag == 'h1':
            self.h1 += 1


class SiteTest(unittest.TestCase):
    def test_home_languages(self):
        for path, phrase in [('index.html', '每天的 AI 新闻与选题，来自 X'),
                             ('en/index.html', 'Daily AI news and topics from X')]:
            file = Path('site') / path
            self.assertIn(phrase, file.read_text())
            page = Page(file)
            self.assertEqual(page.h1, 1)
            self.assertEqual(set(page.hidden_sidebars), {'navigation', 'toc'})
            self.assertTrue(page.descriptions[0])
            self.assertTrue(page.canonicals[0].startswith('https://news.fankai.me/'))

    def test_all_reports_have_subscription_and_description(self):
        reports = list(Path('site/Daily').glob('*/index.html')) + list(Path('site/en/Daily').glob('*/index.html'))
        self.assertTrue(reports)
        for file in reports:
            with self.subTest(file=file):
                page = Page(file)
                self.assertTrue(page.descriptions[0])
                self.assertEqual(page.hidden_sidebars, [])
                links = [urlparse(link) for link in page.links if 'utm_content=page_footer' in link]
                self.assertEqual(len(links), 1)
                self.assertEqual(links[0].netloc, 'fankai.me')
                self.assertEqual(links[0].path, '/subscribe')
                self.assertEqual(parse_qs(links[0].query)['utm_campaign'], ['personal_articles'])

    def test_robots(self):
        self.assertIn('Sitemap: https://news.fankai.me/sitemap.xml', Path('site/robots.txt').read_text())


if __name__ == '__main__':
    unittest.main()
