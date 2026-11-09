#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic Chinese text compositor and two-page PNG quality gate.

Dependencies: Pillow >= 10, a locally installed CJK font (e.g. Noto Sans CJK).
No OCR is used: the script draws approved strings and verifies its own glyph
layer, layout, PNG metadata, hashes and dimensions. Semantic/visual review is
a separate mandatory gate described in docs/image_quality_gate.md.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

SIZE = (1080, 1440)
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/msyh.ttc",
]
IDENTITIES = ("AI教育概念示意图", "AI科学示意图", "官方授权素材",
              "现场照片", "数据图重绘", "科学示意图")


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha_bytes(content):
    return hashlib.sha256(content).hexdigest()


def sha_file(path):
    return sha_bytes(Path(path).read_bytes())


def die(reason):
    raise ValueError(reason)


def font_path(spec):
    p = spec.get("font_file")
    if p:
        if not Path(p).is_file():
            die("字体不存在（禁止静默使用无中文字形的默认字体）: " + p)
        return p
    for candidate in FONT_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    die("没有发现可用的中文字体，请在spec.font_file配置Noto Sans CJK等字体路径。")


def font(path, size):
    # NotoSansCJK .ttc face 0 is Japanese; use face 2 for Simplified Chinese.
    if Path(path).name.startswith("NotoSansCJK-") and str(path).lower().endswith(".ttc"):
        return ImageFont.truetype(str(path), size, index=2)
    return ImageFont.truetype(str(path), size)


def wrap_text(value, f, max_width):
    lines, cur = [], ""
    for segment in value.split("\n"):
        cur = ""
        for c in segment:
            if ImageDraw.Draw(Image.new("L", (1, 1))).textlength(cur + c, font=f) <= max_width:
                cur += c
            else:
                if not cur:
                    die("单个字符无法容纳: " + c)
                lines.append(cur)
                cur = c
        lines.append(cur)
    return lines


def positive_text(spec, field, min_chars=1):
    v = spec.get(field)
    if not isinstance(v, str) or len(v.strip()) < min_chars:
        die("缺少必填文字: " + field)
    if any(s in v for s in ("待补充", "TBD", "Lorem ipsum", "占位文字")):
        die("字段仍包含占位符: " + field)
    return v.strip()


def validate_spec(spec):
    if not isinstance(spec, dict):
        die("spec必须是JSON对象")
    if spec.get("page") not in ("P1", "P2"):
        die("page必须为P1或P2")
    positive_text(spec, "title", 4)
    source = positive_text(spec, "source_label", 8)
    if not any(x in source for x in IDENTITIES):
        die("source_label必须清楚标明图片来源身份")
    if spec.get("background_verified_text_free") is not True:
        die("必须先视觉核查背景无乱字/伪Logo，再设置background_verified_text_free=true")
    if spec["page"] == "P2":
        points = spec.get("points")
        if not isinstance(points, list) or not 2 <= len(points) <= 3:
            die("P2必须提供2–3条已核实的解释要点")
        for i, row in enumerate(points, start=1):
            if not isinstance(row, dict):
                die("points每项必须为对象")
            for key in ("heading", "detail"):
                value = row.get(key)
                if not isinstance(value, str) or len(value.strip()) < 2:
                    die("P2要点缺少"+key+"："+str(i))
                if any(s in value for s in ("待补充", "TBD", "Lorem ipsum", "占位文字")):
                    die("P2要点包含占位文字："+str(i))
    if spec["page"] == "P1" and spec.get("points"):
        die("P1不应堆叠信息要点")
    return spec


def background_with_gradients(image):
    # Ensure white text legibility regardless of background photograph exposure.
    image = image.convert("RGBA")
    grad = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    px = grad.load()
    for y in range(SIZE[1]):
        top = max(0, 1.0 - y / 760)
        bottom = max(0, (y - 690) / 750)
        alpha = int(max(210 * top, 185 * bottom, 25))
        for x in range(SIZE[0]):
            px[x, y] = (4, 20, 48, alpha)
    return Image.alpha_composite(image, grad)


def line(draw, mask_draw, xy, text, f, color, stroke=1):
    x, y = xy
    if not text:
        return None
    bbox = draw.textbbox((x, y), text, font=f, stroke_width=stroke)
    if bbox[0] < 0 or bbox[1] < 0 or bbox[2] > SIZE[0] or bbox[3] > SIZE[1]:
        die("文字超出画布边界："+text[:30])
    draw.text((x, y), text, font=f, fill=color, stroke_width=stroke,
              stroke_fill=(0, 9, 22, 255))
    mask_draw.text((x, y), text, font=f, fill=255)
    return {"text": text, "bbox": list(bbox)}


def multiline(draw, mask_draw, x, y, value, f, width, color,
              max_lines, line_h, stroke=1):
    ls = wrap_text(value, f, width)
    if len(ls) > max_lines:
        die("文字超出允许行数，请精简标题或要点："+value[:28])
    items = []
    for i, txt in enumerate(ls):
        item = line(draw, mask_draw, (x, y + i * line_h), txt, f, color, stroke)
        if item:
            items.append(item)
    return items, y + len(ls) * line_h


def render(background, spec_path, output, qa_path=None):
    spec = validate_spec(json.loads(Path(spec_path).read_text(encoding="utf-8")))
    fpath = font_path(spec)
    original = Image.open(background)
    if original.width <= 0 or original.height <= 0:
        die("背景图片无效")
    # ONLY use backgrounds that were generated as single full-page scenery.
    ratio = original.width / original.height
    if not 0.70 <= ratio <= 0.80:
        die("背景必须为独立3:4画面；拒绝双联或横向拼图")
    image = background_with_gradients(original.resize(SIZE, Image.Resampling.LANCZOS))
    draw = ImageDraw.Draw(image)
    mask = Image.new("L", SIZE, 0)
    md = ImageDraw.Draw(mask)
    entries = []
    entries += multiline(draw, md, 74, 54,
                         spec.get("series", "生命科学教育与人才培养观察"),
                         font(fpath, 33), 940, "#ADEAFF", 1, 43)[0]
    entries += multiline(draw, md, 78, 165, spec["title"],
                         font(fpath, 82 if spec["page"] == "P1" else 69),
                         922, "#FFFFFF",
                         3 if spec["page"] == "P1" else 2,
                         108 if spec["page"] == "P1" else 92)[0]
    if spec["page"] == "P1":
        subtitle = positive_text(spec, "subtitle", 3)
        entries_sub, _ = multiline(draw, md, 80, 540, subtitle,
                                   font(fpath, 36), 910,
                                   "#B5FCF5", 2, 51)
        entries += entries_sub
    else:
        points = spec["points"]
        n = len(points)
        top, height, gap = 805, 486 // n - 8, 8
        for i, row in enumerate(points):
            y = top + i * (height + gap)
            # quiet transparent strips, not a contact-sheet or card matrix
            draw.rounded_rectangle((62, y, 1018, y + height),
                                   radius=20, fill=(4, 26, 56, 225),
                                   outline=(40, 171, 201, 120), width=2)
            entries += multiline(draw, md, 91, y + 12, row["heading"],
                                 font(fpath, 39), 900, "#72EAED", 1, 49)[0]
            entries += multiline(draw, md, 91, y + 64, row["detail"],
                                 font(fpath, 30), 902, "#FFFFFF", 2, 37)[0]
    entries += multiline(draw, md, 75, 1363, spec["source_label"],
                         font(fpath, 23), 925, "#E2F6FB", 2, 29)[0]
    # If the source label needs two lines, move it earlier by adjusting the spec
    for e in entries:
        if e["bbox"][3] > 1436:
            die("页脚来源标签溢出")
    ink = sum(1 for pixel in mask.getdata() if pixel != 0)
    if ink < 4000:
        die("文字图层像素异常，拒绝无文字成品")
    manifest_hash = sha_bytes(canonical({
        k: v for k, v in spec.items() if k not in ("font_file",)
    }).encode("utf-8"))
    meta = PngImagePlugin.PngInfo()
    meta.add_text("bgi_text_qa", "rendered-v1.1")
    meta.add_text("bgi_manifest_sha256", manifest_hash)
    meta.add_text("bgi_page", spec["page"])
    meta.add_text("bgi_text_count", str(len(entries)))
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(out, "PNG", pnginfo=meta, optimize=True)
    qa = {"result": "PASS", "page": spec["page"], "size": list(SIZE),
          "image": str(out), "image_sha256": sha_file(out),
          "spec_sha256": manifest_hash, "font": str(fpath),
          "glyph_ink_pixels": ink, "drawn_text": entries,
          "background_visual_check": "必须另行使用视觉检查确认背景无乱码、拼版、假现场",
          "semantics_check": "必须逐句对照来源及正文，程序不判断事实真伪"}
    qa_out = Path(qa_path) if qa_path else out.with_suffix(".qa.json")
    qa_out.write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa


def verify(image_path, spec_path, qa_path=None):
    spec = validate_spec(json.loads(Path(spec_path).read_text(encoding="utf-8")))
    p = Path(image_path)
    qa_path = Path(qa_path) if qa_path else p.with_suffix(".qa.json")
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    with Image.open(p) as im:
        if im.size != SIZE or im.format != "PNG":
            die("PNG尺寸/格式不匹配")
        if im.info.get("bgi_text_qa") != "rendered-v1.1":
            die("无程序文字叠加标记，拒绝纯背景或旧版无字图")
        expected_hash = sha_bytes(canonical({
            k: v for k, v in spec.items() if k not in ("font_file",)
        }).encode("utf-8"))
        if im.info.get("bgi_manifest_sha256") != expected_hash:
            die("PNG中文字清单哈希不匹配")
        if im.info.get("bgi_page") != spec["page"]:
            die("页码不匹配")
    if sha_file(p) != qa.get("image_sha256"):
        die("图片字节已更改，需重新生成QA报告")
    expected_min = 3 if spec["page"] == "P1" else 4
    if len(qa.get("drawn_text", [])) < expected_min:
        die("关键文字缺件")
    if qa.get("glyph_ink_pixels", 0) < 4000:
        die("关键文字可能未正确绘制")
    return {"result": "PASS", "page": spec["page"],
            "size": list(SIZE), "image": str(p),
            "text_items": len(qa["drawn_text"])}


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    gen = sub.add_parser("render", help="From no-text background + approved JSON to PNG")
    gen.add_argument("--background", required=True)
    gen.add_argument("--spec", required=True)
    gen.add_argument("--out", required=True)
    gen.add_argument("--qa")
    val = sub.add_parser("verify", help="Reject images without render manifest and QA")
    val.add_argument("--image", required=True)
    val.add_argument("--spec", required=True)
    val.add_argument("--qa")
    args = parser.parse_args()
    try:
        if args.cmd == "render":
            report = render(args.background, args.spec, args.out, args.qa)
        else:
            report = verify(args.image, args.spec, args.qa)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
