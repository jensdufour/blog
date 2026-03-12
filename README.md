# Blog

This repo is the **single source of truth** for the blog. All posts (Markdown) and media (images) live here.

- **WordPress sync**: On push to `main`, changed posts and images are synced to WordPress via the REST API

## Creating a new article

### 1. Scaffold the post

```bash
python scripts/new_post.py "My Article Title"
python scripts/new_post.py "My Article Title" --status publish --categories Linux Microsoft --tags Intune MDM
```

This creates:
- `_posts/YYYY-MM-DD-my-article-title.md` — Markdown file with frontmatter
- `media/my-article-title/` — directory for screenshots

### 2. Add screenshots

Save Greenshot captures directly into the `media/<slug>/` folder — **any filename works**. The GitHub Actions workflows will automatically rename them to follow the convention (`<slug>-01.png`, `<slug>-02.png`, ...), convert them to WebP for smaller file sizes, and update your markdown references on push.

### 3. Write the post

Reference images in your Markdown:

```markdown
![Description of the screenshot](../media/my-article-title/my-article-title-01.webp)
```

### 4. Publish

```bash
git add -A
git commit -m "Add article: My Article Title"
git push
```

The GitHub Actions workflow will convert your Markdown to HTML and publish the post. Images are served directly from GitHub — nothing is uploaded to WordPress.

## How it works

| Workflow | Trigger | What happens |
|---|---|---|
| **Optimize media** | Push to `main` changing `media/**` | Renames images to `<slug>-NN` convention, converts to WebP, commits changes |
| **Deploy theme** | Push to `main` changing `theme/**` | Deploys the WordPress theme via rsync over SSH |
| **Sync to WordPress** | Push to `main` changing `_posts/**`, `_pages/**`, or after Optimize media completes | Converts Markdown to HTML, rewrites image paths to GitHub raw URLs, publishes via the WP REST API |

Mapping files track sync state:
- `.post-mapping.json` — slug ↔ WordPress post ID and content hashes

## Repo structure

```
blog/
├── _posts/              # Markdown files (YYYY-MM-DD-slug.md)
│   └── 2026-03-09-my-post.md
├── _pages/              # Static pages synced to WordPress
├── media/               # All images, organized per article
│   └── my-post/
│       ├── my-post-01.webp
│       └── my-post-02.webp
├── theme/               # WordPress theme (deployed via rsync)
├── scripts/
│   ├── new_post.py      # Scaffold a new post + media directory
│   ├── optimize_media.py # Convert images to WebP
│   ├── rename_media.py  # Auto-rename images to <slug>-NN convention
│   ├── sync_to_wp.py    # GitHub → WordPress sync
│   └── requirements.txt
├── .github/workflows/
│   ├── optimize-media.yml # Renames & converts images on media/ changes
│   ├── deploy-theme.yml   # Deploys WP theme on theme/ changes
│   └── sync-to-wp.yml    # Syncs posts & pages to WP on content changes
├── .post-mapping.json   # Post sync state
├── .page-mapping.json   # Page sync state
└── README.md
```

## Post format

```markdown
---
title: 'My Post Title'
date: '2026-03-09'
status: draft
seo_title: 'My Post Title - A Complete Guide'
meta_description: 'Learn how to do X with step-by-step instructions.'
focus_keyphrase: 'my post title'
categories:
- Tech
- Tutorial
tags:
- python
- automation
---

Your Markdown content here.

![Screenshot](../media/my-post-title/my-post-title-01.webp)
```

### Frontmatter fields

| Field | Required | Description |
|---|---|---|
| `title` | No | Post title (defaults to slug if omitted) |
| `date` | No | Publish date in `YYYY-MM-DD` or ISO 8601 format |
| `status` | No | `draft` or `publish` (defaults to `draft`) |
| `seo_title` | No | Yoast SEO title override |
| `meta_description` | No | Yoast meta description |
| `focus_keyphrase` | No | Yoast focus keyphrase |
| `featured_image` | No | Relative path to the featured image in `media/` (e.g. `../media/slug/slug-01.png`) |
| `categories` | No | List of category names |
| `tags` | No | List of tag names |

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
