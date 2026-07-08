"""
Archive Jekyll posts into a JSON file Ghost can import.
"""

__author__ = "Richard Si"

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "click",
#   "rich",
#   "python-frontmatter",
#   "markdown-it-py[plugins]",
#   "PyYaml",
# ]
# ///

import json
import subprocess
import zipfile
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from pprint import pprint
from urllib.parse import urlsplit

import click
import frontmatter
import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from rich.progress import track


class Counter:
    def __init__(self):
        self.counter = 0

    def id(self, type: str) -> str:
        self.counter += 1
        return f"{type}-{self.counter}"


@dataclass(frozen=True)
class Post:
    id: int
    title: str
    slug: str
    html: str
    authors: "list[Author] | None"
    feature_image: str | None
    image_alt: str | None
    created_at: str
    updated_at: str

    def to_json(self) -> dict[str, str]:
        payload = asdict(self)
        del payload["authors"]
        del payload["image_alt"]
        payload["published_at"] = self.created_at
        payload["visibility"] = "public"
        payload["status"] = "published"
        payload["type"] = "post"
        return payload


@dataclass(frozen=True)
class Author:
    id: str
    slug: str
    name: str

    def to_json(self) -> dict[str, str]:
        payload = asdict(self)
        payload["roles"] = ["Contributor"]
        payload["email"] = f"jekyll-imported-{self.slug}@tritag.ca"
        return payload


def convert_image_href(href: str) -> str:
    parsed = urlsplit(href)
    assert parsed.path, f"no URL path in image link?!, {parsed.path}"
    img_name = parsed.path.split("/")[-1]
    return f"/jekyll-import/{img_name}"


def rewrite_image_url(self, tokens, idx, options, env):
    token = tokens[idx]
    src = token.attrs["src"]
    # print("image |", token.attrs["src"])
    if src.startswith("images/") or src.startswith("https://tritag.ca/images/"):
        token.attrs["src"] = convert_image_href(src)
    return self.image(tokens, idx, options, env)


def transform_link(self, tokens, idx, options, env):
    token = tokens[idx]
    href = token.attrs["href"]
    if href.startswith("/images/") or href.startswith("https://tritag.ca/images/z"):
        token.attrs["href"] = convert_image_href(href)
    return self.renderToken(tokens, idx, options, env)


@click.command
@click.argument(
    "export-path", type=click.Path(exists=False, writable=True, path_type=Path)
)
def main(export_path: Path) -> None:
    c = Counter()
    md = (
        MarkdownIt("commonmark", {"breaks": True, "html": True})
        .use(footnote_plugin)
        .enable("table")
    )
    md.add_render_rule("image", rewrite_image_url)
    md.add_render_rule("link_open", transform_link)

    # Process authors
    authors_file = Path.cwd() / "_data" / "authors.yml"
    authors_yaml = yaml.load(authors_file.read_text("utf-8"), yaml.Loader)
    authors = {}
    for nick, data in authors_yaml.items():
        authors[nick] = Author(c.id("author"), nick, data["name"])

    # Process posts
    tags = defaultdict(set)
    posts = {}
    post_paths = list(Path(".", "_posts").iterdir())
    for post_file in track(post_paths, description="Processing posts", transient=True):
        post = frontmatter.loads(post_file.read_text("utf-8"))
        post_id = c.id("post")
        slug = post_file.stem.split("-", maxsplit=3)[-1]

        # So many different ways of declaring authors...
        post_author = None
        if "author" in post.metadata:
            post_author = [authors[post.metadata["author"]]]
        elif author_list := post.metadata.get("authors"):
            if isinstance(author_list, str):
                post_author = [authors[author_list]]
            else:
                post_author = [authors[a] for a in author_list]
        img = (
            post.metadata.get("coverImage", None) or
            post.metadata.get("image", {}).get("path", None)
        )
        created_at = post.metadata["date"]
        if isinstance(created_at, (date, datetime)):
            created_at = created_at.isoformat()

        # Get last updated field if it exists from Git
        updated_at = created_at
        rev_count = int(subprocess.run(
            ["git", "rev-list", "--count", "HEAD", post_file],
            capture_output=True, encoding="utf-8", check=True
        ).stdout)
        if rev_count > 1:
            updated_at = subprocess.run(
                ["git", "log" , "-1", "--pretty=%ad", "--date=iso", "--", post_file],
                capture_output=True, encoding="utf-8", check=True
            ).stdout.strip()

        # Deal with slug conflicts
        if slug in posts:
            before = f"/blog/{created_at.replace('-', '/')}/{slug}/"
            i = 2
            while f"{slug}-{i}" in posts:
                i += 1
            slug = f"{slug}-{i}"
            after = "/".join([*before.split("/")[:-2], slug]) + "/"
            print(f"{before}: {after}")
        posts[slug] = Post(
            id=post_id,
            title=post.metadata["title"],
            slug=slug,
            html=md.render(post.content),
            authors=post_author,
            feature_image=convert_image_href(img) if img else img,
            image_alt=post.metadata.get("image", {}).get("alt", None),
            created_at=created_at,
            updated_at=updated_at,
        )
        if posts[slug].title == "News roundup: December 9, 2025":
            print(posts[slug].html)

        # Link post to tags
        for t in post.metadata.get("tags", []):
            tags[t].add(post_id)
        for t in post.metadata.get("categories", []):
            tags[t].add(post_id)
        if slug == "news-roundup":
            tags["round-up"].add(post_id)

    # Generate final JSON
    tags_blob = []
    post_tags_blob = []
    for tag, post_ids in tags.items():
        if len(post_ids) <= 2:
            # print(f"Excluding tag {tag} as it has only been used once/twice")
            continue

        tag = {
            "elections": "election",
            "round-up": "news roundup",
        }.get(tag, tag)

        if not tag:
            continue

        print(tag, len(post_ids))
        tag_id = c.id("tag")
        tags_blob.append({"id": tag_id, "name": tag, "slug": tag})
        for pid in post_ids:
            post_tags_blob.append({"post_id": pid, "tag_id": tag_id})

    post_authors_blob = [
        {"post_id": p.id, "author_id": author.id}
        for p in posts.values() if p.authors
        for author in p.authors
    ]
    post_meta_blob = [
        {"post_id": p.id, "feature_image_alt": p.image_alt}
        for p in posts.values() if p.image_alt
    ]

    blob = {
        "meta": {"exported_on": int(datetime.now().timestamp() * 1000), "version": "6.0.0"},
        "data": {
            "posts": [p.to_json() for p in posts.values()],
            "tags": tags_blob,
            "users": [u.to_json() for u in authors.values()],
            "posts_tags": post_tags_blob,
            "posts_meta": post_meta_blob,
            "posts_authors": post_authors_blob,
        }
    }
    with zipfile.ZipFile(export_path, "w") as zf:
        zf.writestr("db.json", json.dumps(blob, indent=2))
        zf.mkdir("jekyll-import")
        for img_path in Path(".", "images").iterdir():
            zf.write(img_path, f"jekyll-import/{img_path.name}")


main()
