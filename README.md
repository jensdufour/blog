# Blog

This repo is the **single source of truth** for the blog. All posts (Markdown) and media (images) live here.

- **GitHub Pages**: Posts are rendered as a static site at `https://<username>.github.io/blog/`
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

Save Greenshot captures directly into the `media/<slug>/` folder — **any filename works**. The GitHub Actions workflow will automatically rename them to follow the convention (`<slug>-01.png`, `<slug>-02.png`, ...) and update your markdown references on push.

### 3. Write the post

Reference images in your Markdown:

```markdown
![Description of the screenshot](media/my-article-title/my-article-title-01.png)
```

### 4. Publish

```bash
git add -A
git commit -m "Add article: My Article Title"
git push
```

The GitHub Actions workflow will convert your Markdown to HTML, upload images to WordPress, and publish the post.

## How it works

| Direction | Trigger | What happens |
|---|---|---|
| **GitHub → WordPress** | Push to `main` (changes in `_posts/` or `media/`) | Markdown is converted to HTML, local images are uploaded to WP Media Library, and posts are published/updated via the WP REST API |
| **GitHub → GitHub Pages** | Push to `main` | Jekyll builds the site and deploys to GitHub Pages |

Mapping files track sync state:
- `.post-mapping.json` — slug ↔ WordPress post ID and content hashes
- `.media-mapping.json` — WordPress media URL ↔ local file path (created automatically on first push)

## Repo structure

```
blog/
├── _posts/              # Markdown files (Jekyll naming: YYYY-MM-DD-slug.md)
│   └── 2026-03-09-my-post.md
├── _layouts/            # Jekyll HTML layouts
├── media/               # All images, organized per article
│   └── my-post/
│       ├── my-post-01.png
│       └── my-post-02.png
├── scripts/
│   ├── new_post.py      # Scaffold a new post + media directory
│   ├── rename_media.py  # Auto-rename images to <slug>-NN convention
│   ├── sync_to_wp.py    # GitHub → WordPress sync
│   └── requirements.txt
├── .github/workflows/
│   ├── push-to-wp.yml   # Syncs posts to WP on push
│   └── deploy-pages.yml # Builds and deploys GitHub Pages
├── _config.yml          # Jekyll configuration
├── index.md             # Homepage listing all posts
├── .post-mapping.json   # Post sync state
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

![Screenshot](media/my-post-title/my-post-title-01.png)
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
| `featured_image` | No | Relative path to the featured image in `media/` |
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
