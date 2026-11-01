#!/usr/bin/env python3
"""Make a report PDF lighter without changing a single pixel.

    python3 tools/shrink_pdf.py data/reports/pdf/2026-55-lockheed-martin.pdf [more.pdf ...]

Some exports (Chromium's "Save as PDF" among them) store the same image again
on every page that shows it: a background texture repeated on 16 pages made a
16-page report weigh 19 MB. This keeps one copy of each identical image or
stream and points every page at it. Nothing is re-encoded, so every page looks
exactly as before; the file is rewritten only when it gets smaller, and only
after each page has been rendered before and after and found identical (when
pdftoppm is installed) and its text is unchanged (when pdftotext is).

Needs the pikepdf package (pip install pikepdf). tools/import_report.py runs it
on every new report when pikepdf is installed.
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MIN_STREAM = 4096  # smaller streams are not worth comparing


def _key(stream, keys):
    """Identity of a stream: its stored bytes and its dictionary, with any soft mask by its own identity."""
    parts = []
    for k in sorted(stream.keys()):
        if k == "/Length":
            continue
        v = stream[k]
        if k == "/SMask" and v.objgen in keys:
            parts.append(f"{k}=mask:{keys[v.objgen]}")
        else:
            parts.append(f"{k}={v!r}")
    h = hashlib.sha256(stream.read_raw_bytes())
    h.update("\n".join(parts).encode("utf-8"))
    return h.hexdigest()


def dedupe(pdf):
    """Point every reference to a duplicate stream at its first copy. Returns the number of duplicates."""
    import pikepdf

    streams = [o for o in pdf.objects if isinstance(o, pikepdf.Stream) and len(o.read_raw_bytes()) >= MIN_STREAM]
    keys, first, same = {}, {}, {}
    # masks first, so an image's identity can include its mask's
    for s in sorted(streams, key=lambda o: "/SMask" in o):
        k = _key(s, keys)
        keys[s.objgen] = k
        if k in first:
            same[s.objgen] = first[k]
        else:
            first[k] = s
    if not same:
        return 0

    seen = set()

    def dup(v):
        # scalars come back as plain Python values; only PDF objects can be references
        return isinstance(v, pikepdf.Object) and v.is_indirect and v.objgen in same

    def walk(obj):
        if isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream)):
            items = list(obj.items())
            for k, v in items:
                if k == "/Parent":
                    continue
                if dup(v):
                    obj[k] = same[v.objgen]
                else:
                    visit(v)
        elif isinstance(obj, pikepdf.Array):
            for i in range(len(obj)):
                v = obj[i]
                if dup(v):
                    obj[i] = same[v.objgen]
                else:
                    visit(v)

    def visit(v):
        if isinstance(v, (pikepdf.Dictionary, pikepdf.Stream, pikepdf.Array)):
            if v.is_indirect:
                if v.objgen in seen:
                    return
                seen.add(v.objgen)
            walk(v)

    visit(pdf.Root)
    for page in pdf.pages:
        visit(page.obj)
    return len(same)


def _render(pdf_path, out_dir):
    subprocess.run(["pdftoppm", "-r", "40", "-png", str(pdf_path), str(out_dir / "p")], check=True,
                   capture_output=True)
    return sorted(out_dir.glob("p*.png"))


def _same_pixels(a, b):
    from PIL import Image, ImageChops

    with tempfile.TemporaryDirectory() as t:
        da, db = Path(t, "a"), Path(t, "b")
        da.mkdir()
        db.mkdir()
        pa, pb = _render(a, da), _render(b, db)
        if len(pa) != len(pb):
            return False
        for x, y in zip(pa, pb):
            with Image.open(x) as ix, Image.open(y) as iy:
                if ix.size != iy.size or ImageChops.difference(ix.convert("RGB"), iy.convert("RGB")).getbbox():
                    return False
    return True


def _text(path):
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True).stdout


def shrink(path):
    """Rewrite path in place when lighter and identical. Returns (bytes before, bytes after)."""
    import pikepdf

    path = Path(path)
    before = path.stat().st_size
    with tempfile.TemporaryDirectory() as t:
        out = Path(t, path.name)
        with pikepdf.open(path) as pdf:
            if not dedupe(pdf):
                return before, before
            pdf.save(out, object_stream_mode=pikepdf.ObjectStreamMode.generate, compress_streams=True,
                     recompress_flate=False)
        after = out.stat().st_size
        if after >= before:
            return before, before
        if shutil.which("pdftotext") and _text(path) != _text(out):
            raise RuntimeError(f"{path.name}: the text changed; left as it is")
        if shutil.which("pdftoppm"):
            try:
                import PIL  # noqa: F401
            except ImportError:
                PIL = None
            if PIL is not None and not _same_pixels(path, out):
                raise RuntimeError(f"{path.name}: a page renders differently; left as it is")
        shutil.copyfile(out, path)
    return before, after


def main():
    try:
        import pikepdf  # noqa: F401
    except ImportError:
        sys.exit("Needs pikepdf: pip install pikepdf")
    if len(sys.argv) < 2:
        sys.exit(__doc__.strip().split("\n\n")[1])
    for arg in sys.argv[1:]:
        before, after = shrink(arg)
        mb = lambda n: f"{n / 1e6:.1f} MB"  # noqa: E731
        print(f"{Path(arg).name}: {mb(before)} -> {mb(after)}" if after < before else
              f"{Path(arg).name}: {mb(before)}, nothing to remove")


if __name__ == "__main__":
    main()
