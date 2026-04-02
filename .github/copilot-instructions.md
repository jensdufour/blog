# Copilot Instructions

## Architecture

This is a **blog-as-code** repository. Posts and pages are authored in Markdown with YAML frontmatter and automatically synced to WordPress via GitHub Actions. Images are served from GitHub raw URLs — nothing is uploaded to WordPress.

**Publish pipeline (triggered on push to `main`):**

1. `optimize-media.yml` — renames images to `<slug>-NN` convention, converts to WebP, commits changes
2. `sync-to-wp.yml` — converts Markdown to HTML, rewrites image paths to GitHub raw URLs, publishes via WP REST API (also runs after optimize-media completes)
3. `deploy-theme.yml` — deploys the WordPress block theme via rsync over SSH

Sync state is tracked in `.post-mapping.json` and `.page-mapping.json` (slug → WordPress ID + content hash). These are auto-committed by CI — do not edit manually.

## Scripts

All scripts are Python 3.12. Install dependencies with `pip install -r scripts/requirements.txt`.

| Command | Purpose |
|---|---|
| `python scripts/new_post.py "Title"` | Scaffold a new post + media directory |
| `python scripts/new_post.py "Title" --status publish --categories Linux --tags Intune` | Scaffold with metadata |
| `python scripts/rename_media.py` | Rename images to `<slug>-NN` convention |
| `python scripts/optimize_media.py` | Convert images to WebP (85% quality) |

`sync_to_wp.py` requires `WP_URL`, `WP_USER`, and `WP_APP_PASSWORD` environment variables and is designed to run in CI.

## Post conventions

- **Filename**: `_posts/YYYY-MM-DD-slug.md`
- **Media directory**: `media/<slug>/` with images named `<slug>-01.webp`, `<slug>-02.webp`, etc.
- **Image references**: `![alt text](../media/<slug>/<slug>-01.webp)` (relative path with `../media/`)
- **Status**: `draft` (default) or `publish`

### Frontmatter template

```yaml
---
title: 'Post Title'
date: 'YYYY-MM-DD'
status: draft
seo_title: 'SEO Title Override'
meta_description: 'Meta description for search engines.'
focus_keyphrase: 'primary keyword'
categories:
- Category1
- Category2
tags:
- Tag1
- Tag2
---
```

All frontmatter fields except the `---` delimiters are optional. The Yoast SEO fields (`seo_title`, `meta_description`, `focus_keyphrase`) are synced to the WordPress Yoast plugin.

## Pages

Static pages live in `_pages/` as `<slug>.md` with the same frontmatter format (no date in filename). They sync to WordPress the same way posts do.

## Theme

`theme/` is a WordPress block theme (theme.json v3, FSE templates in `templates/` and `parts/`). Changes are deployed via rsync — do not reference WordPress admin for theme edits.
