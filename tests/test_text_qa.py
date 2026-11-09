#!/usr/bin/env python3
# CI check: blank pages, missing source/text and duplicate/mutated renders must FAIL.
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_and_validate.py"


class QualityGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.bg = self.dir / "background.png"
        Image.new("RGB", (1080, 1440), "#104568").save(self.bg)
        self.p1 = {
            "page": "P1",
            "series": "生命科学教育与人才培养观察",
            "title": "测序实验工程师需要哪些能力？",
            "subtitle": "认识真实学习路径",
            "source_label": "AI教育概念示意图｜非真实培训现场",
            "background_verified_text_free": True
        }
    def tearDown(self):
        self.tmp.cleanup()

    def cmd(self, *args, ok=True):
        p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                           text=True, capture_output=True)
        if ok:
            self.assertEqual(p.returncode, 0, p.stderr)
        else:
            self.assertNotEqual(p.returncode, 0, p.stdout)
        return p

    def spec_file(self, data, name="P1.spec.json"):
        p = self.dir / name
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return p

    def test_render_and_verify_real_text(self):
        spec = self.spec_file(self.p1)
        out = self.dir / "P1.png"
        self.cmd("render", "--background", self.bg, "--spec", spec, "--out", out)
        self.cmd("verify", "--image", out, "--spec", spec)
        self.assertTrue((self.dir / "P1.qa.json").is_file())
        with Image.open(out) as image:
            self.assertEqual(image.size, (1080, 1440))
            self.assertEqual(image.info["bgi_page"], "P1")
            self.assertGreater(int(image.info["bgi_text_count"]), 2)

    def test_blank_no_text_image_fails(self):
        spec = self.spec_file(self.p1)
        self.cmd("verify", "--image", self.bg, "--spec", spec, ok=False)

    def test_missing_title_fails(self):
        bad = {**self.p1, "title": ""}
        spec = self.spec_file(bad)
        self.cmd("render", "--background", self.bg, "--spec", spec,
                 "--out", self.dir / "P1.png", ok=False)

    def test_unchecked_background_fails(self):
        bad = {**self.p1, "background_verified_text_free": False}
        spec = self.spec_file(bad)
        self.cmd("render", "--background", self.bg, "--spec", spec,
                 "--out", self.dir / "P1.png", ok=False)

    def test_p2_needs_explanation(self):
        p2 = {**self.p1, "page":"P2", "points":[]}
        p2.pop("subtitle", None)
        spec = self.spec_file(p2,"P2.spec.json")
        self.cmd("render", "--background", self.bg, "--spec", spec,
                 "--out", self.dir / "P2.png", ok=False)

    def test_tampered_image_fails(self):
        spec = self.spec_file(self.p1)
        out = self.dir / "P1.png"
        self.cmd("render", "--background", self.bg, "--spec", spec, "--out", out)
        with Image.open(out) as im:
            im.convert("RGB").save(out)
        self.cmd("verify", "--image", out, "--spec", spec, ok=False)


if __name__ == "__main__":
    unittest.main()
