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
        # Downsample big images to 150 dpi and re-encode them as JPEG.
        # That pass also rewrites Type 3 glyphs (text in PDFs printed from Chrome)
        # and adds "0 g" to each, which PDF.js obeys: outlined labels and coloured
        # text come out black in the reader. So the glyphs are put back as they were.
        glyphs = type3_glyphs(doc)
        doc.rewrite_images(dpi_threshold=200, dpi_target=150, quality=78)
        for xref, stream in glyphs.items():
            doc.update_stream(xref, stream)
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
