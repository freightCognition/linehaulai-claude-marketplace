#!/usr/bin/env python3
"""Regenerate references/components.md from cult-ui's live sources.

Sources (both published by cult-ui):
  - https://www.cult-ui.com/llms.txt          documented components: name, doc slug, summary
  - https://www.cult-ui.com/r/registry.json   install names, npm deps, registry deps

The doc slug and the registry install name usually match but not always
(e.g. docs "hero-color-panels" installs as "hero-color-panel"). ALIASES maps the
known exceptions; the script exits non-zero if a documented component has no
registry item, so upstream renames are caught instead of silently dropped.

Usage:
  python3 sync_catalog.py                      # fetch live, write ../references/components.md
  python3 sync_catalog.py --llms F --registry F --out F   # use local files
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request

SITE = "https://www.cult-ui.com"
LLMS_URL = f"{SITE}/llms.txt"
REGISTRY_URL = f"{SITE}/r/registry.json"
DEFAULT_OUT = pathlib.Path(__file__).resolve().parent.parent / "references" / "components.md"

# doc slug -> registry install name, for slugs that differ upstream
ALIASES = {
    "bg-animated-fractal-grid": "bg-animated-fractal-dot-grid",
    "hero-color-panels": "hero-color-panel",
}

# Ordered (category, keywords). Keywords match whole words (plural ok): slug words first, then summary words.
CATEGORIES = [
    ("Device & Product Mockups", ["apple", "iphone", "macbook", "mac", "mockup", "browser", "keyboard", "watch", "display"]),
    ("Heroes & Landing Sections", ["hero"]),
    ("Illustrations & SVG", ["illustration", "svg", "shapes", "squiggle", "globe", "cursor", "arrow", "bubbles", "circuit"]),
    ("AI & Agent UI", ["ai", "agent", "prompt", "composer", "chat", "llm"]),
    ("Text & Typography", ["text", "heading", "typewriter", "number", "word", "letter", "paragraph", "eyebrow", "badge"]),
    ("Buttons", ["button"]),
    ("Cards", ["card"]),
    ("Forms & Inputs", ["input", "select", "picker", "field", "switch", "poll", "dropzone", "search", "form", "toggle", "slider", "checkbox", "otp", "segmented"]),
    ("Navigation, Overlays & Layout", ["tabs", "toolbar", "sidebar", "side", "dock", "menu", "island", "popover", "expandable", "screen", "onboarding", "modal", "dialog", "drawer", "tooltip", "toast", "notification", "disclosure", "panel"]),
    ("Media, Video & Social", ["video", "player", "carousel", "logo", "gallery", "tweet", "avatar"]),
    ("Backgrounds, Shaders & Effects", ["bg", "background", "grid", "shader", "texture", "gradient", "glass", "dither", "noise", "beam", "glow", "warp", "blur", "guides"]),
    ("Data, Charts & Code", ["chart", "graph", "stat", "table", "timer", "code", "terminal", "progress", "kanban", "list"]),
]
OTHER = "Other"

DOC_LINE = re.compile(r"^- \[(?P<name>.+?)\]\(https://www\.cult-ui\.com/docs/components/(?P<slug>[^)\s]+?)\.md\): (?P<summary>.*)$", re.M)
PAGE_LINE = re.compile(r"^- \[(?P<name>.+?)\]\((?P<url>https://www\.cult-ui\.com/docs[^)\s]*?)\.md\): (?P<summary>.*)$", re.M)


def load(src: str) -> str:
    if src.startswith("http"):
        req = urllib.request.Request(src, headers={"User-Agent": "cult-ui-catalog-sync"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read().decode("utf-8")
    return pathlib.Path(src).read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    m = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def categorize(slug: str, summary: str) -> str:
    for text in (slug, summary):
        words = set(re.findall(r"[a-z0-9]+", text.lower()))
        for cat, keys in CATEGORIES:
            if any(k in words or k + "s" in words for k in keys):
                return cat
    return OTHER


def build(llms: str, registry: dict) -> str:
    items = {i["name"]: i for i in registry["items"] if i.get("type") == "registry:ui"}
    docs = [m.groupdict() for m in DOC_LINE.finditer(section(llms, "Components"))]
    if not docs:
        raise SystemExit("no components parsed from llms.txt; its format may have changed")

    missing = [d["slug"] for d in docs if ALIASES.get(d["slug"], d["slug"]) not in items]
    if missing:
        raise SystemExit(f"documented components with no registry item (add to ALIASES): {missing}")

    used = set()
    grouped: dict[str, list[str]] = {}
    for d in sorted(docs, key=lambda d: d["name"].lower()):
        install = ALIASES.get(d["slug"], d["slug"])
        used.add(install)
        item = items[install]
        doc_url = f"{SITE}/docs/components/{d['slug']}"
        line = f"- **[{d['name']}]({doc_url})** · install `@cult-ui/{install}` · md {doc_url}.md\n  {d['summary']}"
        extras = []
        if item.get("dependencies"):
            extras.append("npm: " + ", ".join(item["dependencies"]))
        if item.get("registryDependencies"):
            extras.append("shadcn: " + ", ".join(item["registryDependencies"]))
        if install != d["slug"]:
            extras.append(f"note: doc slug `{d['slug']}` differs from install name `{install}`")
        if extras:
            line += "\n  " + " · ".join(extras)
        grouped.setdefault(categorize(d["slug"], d["summary"]), []).append(line)

    order = [c for c, _ in CATEGORIES] + [OTHER]
    out = [
        "# Cult UI Component Catalog",
        "",
        f"Generated {dt.date.today().isoformat()} by `scripts/sync_catalog.py` from {LLMS_URL} and {REGISTRY_URL}. Do not edit by hand; re-run the script.",
        "",
        f"{len(docs)} documented components. Each entry gives the docs page, the shadcn install name, the markdown docs URL (best for WebFetch), and dependencies.",
        "",
        "Install any entry with `npx shadcn@latest add @cult-ui/<install-name>` or `npx shadcn@latest add https://www.cult-ui.com/r/<install-name>.json`.",
        "",
        "## Categories",
        "",
    ]
    out += [f"- {c} ({len(grouped[c])})" for c in order if c in grouped]
    for c in order:
        if c in grouped:
            out += ["", f"## {c}", ""] + grouped[c]

    pages = [m.groupdict() for m in PAGE_LINE.finditer(section(llms, "Docs"))]
    if pages:
        out += ["", "## Guide Pages", ""]
        out += [f"- [{p['name']}]({p['url']}) · md {p['url']}.md\n  {p['summary']}" for p in pages]

    extra = sorted(set(items) - used)
    if extra:
        out += ["", "## Registry Items Without a Docs Page", "",
                "Installable, but undocumented. Many are primitives other components pull in, or deprecated aliases. Read the JSON at `https://www.cult-ui.com/r/<name>.json` for the source.", ""]
        for name in extra:
            desc = items[name].get("description") or "(no description)"
            out.append(f"- `{name}`: {desc}")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--llms", default=LLMS_URL)
    ap.add_argument("--registry", default=REGISTRY_URL)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args(argv)
    md = build(load(a.llms), json.loads(load(a.registry)))
    pathlib.Path(a.out).write_text(md, encoding="utf-8")
    print(f"wrote {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
