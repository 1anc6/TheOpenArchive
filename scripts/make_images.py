"""Make the picture shown on each essay's card (public/images/<id>.jpg).

    python scripts/make_images.py

Each picture is cut from the essay's PDF in source-pdfs/: either one of
the images inside it, or a band of a designed page such as the cover.
Existing pictures are kept; delete one to make it again.
"""
from pathlib import Path

import pymupdf
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "public" / "images"
SRC = ROOT / "source-pdfs"
W, H = 1200, 845  # 1.42 : 1, the card photo shape

INK = "#2c1810"

pymupdf.TOOLS.mupdf_display_errors(False)

# Pictures taken from the essays themselves: n-th largest image in the PDF
FROM_PDF = {
    "gojo-infinity": 2,
}
# Pictures cut from a whole page: (page index, top, bottom[, left, right]) as fractions of the page.
# For PDFs drawn as one designed page with no separate images, like a project cover.
FROM_PAGE = {
    "metaproof": (0, 0.0, 0.5),  # cover: title, tagline and rings, not the stats
    "campussafe": (0, 0.0, 0.5),
    "metrigo": (0, 0.376, 0.713, 0.024, 0.70),  # the network map, without the legend
    # Essays designed in essay-sources/: a band of the cover
    "a-paradox-that-isnt": (0, 0.0, 0.5),
    "ai-is-unintelligent": (0, 0.1, 0.6),
    "tale-of-two-infinities": (0, 0.0, 0.5),
    "proof-for-the-unprovable": (0, 0.03, 0.53),
    "glitch-in-the-fourth-wall": (0, 0.08, 0.58),
    "secret-santa": (0, 0.05, 0.55),
    "prisoners-dilemma": (0, 0.3, 0.8),
    "lego-maths": (0, 0.06, 0.56),
    "planet-of-fractal-geometry": (0, 0.05, 0.55),
    "patterns-in-nature": (0, 0.05, 0.55),
    "absolute-cinema-of-math": (0, 0.32, 0.82),
    "spooky-action": (0, 0.06, 0.56),
    "where-physics-runs-out": (0, 0.0, 0.45),
}
# Text at or above this size (pt) is left out of a page picture, e.g. a cover paragraph
# that overlaps the edge of the map; small labels stay.
HIDE_TEXT = {"metrigo": 9}
# Pictures with their title running edge to edge: shown whole on a blurred copy
# of themselves instead of being cropped to the card shape.
FIT = set()


def fit(img: Image.Image) -> Image.Image:
    """The whole picture, centred on a blurred, darkened, cover-cropped copy of itself."""
    img = img.convert("RGB")
    w, h = img.size
    s = max(W / w, H / h)
    bg = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    bg = bg.crop(((bg.width - W) // 2, (bg.height - H) // 2, (bg.width - W) // 2 + W, (bg.height - H) // 2 + H))
    bg = Image.blend(bg.filter(ImageFilter.GaussianBlur(28)), Image.new("RGB", (W, H), INK), 0.25)
    s = min(W / w, H / h)
    fg = img.resize((round(w * s), round(h * s)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def save(img: Image.Image, name: str):
    img = img.convert("RGB")
    if name in FIT:
        img = fit(img)
    # cover-crop to the card shape
    r = W / H
    w, h = img.size
    if w / h > r:
        nw = int(h * r)
        img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / r)
        img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img = img.resize((W, H), Image.LANCZOS)
    img.save(OUT / f"{name}.jpg", quality=82, optimize=True, progressive=True)
    print(f"  {name}.jpg")


def from_pdf(name: str, spec):
    rank, y0, y1 = spec if isinstance(spec, tuple) else (spec, 0.0, 1.0)
    doc = pymupdf.open(SRC / f"{name}.pdf")
    best = {}  # xref -> (shown area, page, rect)
    for page in doc:
        for im in page.get_images(full=True):
            for r in page.get_image_rects(im[0]):
                if im[0] not in best or r.width * r.height > best[im[0]][0]:
                    best[im[0]] = (r.width * r.height, page.number, r)
    found = sorted(best.values(), key=lambda f: -f[0])
    _, pno, rect = found[rank]
    rect = pymupdf.Rect(rect.x0, rect.y0 + rect.height * y0, rect.x1, rect.y0 + rect.height * y1)
    pix = doc[pno].get_pixmap(clip=rect, dpi=220)
    save(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), name)


def from_page(name: str, spec):
    pno, y0, y1, x0, x1 = (*spec, 0.0, 1.0) if len(spec) == 3 else spec
    page = pymupdf.open(SRC / f"{name}.pdf")[pno]
    if name in HIDE_TEXT:  # on this in-memory copy only; the PDF itself is untouched
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                for span in line["spans"]:
                    if span["size"] >= HIDE_TEXT[name]:
                        page.add_redact_annot(span["bbox"], fill=False)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_NONE)
    r = page.rect
    clip = pymupdf.Rect(r.x0 + r.width * x0, r.y0 + r.height * y0, r.x0 + r.width * x1, r.y0 + r.height * y1)
    pix = page.get_pixmap(clip=clip, dpi=300)
    save(Image.frombytes("RGB", (pix.width, pix.height), pix.samples), name)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # Existing pictures are kept. Delete a picture to regenerate it.
    for name, spec in FROM_PDF.items():
        if (OUT / f"{name}.jpg").exists():
            print(f"  {name}.jpg kept")
            continue
        from_pdf(name, spec)
    for name, spec in FROM_PAGE.items():
        if (OUT / f"{name}.jpg").exists():
            print(f"  {name}.jpg kept")
            continue
        from_page(name, spec)


if __name__ == "__main__":
    main()
