#!/usr/bin/env python3
"""Katte Bot — scrape Srishti Institute website for admin documents.

Crawls https://srishtimanipalinstitute.in starting from homepage, same-domain
links only, max depth 3, max ~150 pages. Extracts main content, drops nav/
header/footer/script/style tags, saves as .md files in docs/ for ingest.py.

Usage:  python3 scrape.py
Needs:  pip install requests beautifulsoup4
"""
import json
import re
import sys
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://srishtimanipalinstitute.in"
DOCS = Path(__file__).parent / "docs"
MAX_PAGES = 150
MAX_DEPTH = 3
DELAY = 1  # seconds between requests
MIN_CONTENT_LEN = 200

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0"
})

# Initialize robots.txt parser
rp = urllib.robotparser.RobotFileParser()
rp.set_url(urljoin(BASE_URL, "/robots.txt"))
try:
    rp.read()
except Exception as e:
    print(f"Warning: could not read robots.txt: {e}")


def can_fetch(url):
    """Check if robots.txt allows fetching this URL."""
    try:
        return rp.can_fetch("*", url)
    except Exception:
        return True


def get_domain(url):
    """Extract domain from URL."""
    return urlparse(url).netloc


def is_same_domain(url):
    """Check if URL is on the same domain."""
    return get_domain(url) == get_domain(BASE_URL)


def normalize_url(url):
    """Normalize URL: remove fragments, lowercase scheme+domain."""
    parsed = urlparse(url)
    # Remove fragment and query params for content dedup
    normalized = urllib.parse.urlunparse((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path,
        "",  # params
        "",  # query
        ""   # fragment
    ))
    # Ensure trailing slash consistency
    if not normalized.endswith("/") and "." not in normalized.split("/")[-1]:
        normalized += "/"
    return normalized


def url_to_slug(url):
    """Convert URL to a safe filename slug."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path or path == "":
        slug = "index"
    else:
        # Use path, replace slashes with hyphens, remove special chars
        slug = re.sub(r"[^a-z0-9-]", "", path.lower().replace("/", "-"))
        slug = re.sub(r"-+", "-", slug).strip("-")

    return slug if slug else "index"


def extract_text(soup):
    """Extract main content from BeautifulSoup object.

    Drops nav, header, footer, script, style tags.
    Prefers <main> tag, falls back to <body>.
    """
    # Remove unwanted tags
    for tag in soup.find_all(["nav", "header", "footer", "script", "style"]):
        tag.decompose()

    # Try to find main content
    main = soup.find("main")
    if main:
        content_elem = main
    else:
        body = soup.find("body")
        content_elem = body if body else soup

    # Extract text
    text = content_elem.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(line for line in lines if line)

    return text


def get_page_title(soup, url):
    """Extract page title from soup or URL."""
    title = soup.find("title")
    if title and title.string:
        return title.string.strip()

    h1 = soup.find("h1")
    if h1 and h1.string:
        return h1.string.strip()

    # Fallback: use URL path
    path = urlparse(url).path.strip("/").split("/")[-1]
    return path.replace("-", " ").title() if path else "Home"


def scrape_page(url):
    """Fetch and parse a single page. Returns (title, text) or None if failed."""
    if not can_fetch(url):
        print(f"  ⊘ {url}: blocked by robots.txt")
        return None

    try:
        resp = session.get(url, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ✗ {url}: {e}")
        return None

    try:
        soup = BeautifulSoup(resp.content, "html.parser")
    except Exception as e:
        print(f"  ✗ {url}: parse error: {e}")
        return None

    title = get_page_title(soup, url)
    text = extract_text(soup)

    if len(text) < MIN_CONTENT_LEN:
        print(f"  ⊘ {url}: too short ({len(text)} chars)")
        return None

    return (title, text)


def get_links(url, html_content):
    """Extract same-domain links from HTML."""
    links = set()
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Resolve relative URLs
            abs_url = urljoin(url, href)
            if is_same_domain(abs_url):
                links.add(normalize_url(abs_url))
    except Exception as e:
        print(f"    warning: could not extract links from {url}: {e}")

    return links


def main():
    visited = set()
    queue = deque([(BASE_URL, 0)])  # (url, depth)
    pages_saved = 0

    print(f"Starting crawl from {BASE_URL}")
    print(f"Max depth: {MAX_DEPTH}, Max pages: {MAX_PAGES}\n")

    DOCS.mkdir(exist_ok=True)

    while queue and len(visited) < MAX_PAGES:
        url, depth = queue.popleft()
        url = normalize_url(url)

        if url in visited:
            continue

        visited.add(url)
        print(f"[{len(visited)}/{MAX_PAGES}] ({depth}) {url}")

        time.sleep(DELAY)
        result = scrape_page(url)

        if result is None:
            continue

        title, text = result

        # Save to markdown file
        slug = url_to_slug(url)
        filename = f"web-{slug}.md"
        filepath = DOCS / filename

        # Avoid overwrites with counter
        counter = 1
        while filepath.exists():
            base_slug = slug.rsplit("-", 1)[0] if "-" in slug else slug
            filename = f"web-{base_slug}-{counter}.md"
            filepath = DOCS / filename
            counter += 1

        content = f"{title}\n{url}\n\n{text}"
        filepath.write_text(content)
        pages_saved += 1
        print(f"  ✓ → {filename}")

        # Extract and queue links (but only if we haven't hit max depth)
        if depth < MAX_DEPTH:
            try:
                resp = session.get(url, timeout=10)
                resp.raise_for_status()
                links = get_links(url, resp.content)
                new_links = [link for link in links if link not in visited]

                if new_links:
                    print(f"    → found {len(new_links)} new link(s)")
                    for link in sorted(new_links)[:20]:  # Limit branching
                        if len(visited) < MAX_PAGES:
                            queue.append((link, depth + 1))
            except Exception as e:
                print(f"    warning: could not extract links: {e}")

    print(f"\n✓ Scraped {pages_saved} page(s), visited {len(visited)} URL(s)")
    if len(visited) >= MAX_PAGES:
        print(f"  (Stopped at {MAX_PAGES} page limit)")


if __name__ == "__main__":
    main()
