#!/usr/bin/env python3
"""Build a single EPUB (or Kobo KEPUB) from exported 曼報 Pro markdown articles.
Usage: md2epub.py <articles_dir> <images_dir> <out_epub> [--kepub] [--from YYYYMMDD] [--to YYYYMMDD]
  articles_dir : folder of "YYYYMMDD 標題.md" files (images referenced as assets/<slug>/x)
  images_dir   : folder mirroring articles_dir/assets (usually a downscaled copy)
  --kepub      : add koboSpan wrappers so Kobo's native renderer is used
  --from/--to  : only include articles whose date prefix is within the range (inclusive)
"""
import sys, os, re, html, zipfile, uuid, datetime, glob, argparse
from xml.dom import minidom

_ap = argparse.ArgumentParser()
_ap.add_argument('articles'); _ap.add_argument('images'); _ap.add_argument('out')
_ap.add_argument('--kepub', action='store_true')
_ap.add_argument('--from', dest='date_from', default='00000000')
_ap.add_argument('--to', dest='date_to', default='99999999')
_a = _ap.parse_args()
ARTICLES, IMAGES, OUT, KEPUB = _a.articles, _a.images, _a.out, _a.kepub

# ---------- inline markdown ----------
LINK_RE = re.compile(r'\[([^\[\]]*)\]\(((?:[^()\s]|\([^()]*\))+)\)')
IMG_RE  = re.compile(r'!\[([^\]]*)\]\(((?:[^()\s]|\([^()]*\))+)\)')
TRIPLE_RE = re.compile(r'\*\*\*(?!\s)(.+?)(?<!\s)\*\*\*')
BOLD_RE = re.compile(r'\*\*(.+?)\*\*')
ITAL_RE = re.compile(r'(?<!\*)\*(?![\s*])([^*\n]+?)(?<!\s)\*(?!\*)')
URL_RE = re.compile(r'https?://[^\s<>"]+')

def attr(s):
    return s.replace('&', '&amp;').replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')

def resolve_img(src):
    """Map markdown image path (assets/slug/x.png) to EPUB path (images/slug/x.ext)."""
    rel = re.sub(r'^assets/', '', src)
    cand = os.path.join(IMAGES, rel)
    if not os.path.exists(cand):
        base, _ = os.path.splitext(cand)
        for ext in ('.jpg', '.jpeg', '.png'):
            if os.path.exists(base + ext):
                cand = base + ext; break
        else:
            return None
    return os.path.relpath(cand, IMAGES)

used_images = {}
def img_tag(alt, src):
    rel = resolve_img(src)
    if rel is None:
        sys.stderr.write(f'missing image: {src}\n'); return ''
    used_images[rel] = True
    return f'<img src="../images/{attr(rel)}" alt="{attr(alt)}"/>'

def inline(text):
    text = html.escape(text, quote=False)
    text = IMG_RE.sub(lambda m: img_tag(m.group(1), m.group(2)), text)
    # links first; protect them from bold/italic passes
    holds = []
    def mk_link(m):
        label = m.group(1)
        if not label.strip('*').strip():  # malformed like [**](url) -> drop link, keep nothing
            return ''
        holds.append(f'<a href="{attr(html.unescape(m.group(2)))}">{inline_fmt(label)}</a>')
        return f'\x00{len(holds)-1}\x00'
    text = LINK_RE.sub(mk_link, text)
    def mk_url(m):
        holds.append(m.group(0)); return f'\x00{len(holds)-1}\x00'
    text = URL_RE.sub(mk_url, text)
    text = inline_fmt(text)
    text = re.sub(r'\x00(\d+)\x00', lambda m: holds[int(m.group(1))], text)
    return text

def inline_fmt(text):
    text = TRIPLE_RE.sub(r'<b><i>\1</i></b>', text)
    text = BOLD_RE.sub(r'<b>\1</b>', text)
    text = ITAL_RE.sub(r'<i>\1</i>', text)
    text = text.replace('**', '')  # stray unmatched markers
    return text

# ---------- block markdown ----------
H_RE   = re.compile(r'^(#{1,6})\s+(.*?)\s*#*$')
UL_RE  = re.compile(r'^( *)[-*+]\s+(.*)$')
OL_RE  = re.compile(r'^( *)(\d+)[.)]\s+(.*)$')
HR_RE  = re.compile(r'^ {0,3}([-*_])( *\1){2,} *$')
IMGLINE_RE = re.compile(r'^\s*!\[([^\]]*)\]\(((?:[^()\s]|\([^()]*\))+)\)\s*$')

def is_cjk(ch):
    return '　' <= ch <= '鿿' or '＀' <= ch <= '￯' or ' ' <= ch <= '⁯'

def para_html(lines):
    out = ''
    for i, ln in enumerate(lines):
        hard = ln.endswith('  ')
        s = ln.strip()
        if not s: continue
        if out and not out.endswith('<br/>'):
            out += '' if (is_cjk(out[-1]) and is_cjk(s[0])) else ' '
        out += inline(s)
        if hard and i < len(lines) - 1:
            out += '<br/>'
    return out

def demote(level):  # body headings sit under the chapter h1
    return max(level, 2)

def parse_blocks(lines, headings=True):
    """Return XHTML for a list of markdown lines."""
    out = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1; continue
        m = H_RE.match(ln)
        if m and headings:
            lvl = demote(len(m.group(1)))
            out.append(f'<h{lvl}>{inline(m.group(2))}</h{lvl}>'); i += 1; continue
        if HR_RE.match(ln):
            out.append('<hr/>'); i += 1; continue
        if ln.lstrip().startswith('>'):
            q = []
            while i < n and (lines[i].lstrip().startswith('>') or (lines[i].strip() and q and not lines[i].lstrip().startswith('>') and False)):
                q.append(re.sub(r'^\s*> ?', '', lines[i])); i += 1
            out.append('<blockquote>' + parse_blocks(q) + '</blockquote>'); continue
        m = IMGLINE_RE.match(ln)
        if m:
            tag = img_tag(m.group(1), m.group(2))
            # optional italic caption on next non-blank line
            j = i + 1
            while j < n and not lines[j].strip(): j += 1
            cap = ''
            if j < n:
                c = lines[j].strip()
                if c.startswith('*') and c.endswith('*') and not c.startswith('**') and len(c) > 2:
                    cap = f'<p class="caption">{inline(c[1:-1])}</p>'; i = j
            out.append(f'<div class="figure">{tag}{cap}</div>'); i += 1; continue
        mu, mo = UL_RE.match(ln), OL_RE.match(ln)
        if mu or mo:
            kind = 'ul' if mu else 'ol'
            indent = len((mu or mo).group(1))
            items = []
            while i < n:
                cur = lines[i]
                if not cur.strip():
                    # loose list: keep going only if next content line is a sibling item
                    j = i
                    while j < n and not lines[j].strip(): j += 1
                    if j < n:
                        mm = (UL_RE if kind == 'ul' else OL_RE).match(lines[j])
                        if mm and len(mm.group(1)) == indent:
                            i = j; continue
                        # continuation of item body if indented deeper
                        if len(lines[j]) - len(lines[j].lstrip()) > indent:
                            items[-1].append(''); i = i + 1; continue
                    break
                mm = (UL_RE if kind == 'ul' else OL_RE).match(cur)
                if mm and len(mm.group(1)) == indent:
                    items.append([mm.group(2 if kind == 'ul' else 3)]); i += 1; continue
                cur_indent = len(cur) - len(cur.lstrip())
                if cur_indent > indent and items:
                    items[-1].append(cur[indent + 2:] if len(cur) > indent + 2 else cur.strip()); i += 1; continue
                break
            lis = []
            for it in items:
                first, rest = it[0], it[1:]
                body = parse_blocks(rest) if any(r.strip() for r in rest) else ''
                if body and not body.startswith('<ul') and not body.startswith('<ol'):
                    lis.append(f'<li><p>{inline(first)}</p>{body}</li>')
                else:
                    lis.append(f'<li>{inline(first)}{body}</li>')
            out.append(f'<{kind}>' + ''.join(lis) + f'</{kind}>'); continue
        # paragraph: gather until blank / block start
        p = []
        while i < n and lines[i].strip() and not (headings and H_RE.match(lines[i])) and not HR_RE.match(lines[i]) \
              and not UL_RE.match(lines[i]) and not OL_RE.match(lines[i]) and not IMGLINE_RE.match(lines[i]) \
              and not lines[i].lstrip().startswith('>'):
            p.append(lines[i]); i += 1
        if p:
            out.append('<p>' + para_html(p) + '</p>')
        else:
            i += 1
    return ''.join(out)

# ---------- article → chapter ----------
def load_article(path):
    text = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    lines = text.split('\n')
    title = os.path.basename(path)[9:-3]
    meta = {}
    body_start = 0
    for idx, ln in enumerate(lines[:12]):
        m = H_RE.match(ln)
        if m and len(m.group(1)) == 1 and not title: title = m.group(2)
        if m and len(m.group(1)) == 1: body_start = idx + 1; continue
        mm = re.match(r'^- (原文|發布日期|分類)：(.*)$', ln)
        if mm: meta[mm.group(1)] = mm.group(2).strip(); body_start = idx + 1
    lines = lines[body_start:]
    return title, meta, parse_blocks(lines)

CSS = """
body { line-height: 1.7; margin: 0; padding: 0 2%; }
h1 { font-size: 1.5em; line-height: 1.3; margin: 1em 0 0.3em; font-weight: bold; }
h2 { font-size: 1.25em; margin: 1.4em 0 0.5em; }
h3 { font-size: 1.1em; margin: 1.2em 0 0.4em; }
h4, h5, h6 { font-size: 1em; margin: 1em 0 0.3em; }
p { margin: 0 0 0.9em; text-align: justify; }
p.meta { font-size: 0.85em; color: #555; margin-bottom: 0.3em; }
p.meta2 { font-size: 0.85em; color: #555; margin-bottom: 1.4em; }
.figure { text-align: center; margin: 1em 0; page-break-inside: avoid; }
.figure img { max-width: 100%; height: auto; }
.caption { font-size: 0.85em; color: #555; text-align: center; margin: 0.3em 0 1em; }
blockquote { margin: 1em 1.5em; padding-left: 0.8em; border-left: 3px solid #999; color: #333; }
ul, ol { margin: 0 0 1em; padding-left: 1.6em; }
li { margin-bottom: 0.4em; }
li p { margin-bottom: 0.4em; }
hr { border: 0; border-top: 1px solid #bbb; margin: 1.6em 25%; }
a { color: inherit; text-decoration: underline; }
.toc li { margin-bottom: 0.3em; }
.toc .date { font-size: 0.8em; color: #666; margin-right: 0.5em; }
.title-page { text-align: center; margin-top: 30%; }
.title-page h1 { font-size: 2em; }
"""

def kepubify(body_html):
    """Wrap block text in koboSpan spans so Kobo's renderer tracks position/annotations."""
    counter = [0]
    def wrap(m):
        counter[0] += 1
        return f'{m.group(1)}<span class="koboSpan" id="kobo.{counter[0]}.1">{m.group(2)}</span>{m.group(3)}'
    pat = re.compile(r'(<(?:p|h[1-6])\b[^>]*>)(.*?)(</(?:p|h[1-6])>)'
                     r'|(<li>)((?:(?!<(?:ul|ol|li|p)\b).)*?)(</li>)'
                     r'|()(<img\b[^>]*/>)()', re.S)
    def dispatch(m):
        g = [x for x in m.groups()]
        for a in (0, 3, 6):
            if g[a] is not None:
                counter[0] += 1
                return f'{g[a]}<span class="koboSpan" id="kobo.{counter[0]}.1">{g[a+1]}</span>{g[a+2]}'
        return m.group(0)
    return pat.sub(dispatch, body_html)

def xhtml(title, body):
    inner = f'<div id="book-columns"><div id="book-inner">{body}</div></div>' if KEPUB else body
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-TW" lang="zh-TW">\n'
            f'<head><meta charset="utf-8"/><title>{html.escape(title)}</title>'
            '<link rel="stylesheet" type="text/css" href="../style.css"/></head>\n'
            f'<body>{inner}</body></html>\n')

# ---------- chapter ordering ----------
# Same-day series are titled like「人性套利 Ⅰ：…」「複利引擎 II：…」; the site mixes
# Unicode numerals (Ⅰ-Ⅻ, U+2160…) with ASCII ones (I, II, III, IV), and a plain string
# sort puts "II" before "I" (because 'I' < '：') and ASCII before Unicode. Sort by
# (date, series name, numeral value, title) so parts read in order.
_UNI_ROMAN = {chr(0x2160 + i): i + 1 for i in range(12)}
_ASCII_ROMAN = {'I': 1, 'V': 5, 'X': 10, 'L': 50}
SERIES_RE = re.compile(r'^(.*?)(?<![A-Za-z0-9])([IVXL]+|[\u2160-\u216b]+)\s*[：:]')

def roman_value(s):
    if all(ch in _UNI_ROMAN for ch in s):
        return sum(_UNI_ROMAN[ch] for ch in s)
    total, prev = 0, 0
    for ch in reversed(s):
        v = _ASCII_ROMAN[ch]
        total += -v if v < prev else v
        prev = max(prev, v)
    return total

def chapter_key(path):
    name = os.path.basename(path)[:-3]
    date, _, title = name.partition(' ')
    m = SERIES_RE.match(title)
    if m:
        return (date, m.group(1).strip(), roman_value(m.group(2)), title)
    return (date, title, 0, title)

# ---------- build ----------
files = sorted((f for f in glob.glob(os.path.join(ARTICLES, '[0-9]' * 8 + ' *.md'))
                if _a.date_from <= os.path.basename(f)[:8] <= _a.date_to), key=chapter_key)
if not files:
    sys.exit('no articles matched')
chapters = []
for k, f in enumerate(files, 1):
    title, meta, body = load_article(f)
    d = os.path.basename(f)[:8]
    date_str = f'{d[:4]}.{d[4:6]}.{d[6:]}'
    cat = meta.get('分類', '')
    url = meta.get('原文', '')
    head = f'<h1>{inline(title)}</h1>'
    head += f'<p class="meta">{html.escape(cat)}｜{date_str}</p>'
    if url:
        head += f'<p class="meta2">原文：<a href="{attr(url)}">{html.escape(url)}</a></p>'
    content = head + body
    if KEPUB: content = kepubify(content)
    chapters.append(dict(id=f'ch{k:03d}', file=f'text/ch{k:03d}.xhtml', title=title, date=date_str, cat=cat, html=xhtml(title, content)))

# validate well-formedness
for c in chapters:
    try: minidom.parseString(c['html'].encode('utf-8'))
    except Exception as e:
        sys.stderr.write(f"XML error in {c['title']}: {e}\n"); sys.exit(1)

book_title = '曼報 Pro 文章合輯'
first, last = chapters[0]['date'], chapters[-1]['date']
subtitle = f'{first} – {last}，共 {len(chapters)} 篇'
uid = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL, 'https://pro.manny-li.com/collection'))
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

title_body = f'<div class="title-page"><h1>{book_title}</h1><p>{subtitle}</p><p>pro.manny-li.com</p></div>'
if KEPUB: title_body = kepubify(title_body)
title_page = xhtml(book_title, title_body)

# nav (EPUB3) + html toc page
nav_items = ''.join(f'<li><a href="{c["file"]}">{html.escape(c["date"])}　{html.escape(c["title"])}</a></li>' for c in chapters)
nav = ('<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n'
       '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-TW" lang="zh-TW">'
       f'<head><meta charset="utf-8"/><title>目錄</title><link rel="stylesheet" type="text/css" href="style.css"/></head><body>'
       f'<nav epub:type="toc" id="toc"><h1>目錄</h1><ol class="toc">{nav_items}</ol></nav>'
       '<nav epub:type="landmarks" hidden="hidden"><ol>'
       '<li><a epub:type="toc" href="nav.xhtml">目錄</a></li>'
       f'<li><a epub:type="bodymatter" href="{chapters[0]["file"]}">內文</a></li></ol></nav>'
       '</body></html>\n')
minidom.parseString(nav.encode('utf-8'))

# NCX (EPUB2 fallback, Kobo reads it)
navpoints = ''.join(
    f'<navPoint id="np{k}" playOrder="{k}"><navLabel><text>{html.escape(c["date"])} {html.escape(c["title"])}</text></navLabel><content src="{c["file"]}"/></navPoint>'
    for k, c in enumerate(chapters, 1))
ncx = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head>'
       f'<meta name="dtb:uid" content="{uid}"/><meta name="dtb:depth" content="1"/>'
       '<meta name="dtb:totalPageCount" content="0"/><meta name="dtb:maxPageNumber" content="0"/></head>'
       f'<docTitle><text>{html.escape(book_title)}</text></docTitle><navMap>{navpoints}</navMap></ncx>\n')

# images actually referenced
img_items = ''
for k, rel in enumerate(sorted(used_images), 1):
    ext = rel.rsplit('.', 1)[-1].lower()
    mt = 'image/jpeg' if ext in ('jpg', 'jpeg') else 'image/png'
    img_items += f'<item id="img{k}" href="images/{attr(rel)}" media-type="{mt}"/>'

manifest = ('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
            '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
            '<item id="css" href="style.css" media-type="text/css"/>'
            '<item id="titlepage" href="text/title.xhtml" media-type="application/xhtml+xml"/>'
            + ''.join(f'<item id="{c["id"]}" href="{c["file"]}" media-type="application/xhtml+xml"/>' for c in chapters)
            + img_items)
spine = '<itemref idref="titlepage"/><itemref idref="nav"/>' + ''.join(f'<itemref idref="{c["id"]}"/>' for c in chapters)
opf = ('<?xml version="1.0" encoding="utf-8"?>\n'
       '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="zh-TW">'
       '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">'
       f'<dc:identifier id="uid">{uid}</dc:identifier>'
       f'<dc:title>{html.escape(book_title)}</dc:title>'
       '<dc:creator>曼報 Manny Li</dc:creator>'
       '<dc:language>zh-TW</dc:language>'
       f'<dc:description>{html.escape(subtitle)}</dc:description>'
       f'<meta property="dcterms:modified">{now}</meta>'
       '</metadata>'
       f'<manifest>{manifest}</manifest>'
       f'<spine toc="ncx">{spine}</spine></package>\n')
minidom.parseString(opf.encode('utf-8'))

container = ('<?xml version="1.0" encoding="utf-8"?>\n'
             '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">'
             '<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>\n')

os.makedirs(os.path.dirname(OUT) or '.', exist_ok=True)
with zipfile.ZipFile(OUT, 'w') as z:
    z.writestr(zipfile.ZipInfo('mimetype'), 'application/epub+zip', compress_type=zipfile.ZIP_STORED)
    z.writestr('META-INF/container.xml', container, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/content.opf', opf, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/nav.xhtml', nav, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/toc.ncx', ncx, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/style.css', CSS, compress_type=zipfile.ZIP_DEFLATED)
    z.writestr('OEBPS/text/title.xhtml', title_page, compress_type=zipfile.ZIP_DEFLATED)
    for c in chapters:
        z.writestr('OEBPS/' + c['file'], c['html'], compress_type=zipfile.ZIP_DEFLATED)
    for rel in sorted(used_images):
        z.write(os.path.join(IMAGES, rel), 'OEBPS/images/' + rel, compress_type=zipfile.ZIP_STORED)

print(f'wrote {OUT}: {len(chapters)} chapters, {len(used_images)} images, {os.path.getsize(OUT)/1e6:.1f} MB')
