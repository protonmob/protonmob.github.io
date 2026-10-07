"""Mirror a published Framer site into a self-contained static folder.

Every https://framerusercontent.com/... reference (in HTML, .mjs, .css, .json)
is downloaded under /_fc/ and rewritten to a root-relative path.
"""
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

SITE = "https://protonmob.com"
PAGES = {"index.html": "index.html", "support.html": "support/index.html"}
RAW = Path(sys.argv[2])
OUT = Path(sys.argv[1])
FC = "https://framerusercontent.com"
URL_RE = re.compile(r"https://(?:framerusercontent\.com|app\.framerstatic\.com|lottie\.host)/[^\s\"'`)\\,<>]+")
REL_IMPORT_RE = re.compile(r"""(?:from|import)\s*\(?\s*["'](\./[^"']+\.mjs)["']""")
TEXT_EXT = {".mjs", ".js", ".css", ".json", ".html", ".svg"}

seen: set[str] = set()
queue: list[str] = []


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def local_path(url: str) -> str:
    parts = urlsplit(url)
    prefix = {"framerusercontent.com": "/_fc", "app.framerstatic.com": "/_fs", "lottie.host": "/_lottie"}[parts.netloc]
    return prefix + parts.path


def rewrite(text: str) -> str:
    def repl(m: re.Match) -> str:
        url = m.group(0)
        clean = url.split("?")[0].split("#")[0]
        enqueue(clean)
        return local_path(clean)
    return URL_RE.sub(repl, text)


def enqueue(url: str) -> None:
    if url not in seen:
        seen.add(url)
        queue.append(url)


def process_text(text: str, base_url: str | None) -> str:
    if base_url:
        base_dir = base_url.rsplit("/", 1)[0]
        for rel in REL_IMPORT_RE.findall(text):
            enqueue(base_dir + "/" + rel[2:])
    return rewrite(text)


for route, name in PAGES.items():
    html = (RAW / route).read_text()
    # drop Framer analytics
    html = re.sub(r'<script[^>]*events\.framer\.com[^>]*></script>', "", html)
    dest = OUT / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(process_text(html, None))

failed = []
while queue:
    url = queue.pop()
    dest = OUT / local_path(url).lstrip("/")
    try:
        data = fetch(url)
    except Exception as e:  # noqa: BLE001
        failed.append((url, str(e)))
        continue
    if not Path(urlsplit(url).path).suffix:
        continue  # a base prefix used to build URLs at runtime, not a file
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
    except (FileExistsError, NotADirectoryError) as e:
        failed.append((url, str(e)))
        continue
    if dest.suffix in TEXT_EXT:
        try:
            data = process_text(data.decode(), url).encode()
        except UnicodeDecodeError:
            pass
    dest.write_bytes(data)

print(f"downloaded {len(seen) - len(failed)} files")
for url, err in failed:
    print("FAILED", url, err)
