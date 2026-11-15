"""Update the latest blog links from the clinic's public Naver RSS feed."""

import argparse
from datetime import timedelta, timezone
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET


FEED_URL = "https://rss.blog.naver.com/khhongik.xml"
BLOG_URL = "https://blog.naver.com/khhongik"
START = "        <!-- latest-posts:start -->"
END = "        <!-- latest-posts:end -->"
KST = timezone(timedelta(hours=9))


def fetch_entries():
    request = Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=15) as response:
        feed = ET.fromstring(response.read())

    entries = {}
    for item in feed.findall("channel/item"):
        url = urlsplit(item.findtext("link", ""))
        match = re.fullmatch(r"/khhongik/(\d+)", url.path)
        title = " ".join(item.findtext("title", "").split())
        if url.hostname not in {"blog.naver.com", "m.blog.naver.com"} or not match or not title:
            continue
        try:
            published = parsedate_to_datetime(item.findtext("pubDate", "")).astimezone(KST)
        except (ValueError, TypeError, OverflowError):
            continue
        category = " ".join(item.findtext("category", "").split())
        entries[match[1]] = (published, title, category)

    if not entries:
        raise ValueError("Naver RSS returned no usable posts")
    return sorted(entries.items(), key=lambda entry: entry[1][0], reverse=True)[:5]


def update_page(page, entries):
    rows = []
    for post_id, (published, title, category) in entries:
        label = f"<span>{escape(category)}</span>" if category else ""
        rows.append(
            f'        <a href="{BLOG_URL}/{post_id}">\n'
            f'          <div class="post-meta">{label}<time datetime="{published:%Y-%m-%d}">{published:%Y.%m.%d}</time></div>\n'
            f'          <h3>{escape(title)}</h3>\n'
            '          <span aria-hidden="true">↗</span>\n'
            '        </a>'
        )
    html = page.read_text(encoding="utf-8")
    before, marker, remaining = html.partition(START)
    _, end, after = remaining.partition(END)
    if not marker or not end:
        raise RuntimeError("Latest blog post markers are missing")
    page.write_text(before + marker + "\n" + "\n".join(rows) + "\n" + end + after, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("page", type=Path)
    parser.add_argument("--allow-unavailable", action="store_true")
    args = parser.parse_args()
    try:
        entries = fetch_entries()
    except (OSError, ET.ParseError, ValueError) as error:
        if not args.allow_unavailable:
            raise
        print(f"Naver RSS unavailable. Using the saved links: {error}", file=sys.stderr)
        return
    update_page(args.page, entries)


if __name__ == "__main__":
    main()
