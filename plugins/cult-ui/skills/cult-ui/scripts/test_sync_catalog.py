#!/usr/bin/env python3
"""Tests for sync_catalog.py. Run: python3 -m unittest test_sync_catalog (from this directory)."""
import unittest

import sync_catalog as sc

LLMS = """# Cult UI

## Docs

- [Theming](https://www.cult-ui.com/docs/theming.md): Theme tokens.

## Components

- [Texture Button](https://www.cult-ui.com/docs/components/texture-button.md): Tactile button.
- [Hero Color Panels](https://www.cult-ui.com/docs/components/hero-color-panels.md): Split hero.
- [Mystery Thing](https://www.cult-ui.com/docs/components/mystery-thing.md): Something odd.
"""

REGISTRY = {"items": [
    {"name": "texture-button", "type": "registry:ui", "dependencies": ["class-variance-authority"]},
    {"name": "hero-color-panel", "type": "registry:ui", "registryDependencies": ["badge", "button"]},
    {"name": "mystery-thing", "type": "registry:ui"},
    {"name": "animated-badge", "type": "registry:ui", "description": "Deprecated alias for halo-badge."},
    {"name": "texture-button-demo", "type": "registry:component"},
]}


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.md = sc.build(LLMS, REGISTRY)

    def test_every_documented_component_listed_with_urls(self):
        self.assertIn("**[Texture Button](https://www.cult-ui.com/docs/components/texture-button)**", self.md)
        self.assertIn("md https://www.cult-ui.com/docs/components/texture-button.md", self.md)
        self.assertIn("3 documented components", self.md)

    def test_alias_uses_registry_install_name(self):
        self.assertIn("install `@cult-ui/hero-color-panel`", self.md)
        self.assertIn("doc slug `hero-color-panels` differs", self.md)

    def test_dependencies_rendered(self):
        self.assertIn("npm: class-variance-authority", self.md)
        self.assertIn("shadcn: badge, button", self.md)

    def test_categories(self):
        self.assertIn("## Buttons", self.md)
        self.assertIn("## Heroes & Landing Sections", self.md)
        self.assertIn("## Other", self.md)

    def test_undocumented_items_listed_but_demos_excluded(self):
        self.assertIn("`animated-badge`: Deprecated alias", self.md)
        self.assertNotIn("texture-button-demo", self.md)

    def test_guide_pages(self):
        self.assertIn("[Theming](https://www.cult-ui.com/docs/theming)", self.md)

    def test_unmapped_doc_slug_fails_loudly(self):
        broken = {"items": [i for i in REGISTRY["items"] if i["name"] != "mystery-thing"]}
        with self.assertRaises(SystemExit) as cm:
            sc.build(LLMS, broken)
        self.assertIn("mystery-thing", str(cm.exception))

    def test_unparseable_llms_fails_loudly(self):
        with self.assertRaises(SystemExit):
            sc.build("# nothing here", REGISTRY)


if __name__ == "__main__":
    unittest.main()
