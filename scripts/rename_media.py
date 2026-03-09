"""Rename media files to follow a per-article naming convention.

Convention:  media/<slug>/<slug>-01.png, media/<slug>/<slug>-02.png, ...

Images are numbered in the order they appear in each post.
Updates all markdown references and the .media-mapping.json file.
"""

import json
import re
import shutil
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT_DIR / "_posts"
MEDIA_DIR = ROOT_DIR / "media"
MEDIA_MAPPING_FILE = ROOT_DIR / ".media-mapping.json"

IMG_PATTERN = re.compile(r"(!\[[^\]]*\])\((media/[^)]+)\)")


def extract_slug(filename: str) -> str:
    """Extract slug from a Jekyll post filename like 2025-08-01-my-post.md."""
    # Strip .md and the YYYY-MM-DD- prefix
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", filename.removesuffix(".md"))


def main() -> None:
    # Load media mapping
    media_mapping: dict = {}
    if MEDIA_MAPPING_FILE.exists():
        media_mapping = json.loads(MEDIA_MAPPING_FILE.read_text(encoding="utf-8"))

    # Build reverse mapping: old local path → list of remote URLs
    reverse_map: dict[str, list[str]] = {}
    for url, local in media_mapping.items():
        reverse_map.setdefault(local, []).append(url)

    # Collect all renames: old_path → new_path
    all_renames: dict[str, str] = {}

    for post_file in sorted(POSTS_DIR.glob("*.md")):
        slug = extract_slug(post_file.name)
        content = post_file.read_text(encoding="utf-8")

        # Find all image references in order
        matches = list(IMG_PATTERN.finditer(content))
        if not matches:
            continue

        # Deduplicate: if same image appears twice, it gets one number
        seen: dict[str, str] = {}
        counter = 0

        for match in matches:
            old_path = match.group(2)
            if old_path in seen:
                continue

            counter += 1
            ext = Path(old_path).suffix
            new_path = f"media/{slug}/{slug}-{counter:02d}{ext}"
            seen[old_path] = new_path
            all_renames[old_path] = new_path

        # Rewrite references in the post content
        def replace_ref(m: re.Match) -> str:
            alt = m.group(1)
            old = m.group(2)
            new = seen.get(old, old)
            return f"{alt}({new})"

        new_content = IMG_PATTERN.sub(replace_ref, content)

        # Also rewrite featured_image in frontmatter
        for old, new in seen.items():
            new_content = new_content.replace(f"featured_image: {old}", f"featured_image: {new}")

        if new_content != content:
            post_file.write_text(new_content, encoding="utf-8")
            print(f"Updated {post_file.name}")

    if not all_renames:
        print("No images to rename.")
        return

    # Move files on disk
    for old_path, new_path in all_renames.items():
        src = ROOT_DIR / old_path
        dst = ROOT_DIR / new_path
        if not src.exists():
            print(f"  WARNING: {old_path} does not exist, skipping")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        print(f"  {old_path} → {new_path}")

    # Update media mapping
    new_mapping: dict[str, str] = {}
    for url, old_local in media_mapping.items():
        new_local = all_renames.get(old_local, old_local)
        new_mapping[url] = new_local
    MEDIA_MAPPING_FILE.write_text(
        json.dumps(new_mapping, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print("Updated .media-mapping.json")

    # Clean up empty directories in media/
    for dirpath in sorted(MEDIA_DIR.rglob("*"), reverse=True):
        if dirpath.is_dir() and not any(dirpath.iterdir()):
            dirpath.rmdir()
            print(f"  Removed empty dir: {dirpath.relative_to(ROOT_DIR)}")

    print(f"Done. Renamed {len(all_renames)} images.")


if __name__ == "__main__":
    main()
