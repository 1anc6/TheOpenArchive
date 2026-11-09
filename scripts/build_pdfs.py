"""Build the web copies of the essay PDFs from the originals.

    python scripts/build_pdfs.py            # all books
    python scripts/build_pdfs.py gojo-infinity lego-maths   # just these

How it works:
  * The untouched originals live in source-pdfs/. Always edit those, then re-run.
  * Each one is shrunk for the web and written to public/books/<file>.pdf,
    and the page count in public/data/books.json is updated.

Needs: pip install pymupdf
"""
import json
import re
import shutil
import sys
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
ORIGINALS = ROOT / "source-pdfs"
BOOKS_JSON = PUBLIC / "data" / "books.json"

pymupdf.TOOLS.mupdf_display_errors(False)


def embed_missing_fonts(doc, name):
    """Some PDFs name a font (e.g. Times New Roman) without including it, so each
    browser substitutes its own and the text comes out garbled or misaligned.
    Re-writing the document through MuPDF embeds the fonts it draws with; the
    text stays real, selectable text."""
    # Type 3 fonts also report "n/a", but their glyphs are drawn inside the PDF itself.
    missing = {f[3] for page in doc for f in page.get_fonts() if f[1] == "n/a" and f[2] != "Type3"}
    if not missing:
        return doc
    meta = doc.metadata
    fixed = pymupdf.open("pdf", doc.convert_to_pdf())
    fixed.set_metadata(meta)
    print(f"  {name}: embedded fonts {sorted(missing)}")
    return fixed


def type3_glyphs(doc):
    """The drawing of every Type 3 glyph, by xref."""
    glyphs = {}
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, "Subtype") != ("name", "/Type3"):
            continue
        kind, procs = doc.xref_get_key(xref, "CharProcs")
        if kind == "xref":
            procs = doc.xref_object(int(procs.split()[0]))
        for g in re.findall(r"(\d+) 0 R", procs):
            glyphs[int(g)] = doc.xref_stream(int(g))
    return glyphs


def pattern_resources(doc):
    """The /Pattern and /Shading entries of every resource dictionary, by xref.
    Chrome draws CSS gradients and background images as patterns."""
    found = {}
    for xref in range(1, doc.xref_length()):
        for path in ("Resources/", ""):
            pat = doc.xref_get_key(xref, path + "Pattern")
            if pat[0] in ("dict", "xref"):
                found[(xref, path)] = (pat[1], doc.xref_get_key(xref, path + "Shading"))
    return found


def restore_patterns(doc, saved):
    """MuPDF's image pass swaps each /Pattern resource for a /Shading one set to
    null. PDF.js then stops drawing the page at the first gradient or patterned
    image ("Unknown PatternName"), leaving the rest of it blank."""
    for (xref, path), (pattern, (kind, shading)) in saved.items():
        doc.xref_set_key(xref, path + "Pattern", pattern)
        doc.xref_set_key(xref, path + "Shading", shading if kind in ("dict", "xref") else "null")


def shrink_images(doc, max_side=2400, quality=90):
    """Downsample big images and store photos as JPEG, changing each image
    object in place. Used for the essays printed from HTML: MuPDF's own image
    pass rewrites their page drawings and drops the photos Chrome draws as
    patterns (cover pictures, rounded-corner photos)."""
    masks = {int(v.split()[0]) for x in range(1, doc.xref_length())
             for k, v in [doc.xref_get_key(x, "SMask")] if k == "xref"}
    for xref in range(1, doc.xref_length()):
        if xref in masks or doc.xref_get_key(xref, "Subtype")[1] != "/Image":
            continue
        raw = len(doc.xref_stream_raw(xref))
        w, h = int(doc.xref_get_key(xref, "Width")[1]), int(doc.xref_get_key(xref, "Height")[1])
        is_jpeg = doc.xref_get_key(xref, "Filter")[1] == "/DCTDecode"
        if max(w, h) <= max_side and (is_jpeg or raw < 400_000):
            continue
        pix = pymupdf.Pixmap(doc, xref)
        if pix.alpha:
            pix = pymupdf.Pixmap(pix, 0)
        if pix.colorspace is None or pix.colorspace.n not in (1, 3):
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        f = min(1, max_side / max(w, h))
        nw, nh = max(1, round(w * f)), max(1, round(h * f))
        if f < 1:
            pix = pymupdf.Pixmap(pix, nw, nh, None)
        jpg = pix.tobytes("jpg", jpg_quality=quality)
        if f == 1 and len(jpg) > raw * 0.5:
            continue  # not worth it
        doc.update_stream(xref, jpg, compress=False)
        for key, val in (("Filter", "/DCTDecode"), ("DecodeParms", "null"), ("Width", str(nw)), ("Height", str(nh)),
                         ("BitsPerComponent", "8"), ("ColorSpace", "/DeviceGray" if pix.n == 1 else "/DeviceRGB"),
                         ("Decode", "null")):
            doc.xref_set_key(xref, key, val)
        kind, mask = doc.xref_get_key(xref, "SMask")
        if kind == "xref" and f < 1:
            m = int(mask.split()[0])
            mpix = pymupdf.Pixmap(pymupdf.Pixmap(doc, m), nw, nh, None)
            doc.update_stream(m, mpix.samples, compress=True)
            for key, val in (("Width", str(nw)), ("Height", str(nh)), ("BitsPerComponent", "8"),
                             ("ColorSpace", "/DeviceGray"), ("DecodeParms", "null")):
                doc.xref_set_key(m, key, val)


def unique_type3_names(doc):
    """Chrome gives outlined text two Type 3 fonts (the halo and the letters) with
    one FontName. PDF.js tells fonts apart by name, so it draws the halo's shapes
    in the letters' colour and the labels turn into black blobs. Each repeat gets
    its own copy of the (shared) font descriptor under a new name."""
    seen = set()
    for xref in range(1, doc.xref_length()):
        if doc.xref_get_key(xref, "Subtype") != ("name", "/Type3"):
            continue
        kind, fd = doc.xref_get_key(xref, "FontDescriptor")
        if kind != "xref":
            continue
        fd = int(fd.split()[0])
        name = doc.xref_get_key(fd, "FontName")[1]
        if name in seen:
            copy = doc.get_new_xref()
            doc.update_object(copy, doc.xref_object(fd))
            doc.xref_set_key(copy, "FontName", f"{name}-{xref}")
            doc.xref_set_key(xref, "FontDescriptor", f"{copy} 0 R")
        seen.add(name)


def main(only):
    books = json.loads(BOOKS_JSON.read_text(encoding="utf-8"))
    ORIGINALS.mkdir(exist_ok=True)

    for book in books:
        if only and book["id"] not in only:
            continue
        target = PUBLIC / book["file"]
        original = ORIGINALS / Path(book["file"]).name
        if not original.exists():
            shutil.copy2(target, original)  # first run: keep the untouched PDF

        doc = pymupdf.open(original)
        doc = embed_missing_fonts(doc, book["id"])
        if (ROOT / "essay-sources" / book["id"]).is_dir():
            # Essays printed from HTML (see shrink_images), and Gojo's Infinity,
            # whose upscaled pictures would otherwise be cut back to 150 dpi.
            shrink_images(doc)
        else:
            # Downsample big images to 150 dpi and re-encode them as JPEG.
            # That pass also rewrites Type 3 glyphs and adds "0 g" to each, which
            # PDF.js obeys: outlined labels and coloured text come out black in
            # the reader. So the glyphs are put back as they were.
            glyphs = type3_glyphs(doc)
            patterns = pattern_resources(doc)
            doc.rewrite_images(dpi_threshold=200, dpi_target=150, quality=78)
            for xref, stream in glyphs.items():
                doc.update_stream(xref, stream)
            restore_patterns(doc, patterns)
        unique_type3_names(doc)
        # Keep only the characters each embedded font actually uses
        # (e.g. Secret Santa embedded a whole 3.8 MB emoji font).
        try:
            doc.subset_fonts()
        except Exception as err:
            print(f"  {book['id']}: font subsetting skipped ({err})")
        doc.set_metadata({**doc.metadata, "title": book["title"], "author": book["author"]})
        doc.save(target, garbage=4, deflate=True, use_objstms=1)
        book["pages"] = doc.page_count
        doc.close()
        print(f"  {book['id']}: {book['pages']} pages, {target.stat().st_size // 1024} KB")

    BOOKS_JSON.write_text(json.dumps(books, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("Done. Updated page counts in public/data/books.json")


if __name__ == "__main__":
    main(set(sys.argv[1:]))
