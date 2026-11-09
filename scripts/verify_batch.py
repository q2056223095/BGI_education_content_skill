#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed batch checker: no text-free P1/P2 can count as completed."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageChops

from render_and_validate import verify

REQUIRED = ("小红书文案.txt", "来源与合规.md",
            "P1.png", "P2.png", "P1.spec.json", "P2.spec.json",
            "P1.qa.json", "P2.qa.json")


def verify_topic(folder):
    missing = [name for name in REQUIRED if not (folder / name).is_file()]
    issues = [f"missing: {name}" for name in missing]
    checks = []
    for page in ("P1", "P2"):
        if any(name.startswith(page + ".") for name in missing):
            continue
        try:
            checks.append(verify(folder / f"{page}.png",
                                 folder / f"{page}.spec.json",
                                 folder / f"{page}.qa.json"))
        except Exception as exc:
            issues.append(f"{page}: {exc}")
    if not missing:
        try:
            p1 = Image.open(folder / "P1.png").convert("RGB")
            p2 = Image.open(folder / "P2.png").convert("RGB")
            # Detect duplicate PNG masquerading as distinct explanatory page.
            if hashlib.sha256((folder / "P1.png").read_bytes()).digest() == hashlib.sha256(
                    (folder / "P2.png").read_bytes()).digest():
                issues.append("P1/P2 are exact duplicate files")
            else:
                diff = ImageChops.difference(p1.resize((270, 360)),
                                             p2.resize((270, 360)))
                if diff.getbbox() is None:
                    issues.append("P1/P2 pixels identical")
        except Exception as exc:
            issues.append(f"image pair check: {exc}")
    text = (folder / "小红书文案.txt")
    if text.exists() and len(text.read_text(encoding="utf-8").strip()) < 100:
        issues.append("caption too short or empty")
    return {"topic": folder.name, "status": "PASS" if not issues else "FAIL",
            "missing_or_failed": issues, "pages_checked": checks}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, type=Path)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    if not args.batch.is_dir():
        raise SystemExit("Batch folder does not exist")
    topics = sorted(p for p in args.batch.iterdir()
                    if p.is_dir() and p.name[:2].isdigit() and "_" in p.name)
    if not topics:
        raise SystemExit("No topic directories found: batch cannot pass")
    results = [verify_topic(p) for p in topics]
    pass_count = sum(t["status"] == "PASS" for t in results)
    report = {"batch": str(args.batch), "topic_count": len(topics),
              "completed_count": pass_count, "partial_or_failed_count":
              len(topics) - pass_count, "results": results,
              "all_passed": pass_count == len(topics)}
    dest = args.report or args.batch / "图片质量验收报告.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_passed"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
