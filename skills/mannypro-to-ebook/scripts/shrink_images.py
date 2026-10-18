#!/usr/bin/env python3
"""Copy an assets tree to a new folder with images normalised for e-ink readers.

usage: shrink_images.py <src_assets_dir> <dst_dir> [--max 1400] [--png-threshold 300000]
                        [--quality 82] [--jpeg-threshold 600000] [--requality 75]

Rules (same on every platform):
  * images wider or taller than --max are scaled down proportionally
  * the real format is sniffed from the file header, not the extension: the site serves
    JPEG and WebP files under .png names, and EPUB readers only reliably render real
    PNG/JPEG, so anything mislabelled is re-encoded and given the right extension
  * PNG/WebP files larger than --png-threshold bytes become JPEG (charts shrink 3-5x with no
    visible loss on e-ink); md2epub.py resolves .png -> .jpg automatically
  * JPEG files larger than --jpeg-threshold bytes are re-saved at --requality
  * files that need none of the above are copied byte-for-byte (no re-encoding)

Backends: Pillow if installed (`pip install pillow`), otherwise macOS `sips`.
With neither, files are copied unchanged and a warning is printed.
"""
import argparse, os, shutil, subprocess, sys

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--max', type=int, default=1400)
ap.add_argument('--png-threshold', type=int, default=300_000)
ap.add_argument('--quality', type=int, default=82)
ap.add_argument('--jpeg-threshold', type=int, default=600_000)
ap.add_argument('--requality', type=int, default=75)
a = ap.parse_args()

try:
    from PIL import Image
    BACKEND = 'pillow'
except ImportError:
    Image = None
    BACKEND = 'sips' if shutil.which('sips') else None
    if BACKEND is None:
        sys.stderr.write('warning: neither Pillow nor sips available; images copied without downscaling\n')

IMG_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

def sniff(path):
    with open(path, 'rb') as f: head = f.read(16)
    if head.startswith(b'\x89PNG'): return 'png'
    if head.startswith(b'\xff\xd8'): return 'jpeg'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP': return 'webp'
    if head.startswith(b'GIF8'): return 'gif'
    return 'unknown'

def dims(path):
    if BACKEND == 'pillow':
        with Image.open(path) as im: return im.size
    out = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', path],
                         capture_output=True, text=True).stdout
    w = h = 0
    for line in out.splitlines():
        if 'pixelWidth' in line: w = int(line.split()[-1])
        if 'pixelHeight' in line: h = int(line.split()[-1])
    return w, h

def plan(src, ext):
    """Return (target_format, needs_reencode, quality) for one image."""
    size = os.path.getsize(src)
    real = sniff(src)
    w, h = dims(src)
    resize = max(w, h) > a.max
    if real == 'jpeg':
        target = 'jpeg'
        big = size > a.jpeg_threshold
        reencode = resize or big or ext not in ('.jpg', '.jpeg')
        quality = a.requality if big else a.quality
    else:  # png / webp / gif / unknown
        target = 'jpeg' if size > a.png_threshold else 'png'
        reencode = resize or target == 'jpeg' or real != 'png' or ext != '.png'
        quality = a.quality
    return target, reencode, quality

def with_pillow(src, dst, target, quality):
    im = Image.open(src)
    im.thumbnail((a.max, a.max))  # no-op when already small enough
    if target == 'jpeg':
        if im.mode in ('RGBA', 'LA', 'P'):
            rgba = im.convert('RGBA')
            bg = Image.new('RGB', im.size, (255, 255, 255))
            bg.paste(rgba, mask=rgba.split()[-1]); im = bg
        elif im.mode != 'RGB':
            im = im.convert('RGB')
        im.save(dst, 'JPEG', quality=quality, optimize=True)
    else:
        im.save(dst, 'PNG', optimize=True)

def with_sips(src, dst, target, quality):
    # sips reads WebP but cannot write it, so always produce a fresh PNG/JPEG via --out
    args = ['sips', '-Z', str(a.max), '-s', 'format', target]
    if target == 'jpeg': args += ['-s', 'formatOptions', str(quality)]
    r = subprocess.run(args + [src, '--out', dst], capture_output=True, text=True)
    if r.returncode != 0: raise RuntimeError(r.stderr.strip() or r.stdout.strip())

n_img = n_jpeg = n_copy = 0
for root, _, files in os.walk(a.src):
    rel_root = os.path.relpath(root, a.src)
    out_root = os.path.join(a.dst, rel_root) if rel_root != '.' else a.dst
    os.makedirs(out_root, exist_ok=True)
    for name in files:
        src = os.path.join(root, name)
        base, ext = os.path.splitext(name)
        ext = ext.lower()
        if ext not in IMG_EXT or BACKEND is None:
            shutil.copy2(src, os.path.join(out_root, name)); continue
        try:
            target, reencode, quality = plan(src, ext)
            if not reencode:
                shutil.copy2(src, os.path.join(out_root, name)); n_copy += 1; continue
            dst = os.path.join(out_root, base + ('.jpg' if target == 'jpeg' else '.png'))
            (with_pillow if BACKEND == 'pillow' else with_sips)(src, dst, target, quality)
            if not os.path.exists(dst): raise RuntimeError('backend produced no output')
            n_img += 1; n_jpeg += (target == 'jpeg')
        except Exception as e:
            sys.stderr.write(f'warning: {src}: {e}; copied as-is\n')
            shutil.copy2(src, os.path.join(out_root, name))

total = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(a.dst) for f in fs)
print(f'{BACKEND or "copy"}: {n_img} images re-encoded ({n_jpeg} as jpeg), {n_copy} copied unchanged, output {total/1e6:.0f} MB')
