# Blog

This repo is the **single source of truth** for your blog. It contains all posts (as Markdown) and all media (images), making it fully portable.

- **GitHub Pages**: Posts are rendered as a static site at `https://<username>.github.io/blog/`
- **WordPress sync**: On push to `main`, posts and images are synced to WordPress via the REST API

Deploy a fresh WordPress site, run the sync, and everything is up and running.

## How it works

| Direction | Trigger | What happens |
|---|---|---|
| **GitHub → WordPress** | Push to `main` (changes in `_posts/` or `media/`) | Markdown is converted to HTML, local images are uploaded to WP Media Library, and posts are published/updated via the WP REST API |
| **GitHub → GitHub Pages** | Push to `main` | Jekyll builds the site and deploys to GitHub Pages |

Two mapping files track sync state:
- `.post-mapping.json` — slug ↔ WordPress post ID, content hashes, timestamps
- `.media-mapping.json` — WordPress media URL ↔ local file path

## Repo structure

```
blog/
├── _posts/              # Markdown files (Jekyll naming: YYYY-MM-DD-slug.md)
│   └── 2026-03-08-my-post.md
├── _layouts/            # Jekyll HTML layouts
├── media/               # All images/media, mirroring WP uploads structure
│   └── 2026/
│       └── 03/
│           └── image.jpg
├── scripts/
│   ├── sync_to_wp.py    # GitHub → WordPress
│   ├── sync_from_wp.py  # Initial import from WordPress
│   └── requirements.txt
├── .github/workflows/
│   ├── push-to-wp.yml   # Syncs posts to WP on push
│   └── deploy-pages.yml # Builds and deploys GitHub Pages
├── _config.yml          # Jekyll configuration
├── index.md             # Homepage listing all posts
├── .post-mapping.json
├── .media-mapping.json
└── README.md
```

## Post format

Posts live in `_posts/` as Markdown files with YAML frontmatter. Filenames must follow Jekyll's `YYYY-MM-DD-slug.md` convention:

```markdown
---
title: "My Post Title"
date: 2026-03-08
status: publish
featured_image: media/2026/03/hero.jpg
categories:
  - Tech
  - Tutorial
tags:
  - python
  - automation
---

Your Markdown content here.

![Screenshot](media/2026/03/screenshot.png)
```

### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `title` | No | Post title (defaults to slug if omitted) |
| `date` | No | Publish date in `YYYY-MM-DD` or ISO 8601 format |
| `status` | No | `draft` or `publish` (defaults to `draft`) |
| `featured_image` | No | Relative path to the featured image in `media/` |
| `categories` | No | List of category names |
| `tags` | No | List of tag names |

The slug is derived from the filename: `2026-03-08-my-first-post.md` → slug `my-first-post`.

## Images and media

- **All images are stored in the repo** under `media/`, preserving the WP uploads date structure (`media/YYYY/MM/filename`)
- When pushing to WordPress, local images are uploaded to the WP Media Library and URLs are rewritten automatically
- The `.media-mapping.json` file tracks which local files map to which WP URLs to avoid re-uploading

## Setup

### 1. WordPress: Create an Application Password

1. In your WordPress admin, go to **Users → Profile**
2. Scroll to **Application Passwords**
3. Enter a name (e.g., `github-sync`) and click **Add New Application Password**
4. Copy the generated password

### 2. GitHub: Add repository secrets

Go to your repo **Settings → Secrets and variables → Actions** and add:

| Secret | Value |
|---|---|
| `WP_URL` | Your WordPress site URL, e.g., `https://yourblog.com` |
| `WP_USER` | Your WordPress username |
| `WP_APP_PASSWORD` | The application password from step 1 |

### 3. Enable GitHub Pages

Go to **Settings → Pages** and set the source to **GitHub Actions**.

### 4. Initial import from an existing WordPress site (optional)

To pull all existing posts and media into the repo once:

```bash
export WP_URL="https://yourblog.com"
export WP_USER="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
pip install -r scripts/requirements.txt
python scripts/sync_from_wp.py
```

This will populate `_posts/`, `media/`, `.post-mapping.json`, and `.media-mapping.json`.

### 5. Deploying to a fresh WordPress site

1. Set up a new WordPress installation
2. Create an Application Password (step 1 above)
3. Update the `WP_URL` secret (and credentials) to point to the new site
4. Clear `.post-mapping.json` and `.media-mapping.json` (set both to `{}`)
5. Run the push workflow manually, or run locally:

```bash
export WP_URL="https://new-site.com"
export WP_USER="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
python scripts/sync_to_wp.py
```

All posts and images will be created on the new site.
