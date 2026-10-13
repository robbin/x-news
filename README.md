# x-news · 范凯说AI · X 情报

MkDocs Material site, deployed to GitHub Pages by `.github/workflows/deploy.yml` on every push to `main`.
Site: https://robbin.github.io/x-news/  Repo: https://github.com/robbin/x-news

## Layout
- `docs/{Daily,Chinese-Topics,English-Topics,High-Traffic}/*.md` — reports (YAML frontmatter `title`, `date` used if present; else first `#` heading / filename date).
- `hooks/autonav.py` — at build time generates nav, each category `index.md` and the homepage (newest first). Never edit mkdocs.yml to add reports. Generated `index.md` files are overwritten at build; don't hand-edit them.

## Sync procedure (git via gh)
Run `/workspace/news-site/sync.sh`. `/workspace/news-site` is a git clone of robbin/x-news (auth via `gh auth setup-git`). The script pulls, mirrors `/workspace/News/<cat>/*.md` into `docs/<cat>/` (deleting reports removed from the source) (generated `index.md` kept), commits and pushes to `main` if anything changed. The push triggers the Pages workflow; check with `gh run list -R robbin/x-news` / `gh run watch -R robbin/x-news`. Site updates in ~1–2 min.
