#!/usr/bin/env python

import datetime as dt
import os
import shutil

from contextlib import contextmanager
from dataclasses import dataclass
from operator import attrgetter
from typing import List, Optional

import frontmatter
import mistletoe
import yattag

from slugify import slugify
from typogrify.filters import typogrify

BLOG_TITLE = "the blog"
DEFAULT_DESCRIPTION = "A cool and nice programming blog"
MY_NAME = "Patrick Gingras"
EMAIL = "p.7g@icloud.com"
LANG = "en"
HEADER_LINKS = [
    ("github", "https://github.com/p7g"),
    ("linkedin", "https://linkedin.com/in/pat775"),
]


def deferred_stylesheet(doc, href: str):
    doc.stag(
        "link",
        rel="preload",
        **{"as": "style"},
        href=href,
        onload="this.onload=null; this.rel='stylesheet';",
    )
    with doc.tag("noscript"):
        doc.stag("link", rel="stylesheet", href=href)


def header(doc, tag, text, line):
    with tag("header", klass="header"):
        with tag("a", href="/", title="home"):
            line("h1", BLOG_TITLE, klass="header__title")
        line("p", MY_NAME, klass="header__name")

        with tag("section", klass="header__links"):
            for link_text, address in HEADER_LINKS:
                line("a", link_text, href=address, klass="header__links__link")
                text(" ")

        doc.stag("hr")

    return doc


@contextmanager
def base_page(doc, tag, text, line, *, title: str = None, description: str = None):
    doc.asis("<!DOCTYPE html>")

    with tag("html", lang=LANG):
        with tag("head"):
            doc.stag("meta", charset="utf-8")
            doc.stag(
                "meta", name="viewport", content="width=device-width, initial-scale=1"
            )
            doc.stag(
                "meta", name="description", content=description or DEFAULT_DESCRIPTION,
            )
            doc.stag(
                "link",
                rel="shortcut icon",
                type="image/x-icon",
                href="/static/favicon.ico",
            )
            line("title", f"{title} | {BLOG_TITLE}" if title else BLOG_TITLE)
            deferred_stylesheet(
                doc,
                "https://fonts.googleapis.com/css?family="
                "IBM+Plex+Serif:400,400i,700,700i"
                "|Faustina:400,400i,700,700i"
                "|Inconsolata"
                "&display=block",
            )

            with open("styles.css", "r") as f:
                line("style", f.read())
        with tag("body"):
            yield


def home_page(posts: List["Post"]):
    doc, tag, text, line = ttl = yattag.Doc().ttl()

    with base_page(*ttl):
        header(*ttl)

        with tag("main", klass="main"):
            with tag("section", klass="main__post_list"):
                for post in posts:
                    with tag("article", klass="main__post"):
                        with tag("a", href=post.url):
                            with tag("h3", klass="main__post__title"):
                                doc.asis(typogrify(post.title))
                        with tag("small", klass="main__post__date"):
                            line(
                                "time",
                                post.date.strftime("%B %d, %Y"),
                                datetime=post.date.isoformat(),
                            )
                        if post.description is not None:
                            with tag(
                                "p", klass="main__post__description",
                            ):
                                doc.asis(typogrify(post.description))

    return doc.getvalue()


def post_page(post: "Post"):
    doc, tag, text, line = ttl = yattag.Doc().ttl()

    with base_page(*ttl, title=post.title, description=post.description):
        header(*ttl)

        with tag("main", klass="main"):
            with tag("article", klass="post"):
                with tag("header", klass="post__header"):
                    with tag("h2", klass="post__heading"):
                        doc.asis(typogrify(post.title))
                    line(
                        "time",
                        post.date.strftime("%B %d, %Y"),
                        datetime=post.date.isoformat(),
                        klass="post__heading__time",
                    )
                with tag("main", klass="post__main"):
                    doc.asis(typogrify(post.html))
        with tag("footer", klass="post__footer"):
            doc.stag("hr")
            text("Tell me I'm wrong: ")
            line("a", EMAIL, href=f"mailto:{EMAIL}", klass="post__footer__email")

    return doc.getvalue()


@dataclass
class Post:
    title: str
    description: Optional[str]
    date: dt.date
    html: str

    @property
    def slug(self):
        return slugify(self.title)

    @property
    def url(self):
        return f"/posts/{self.slug}"


posts = []

with os.scandir("posts") as it:
    for post_file in it:
        if not post_file.is_file() or post_file.name.startswith("."):
            continue

        with open(post_file.path, "r") as f:
            text = f.read()

        post_raw = frontmatter.loads(text)

        date = post_raw["date"]
        if isinstance(date, str):
            date = dt.date.fromisoformat(date)

        posts.append(
            Post(
                title=post_raw["title"],
                description=post_raw.get("description"),
                date=date,
                html=mistletoe.markdown(post_raw.content).replace("&quot;", '"'),
            )
        )


posts = list(sorted(posts, key=attrgetter("date"), reverse=True))

shutil.rmtree("build")
os.makedirs(os.path.join("build", "posts"), exist_ok=True)

# generate main page
with open(os.path.join("build", "index.html"), "w") as f:
    f.write(home_page(posts))

for post in posts:
    post_dir = os.path.join("build", "posts", post.slug)
    os.makedirs(post_dir, exist_ok=False)

    with open(os.path.join(post_dir, "index.html"), "w") as f:
        f.write(post_page(post))

if os.path.exists("static"):
    shutil.copytree("static", os.path.join("build", "static"))
