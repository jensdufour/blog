"""Scaffold a new blog post with frontmatter and media directory.

Usage:
    python scripts/new_post.py "My Article Title"
    python scripts/new_post.py "My Article Title" --status publish
    python scripts/new_post.py "My Article Title" --categories Linux Microsoft --tags Intune MDM
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "_posts"
MEDIA_DIR = ROOT_DIR / "media"


def slugify(title: str) -> str:
    """Convert a title to a URL-friendly slug."""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new blog post.")
    parser.add_argument("title", help="The post title")
    parser.add_argument("--status", default="draft", choices=["draft", "publish"])
    parser.add_argument("--categories", nargs="+", default=[])
    parser.add_argument("--tags", nargs="+", default=[])
    args = parser.parse_args()

    today = date.today().isoformat()
    slug = slugify(args.title)
    filename = f"{today}-{slug}.md"
    filepath = POSTS_DIR / filename
    media_dir = MEDIA_DIR / slug

    if filepath.exists():
        print(f"Post already exists: {filepath}", file=sys.stderr)
        sys.exit(1)

    # Build frontmatter
    categories_yaml = ""
    if args.categories:
        items = "\n".join(f"- {c}" for c in args.categories)
        categories_yaml = f"categories:\n{items}\n"

    tags_yaml = ""
    if args.tags:
        items = "\n".join(f"- {t}" for t in args.tags)
        tags_yaml = f"tags:\n{items}\n"

    frontmatter = f"""---
title: '{args.title}'
date: '{today}'
status: {args.status}
seo_title: ''
meta_description: ''
focus_keyphrase: ''
{categories_yaml}{tags_yaml}---

## Introduction

Write your introduction here.

<!-- Screenshots: save Greenshot captures to media/{slug}/ -->
<!-- Reference: ![alt text](../media/{slug}/{slug}-01.png) -->
"""

    # Create post file and media directory
    filepath.write_text(frontmatter, encoding="utf-8")
    media_dir.mkdir(parents=True, exist_ok=True)

    print(f"Created post:  {filepath.relative_to(ROOT_DIR)}")
    print(f"Media folder:  {media_dir.relative_to(ROOT_DIR)}")
    print()
    print("Next steps:")
    print(f"  1. Save Greenshot screenshots to: {media_dir}")
    print(f"     Naming convention: {slug}-01.png, {slug}-02.png, ...")
    print(f"  2. Edit {filepath.relative_to(ROOT_DIR)}")
    print(f"  3. Reference images: ![description](media/{slug}/{slug}-01.png)")
    print(f"  4. Commit and push to sync to WordPress")


if __name__ == "__main__":
    main()
