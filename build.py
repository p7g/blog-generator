import os
import shutil

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from operator import attrgetter
from typing import List, Optional

import frontmatter
import mistletoe
import yattag

from slugify import slugify

BLOG_TITLE = "the blog"
MY_NAME = "patrick gingras"
HEADER_LINKS = [
    ("github", "https://github.com/p7g"),
    ("linkedin", "https://linkedin.com/pat775"),
]

CSS = """
body {
    margin: 0;
}
"""


def header(doc, tag, text, line):
    with tag("header", klass="header"):
        with tag("a", href="/", title="home"):
            line("h1", BLOG_TITLE, klass="header__title")
        line("p", MY_NAME, klass="header__name")

        with tag("section", klass="header__links"):
            for link_text, address in HEADER_LINKS:
                line("a", link_text, href=address, klass="header__links__link")
    return doc


@contextmanager
def base_page(doc, tag, text, line):
    doc.asis("<!DOCTYPE html>")

    with tag("html"):
        with tag("head"):
            line("style", CSS)
        with tag("body"):
            yield


def home_page(posts: List["Post"]):
    doc, tag, text, line = ttl = yattag.Doc().ttl()

    with base_page(*ttl):
        header(*ttl)

        with tag("main", klass="main"):
            with tag("section", klass="main__post_list"):
                line("h2", "posts", klass="main__post_list__heading")
                for post in posts:
                    with tag("article"):
                        with tag("a", href=post.url):
                            line("h3", post.title, klass="main__post__title")
                        line(
                            "time",
                            post.date.strftime("%c"),
                            klass="main__post__date",
                            datetime=post.date.isoformat(),
                        )
                        if post.description is not None:
                            line(
                                "p",
                                post.description,
                                klass="main__post__description",
                            )
    return doc.getvalue()


def post_page(post: "Post"):
    doc, tag, text, line = ttl = yattag.Doc().ttl()

    with base_page(*ttl):
        header(*ttl)
    return doc.getvalue()


@dataclass
class Post:
    title: str
    description: Optional[str]
    date: datetime
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

        posts.append(
            Post(
                title=post_raw["title"],
                description=post_raw.get("description"),
                date=datetime.fromisoformat(post_raw["date"]),
                html=mistletoe.markdown(post_raw.content),
            )
        )


posts = list(sorted(posts, key=attrgetter("date")))

shutil.rmtree("build")
os.makedirs(os.path.join("build", "posts"), exist_ok=True)

# generate main page
with open(os.path.join("build", "index.html"), "w") as f:
    f.write(yattag.indent(home_page(posts)))

for post in posts:
    post_dir = os.path.join("build", "posts", post.slug)
    os.makedirs(post_dir, exist_ok=False)

    with open(os.path.join(post_dir, "index.html"), "w") as f:
        f.write(yattag.indent(post_page(post)))
