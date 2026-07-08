"""
Fix imported Jekyll posts via the Ghost Content API.
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
#   "urllib3",
#   "pyjwt",
# ]
# ///

import os
import subprocess
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from pathlib import Path
from pprint import pprint
from urllib.parse import urlsplit

import click
import frontmatter
import yaml
import urllib3
import jwt
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin
from rich.progress import track

GHOST_API_TOKEN = os.getenv("GHOST_API_TOKEN")


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
def main() -> None:
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
            # print(f"{before}: {after}")
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
        if posts[slug].title == "News roundup: December 9, 2025" and False:
            print(posts[slug].html)

        # Link post to tags
        for t in post.metadata.get("tags", []):
            tags[t].add(post_id)
        for t in post.metadata.get("categories", []):
            tags[t].add(post_id)
        if slug == "news-roundup":
            tags["round-up"].add(post_id)

    issue_updates(posts)


def create_jwt(key) -> str:
    id, secret = key.split(':')
    iat = int(datetime.now().timestamp())

    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': '/admin/'
    }
    return jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)


def ghost_request(pool, method, url, *, json=None) -> urllib3.HTTPResponse:
    headers = {"Authorization": f"Ghost {create_jwt(GHOST_API_TOKEN)}"}
    url = f"https://www.tritag.ca/ghost/api/admin{url}"
    print(f"[{method}]", url, end=" ")
    resp = pool.request(method, url, headers=headers, json=json)
    print(resp.status)
    return resp


def issue_updates(posts: dict[str, Post]) -> None:
    pool = urllib3.PoolManager()

    for i, (slug, post) in enumerate(posts.items(), start=1):
        if not slug.endswith(tuple("1234567890")):
            print(f"skipping {slug}")
            continue

        print(f"[post #{i}] {post.title}")
        resp = ghost_request(pool, "GET", f"/posts/slug/{slug}/")
        body = resp.json()
        id = body["posts"][0]["id"]
        remote_title = body["posts"][0]["title"]
        if post.title != remote_title:
            print(f"[ERROR] skipping {slug}, mismatched titles:\n  remote: {remote_title}\n  local: {post.title}")
            continue
        updated_at = body["posts"][0]["updated_at"]
        resp = ghost_request(pool, "PUT", f"/posts/{id}/?source=html&save_revision=1", json={"posts": [{
            "updated_at": updated_at,
            "html": post.html,
        }]})


main()
