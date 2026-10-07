"""S07 T023 (adversary B1, B2, B3): `check-ux-gates` follows every way a preview can name a local stylesheet.

On a slice branch a preview renders only when something it links or imports changed, so a stylesheet the scope cannot
follow is a change that renders nothing. Three spellings were not followed: an unquoted `href=app.css`, an `@import` of
a quoted name with a space in it, which was cut at the space, and a percent-encoded `href`, matched undecoded against
the file it names. The scope is `styles_of`, held here directly on files written for each case; the spellings that
were already followed are held beside them.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType

from slipwai.assets import ROOT

sys.dont_write_bytecode = True


def gates() -> ModuleType:
    spec = importlib.util.spec_from_file_location("ux_gates_links", ROOT / "assets/toolkit/scripts/check-ux-gates.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LinksTest(unittest.TestCase):
    module: ModuleType

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = gates()

    def followed(self, preview: str, sheets: dict[str, str] | None = None) -> set[str]:
        """The names `styles_of` reaches from a preview in `screens/`, beside which `sheets` are written."""
        with tempfile.TemporaryDirectory() as directory:
            screens = Path(directory).resolve() / "screens"
            screens.mkdir()
            for name, text in (sheets or {}).items():
                (screens / name).write_text(text, encoding="utf-8")
            page = screens / "page.html"
            page.write_text(preview, encoding="utf-8")
            return {path.relative_to(screens).as_posix() for path in self.module.styles_of(page)}

    def test_b1_an_unquoted_href_is_followed(self) -> None:
        self.assertEqual(self.followed('<link rel=stylesheet href=app.css><button>Go</button>'), {"app.css"})
        self.assertEqual(self.followed('<link href=app.css rel="stylesheet">'), {"app.css"})
        self.assertEqual(self.followed("<link rel=stylesheet href=app.css\tmedia=screen>"), {"app.css"},
                         "an unquoted value runs to whitespace or `>`, as HTML reads it")

    def test_b2_an_import_of_a_quoted_name_with_a_space_is_followed_whole(self) -> None:
        self.assertEqual(self.followed('<style>@import "my styles.css";</style>'), {"my styles.css"})
        self.assertEqual(self.followed("<style>@import url('my styles.css');</style>"), {"my styles.css"})
        self.assertEqual(self.followed('<style>@import url( "my styles.css" ) screen;</style>'), {"my styles.css"})

    def test_b2_an_import_inside_a_stylesheet_is_followed_whole_too(self) -> None:
        sheets = {"entry.css": '@import "deep sheet.css";\n'}
        reached = self.followed('<link rel="stylesheet" href="entry.css">', sheets)
        self.assertEqual(reached, {"entry.css", "deep sheet.css"})

    def test_b3_a_percent_encoded_href_names_the_decoded_file(self) -> None:
        self.assertEqual(self.followed('<link rel="stylesheet" href="my%20styles.css">'), {"my styles.css"})
        self.assertEqual(self.followed("<style>@import url('deep%20sheet.css');</style>"), {"deep sheet.css"})

    def test_the_quoted_forms_are_still_followed(self) -> None:
        self.assertEqual(self.followed('<link rel="stylesheet" href="a.css">'), {"a.css"})
        self.assertEqual(self.followed("<link rel='stylesheet' href='a.css?v=2#x'>"), {"a.css"})
        self.assertEqual(self.followed('<style>@import "b.css";</style>'), {"b.css"})
        self.assertEqual(self.followed("<style>@import url(c.css);</style>"), {"c.css"})
        self.assertEqual(self.followed("<style>@import url(\"d.css\") print;</style>"), {"d.css"})

    def test_what_is_not_a_local_file_is_still_not_followed(self) -> None:
        self.assertEqual(self.followed('<link rel="stylesheet" href="https://cdn.example/x.css">'), set())
        self.assertEqual(self.followed("<link rel=stylesheet href=//cdn.example/x.css>"), set())
        self.assertEqual(self.followed('<link rel="icon" href="icon.css">'), set())
        self.assertEqual(self.followed("<style>@import url(data:text/css,a%20b);</style>"), set())


if __name__ == "__main__":
    unittest.main()
