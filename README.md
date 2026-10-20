# x-news · 范凯说AI · X 新闻

MkDocs Material site, deployed to GitHub Pages by `.github/workflows/deploy.yml` on every push to `main`.
Site: https://news.fankai.me/  Repo: https://github.com/robbin/x-news

## Layout
- `docs/{Daily,Chinese-Topics,English-Topics,High-Traffic}/*.md` — reports (YAML frontmatter `title`, `date` used if present; else first `#` heading / filename date).
- `hooks/autonav.py` — at build time generates nav, each category `index.md` and the homepage (newest first). Never edit mkdocs.yml to add reports. Generated `index.md` files are overwritten at build; don't hand-edit them.
- `hooks/presentation.py` — adds the bilingual homepage introduction, page descriptions and email subscription CTA at build time. It does not modify report sources. Design lives in `docs/stylesheets/extra.css`.

## Email subscriptions

All current subscription links lead to the personal publication at `fankai.me/subscribe`. These are Chinese personal articles, not daily or weekly news emails. UTM parameters distinguish the header, homepage hero, page footer and site footer; attribution availability depends on the destination analytics.

A future weekly digest should have its own explicit opt-in (for example, a separate Substack section) and a verified subscription URL before adding a second CTA. Do not enroll existing article subscribers automatically or promise a schedule before the editorial workflow is ready. Keep report generation/sync under Jarvis; no credentials or subscriber data belong in this public repository.

## Local validation

```sh
uv run --with-requirements requirements.txt mkdocs build --strict
uv run python -m unittest discover -s tests
```

The build regenerates tracked index files. Do not include unrelated generated index changes in presentation-only commits.

## Sync procedure (git via gh)
Run `/workspace/news-site/sync.sh`. `/workspace/news-site` is a git clone of robbin/x-news (auth via `gh auth setup-git`). The script pulls, mirrors `/workspace/News/<cat>/*.md` into `docs/<cat>/` (deleting reports removed from the source) (generated `index.md` kept), commits and pushes to `main` if anything changed. The push triggers the Pages workflow; check with `gh run list -R robbin/x-news` / `gh run watch -R robbin/x-news`. Site updates in ~1–2 min.

## Bilingual (中文 / English)
- Plugin `mkdocs-static-i18n` (suffix layout): `foo.md` = Chinese (default, served at `/`), `foo.en.md` = English (served at `/en/`). Missing `.en.md` falls back to Chinese.
- Switch: Material language selector + a `中文/EN` pill at the top-right (`docs/javascripts/header-links.js`); both jump to the same article in the other language.
- `hooks/autonav.py` also generates `index.en.md` (home + each category). English titles come from the `.en.md` frontmatter `title`.
- English reports live next to the Chinese ones in `/workspace/News/<cat>/` as `<same name>.en.md`; `sync.sh` mirrors both.
