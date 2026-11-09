"""Lay out Gojo Satoru's Infinity so that every chapter starts on a new page.

    python scripts/gojo_chapter_pages.py
    python scripts/build_pdfs.py gojo-infinity

The essay was typeset in LaTeX and only its PDF survives, kept untouched at
essay-sources/gojo-infinity/original.pdf. This script cuts each original page
into horizontal strips at the gaps between lines, then stacks the strips onto
new pages, opening a new page at each chapter heading. Nothing is redrawn:
the text, maths and diagrams are the original vector drawing, so they stay
sharp and selectable at any zoom.

  * Pictures: if essay-sources/gojo-infinity/img/<name>.jpg exists (an upscaled
    copy), it replaces the low-resolution original. See IMAGES below.
  * Page numbers are put back in the essay's own font (digits cut from the
    original footers), counting from 1 on the Introduction, as before.
  * Writes source-pdfs/gojo-infinity.pdf and prints the page each chapter now
    starts on, for "sections" in public/data/books.json.

Needs: pip install pymupdf
"""
import re
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "essay-sources" / "gojo-infinity"
ORIGINAL = SRC_DIR / "original.pdf"
OUT = ROOT / "source-pdfs" / "gojo-infinity.pdf"

# Picture in the original PDF (by its size in pixels) -> file in img/
IMAGES = {
    (235, 332): "cover.jpg",    # title page: Gojo
    (249, 140): "figure-1.jpg",  # Infinity stopping an attack
    (250, 112): "figure-7.jpg",  # Hino (RIKEN) notes
    (226, 156): "figure-9.jpg",  # Mahoraga
    (158, 175): "figure-11.jpg",  # Sukuna's World Cutting Slash
}

FOOTER_Y = 785      # anything below this is the page number
TOP = 69.6          # where a chapter heading sits
TEXT_TOP = 73.0     # where the first line of a continued page sits
BOTTOM = 774.0      # lowest point the body may reach
LINE_GAP = 5.0      # gap between two lines of a paragraph
BLOCK_GAP = 16.0    # gap around figures and equations

pymupdf.TOOLS.mupdf_display_errors(False)


def swap_images(doc):
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, "Subtype")[1] != "/Image":
            continue
        size = int(doc.xref_get_key(xref, "Width")[1]), int(doc.xref_get_key(xref, "Height")[1])
        path = SRC_DIR / "img" / IMAGES.get(size, "-")
        if not path.exists():
            continue
        pix = pymupdf.Pixmap(str(path))
        doc.update_stream(xref, path.read_bytes(), compress=False)
        for key, val in (("Filter", "/DCTDecode"), ("DecodeParms", "null"), ("Width", str(pix.width)),
                         ("Height", str(pix.height)), ("BitsPerComponent", "8"),
                         ("ColorSpace", "/DeviceGray" if pix.n == 1 else "/DeviceRGB")):
            doc.xref_set_key(xref, key, val)
        print(f"  picture {size[0]}x{size[1]} -> {path.name} ({pix.width}x{pix.height})")


class Block:
    """A horizontal band of a page with nothing crossing its top or bottom edge."""

    def __init__(self, pno, y0, y1, items):
        self.pno, self.y0, self.y1, self.items = pno, y0, y1, items
        lines = [i for i in items if i["kind"] == "text"]
        first = min(lines, key=lambda i: (i["y0"], i["x0"])) if lines else None
        self.text = " ".join(i["text"] for i in sorted(lines, key=lambda i: (i["y0"], i["x0"])))
        self.heading = bool(first) and first["size"] > 13
        # One ordinary line of a paragraph: 10 pt text starting at the margin or indent
        self.prose = (len(lines) > 0 and all(i["kind"] == "text" or i["h"] < 3 for i in items)
                      and abs(first["size"] - 10) < 0.5 and min(i["x0"] for i in items) > 70
                      and round(first["x0"]) in (71, 86))
        self.indent = bool(first) and round(first["x0"]) == 86
        self.zone = None  # figure number, for every band of a figure and its caption

    @property
    def h(self):
        return self.y1 - self.y0


def page_blocks(page):
    items = []
    for b in page.get_text("dict")["blocks"]:
        if b["type"] == 1:
            x0, y0, x1, y1 = b["bbox"]
            items.append({"kind": "image", "y0": y0, "y1": y1, "x0": x0, "h": y1 - y0})
            continue
        for line in b["lines"]:
            x0, y0, x1, y1 = line["bbox"]
            items.append({"kind": "text", "y0": y0, "y1": y1, "x0": x0, "h": y1 - y0,
                          "size": line["spans"][0]["size"], "text": "".join(s["text"] for s in line["spans"])})
    for d in page.get_drawings():
        r = d["rect"]
        items.append({"kind": "draw", "y0": r.y0, "y1": r.y1, "x0": r.x0, "h": r.height})
    items = sorted((i for i in items if i["y0"] < FOOTER_Y), key=lambda i: i["y0"])
    bands = []
    for it in items:
        if bands and it["y0"] < bands[-1][1]:
            bands[-1][1] = max(bands[-1][1], it["y1"])
            bands[-1][2].append(it)
        else:
            bands.append([it["y0"], it["y1"], [it]])
    return [Block(page.number, y0, y1, its) for y0, y1, its in bands]


def mark_figures(blocks):
    """A figure is its caption plus every non-paragraph band straight above it."""
    for i, b in enumerate(blocks):
        m = re.match(r"Figure (\d+):", b.text)
        if not m:
            continue
        n = int(m.group(1))
        b.zone = n
        j = i + 1  # rest of the caption
        while j < len(blocks) and blocks[j].pno == b.pno and blocks[j].y0 - blocks[j - 1].y1 < 3:
            blocks[j].zone = n
            j += 1
        j = i - 1  # the picture or diagram
        while j >= 0 and blocks[j].pno == b.pno and not blocks[j].prose and not blocks[j].heading:
            blocks[j].zone = n
            j -= 1


def can_break(blocks, i):
    """May a page end after blocks[i]?"""
    a, b = blocks[i], blocks[i + 1]
    if a.zone and a.zone == b.zone:
        return False
    ok_after = a.prose if not a.zone else True
    ok_before = b.prose if not b.zone else True
    if not (ok_after and ok_before):
        return False
    if a.prose and a.indent and not a.zone:
        return False  # don't leave a paragraph's first line alone at the foot of a page
    nxt = blocks[i + 2] if i + 2 < len(blocks) else None
    if b.prose and not b.zone and (nxt is None or nxt.indent or not nxt.prose or nxt.heading):
        return False  # nor its last line alone at the top of the next
    return True


def gap_between(a, b):
    if a.pno == b.pno:
        return b.y0 - a.y1
    return LINE_GAP if a.prose and b.prose and not a.zone and not b.zone else BLOCK_GAP


def strip_source(doc, pno, keep, cache):
    """A one-page copy of page pno with only the text inside `keep` left in it,
    so the text layer of the new page holds no hidden copies of other strips."""
    key = (pno, tuple(round(v, 2) for v in keep))
    if key not in cache:
        tmp = pymupdf.open()
        tmp.insert_pdf(doc, from_page=pno, to_page=pno)
        page = tmp[0]
        r = page.rect + (-50, -50, 50, 50)
        for area in (pymupdf.Rect(r.x0, r.y0, r.x1, keep.y0), pymupdf.Rect(r.x0, keep.y1, r.x1, r.y1),
                     pymupdf.Rect(r.x0, keep.y0, keep.x0, keep.y1), pymupdf.Rect(keep.x1, keep.y0, r.x1, keep.y1)):
            if area.width > 0 and area.height > 0:
                page.add_redact_annot(area)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE,
                              text=pymupdf.PDF_REDACT_TEXT_REMOVE)
        cache[key] = tmp
    return cache[key]


def footer_digits(doc):
    """Each digit of the footer font: (source page, clip rect, baseline y)."""
    digits = {}
    for page in doc:
        for b in page.get_text("rawdict")["blocks"]:
            for line in b.get("lines", []):
                for span in line["spans"]:
                    if abs(span["size"] - 10) > 0.3 or not span["font"].endswith("CMR10"):
                        continue
                    for ch in span["chars"]:
                        c = ch["c"]
                        if c.isdigit() and c not in digits:
                            digits[c] = (page.number, pymupdf.Rect(ch["bbox"]), ch["origin"][1])
    return digits


def main():
    src = pymupdf.open(ORIGINAL)
    swap_images(src)
    digits = footer_digits(src)
    footer = next(b for b in src[1].get_text("dict")["blocks"] if b["type"] == 0 and b["bbox"][1] > FOOTER_Y)
    foot_base = footer["lines"][0]["spans"][0]["origin"][1]
    centre = (footer["bbox"][0] + footer["bbox"][2]) / 2

    blocks = [b for p in src if p.number > 0 for b in page_blocks(p)]
    mark_figures(blocks)

    # Pack the bands onto pages: [ [block, ...], ... ]
    pages, cur, y = [], [], 0.0
    for i, b in enumerate(blocks):
        if b.heading or not cur:
            if cur:
                pages.append(cur)
            cur = [b]
            y = (TOP if b.heading else TEXT_TOP if b.prose else b.y0) + b.h
            continue
        gap = gap_between(cur[-1], b)
        # Height of b plus everything glued to it that must come along
        j, need = i, b.h
        while j + 1 < len(blocks) and not blocks[j + 1].heading and not can_break(blocks, j):
            need += gap_between(blocks[j], blocks[j + 1]) + blocks[j + 1].h
            j += 1
        if y + gap + need > BOTTOM and can_break(blocks, i - 1):
            pages.append(cur)
            cur = [b]
            y = (TEXT_TOP if b.prose else max(TOP, min(b.y0, TEXT_TOP))) + b.h
        else:
            cur.append(b)
            y += gap + b.h
    pages.append(cur)

    out = pymupdf.open()
    out.insert_pdf(src, from_page=0, to_page=0)  # title page as it is
    width, height = src[0].rect.width, src[0].rect.height
    cache, sections = {}, []
    for n, page_blocks_ in enumerate(pages, start=1):
        page = out.new_page(width=width, height=height)
        first = page_blocks_[0]
        y = TOP if first.heading else TEXT_TOP if first.prose else max(TOP, min(first.y0, TEXT_TOP))
        # Runs of bands that sit together on the same original page go in as one strip
        runs, prev = [], None
        for b in page_blocks_:
            if prev is not None and prev.pno == b.pno:
                runs[-1].append(b)
            else:
                runs.append([b])
            prev = b
        for k, run in enumerate(runs):
            if k:
                y += gap_between(runs[k - 1][-1], run[0])
            sp = src[run[0].pno]
            # Cut halfway into the gap above and below, so no glyph edge is lost
            idx0, idx1 = blocks.index(run[0]), blocks.index(run[-1])
            above = blocks[idx0 - 1] if idx0 and blocks[idx0 - 1].pno == run[0].pno else None
            below = blocks[idx1 + 1] if idx1 + 1 < len(blocks) and blocks[idx1 + 1].pno == run[0].pno else None
            pad_top = min(6, (run[0].y0 - above.y1) / 2) if above else 6
            pad_bot = min(6, (below.y0 - run[-1].y1) / 2) if below else min(6, FOOTER_Y - run[-1].y1)
            clip = pymupdf.Rect(0, run[0].y0 - pad_top, sp.rect.width, run[-1].y1 + pad_bot)
            strip = strip_source(src, run[0].pno, clip, cache)
            dest = pymupdf.Rect(0, y - pad_top, sp.rect.width, y - pad_top + clip.height)
            page.show_pdf_page(dest, strip, 0, clip=clip)
            y += run[-1].y1 - run[0].y0
        # Page number, centred, cut from the original footer glyphs
        label = str(n)
        widths = [digits[c][1].width for c in label]
        x = centre - sum(widths) / 2
        for c, w in zip(label, widths):
            dpno, box, base = digits[c]
            dest = pymupdf.Rect(x, box.y0 - base + foot_base, x + w, box.y1 - base + foot_base)
            page.show_pdf_page(dest, strip_source(src, dpno, box, cache), 0, clip=box)
            x += w
        if first.heading:
            title = re.sub(r"^\d+\s*", "", first.text).strip()
            sections.append((title, n + 1))

    out.set_toc([[1, t, p] for t, p in sections])
    out.set_metadata(src.metadata)
    OUT.parent.mkdir(exist_ok=True)
    out.save(OUT, garbage=4, deflate=True)
    print(f"Wrote {OUT.relative_to(ROOT)}: {out.page_count} pages")
    for t, p in sections:
        print(f"  page {p:2}: {t}")


if __name__ == "__main__":
    main()
