# file_info.py  ─  metadata extraction for FolderGuardian

from pathlib import Path
from datetime import datetime

# ── Optional rich-format support ────────────────────────────────
_DOCX = False
try:
    from docx import Document as _DocxDoc
    _DOCX = True
except ImportError:
    pass

# ── Type registry ────────────────────────────────────────────────
FILE_TYPES: dict[str, tuple[str, str]] = {
    '.txt':  ('Text File',             '📄'),
    '.docx': ('Word Document',         '📝'),
    '.doc':  ('Word Doc (Legacy)',     '📝'),
    '.pdf':  ('PDF Document',          '📕'),
    '.xlsx': ('Excel Spreadsheet',     '📊'),
    '.xls':  ('Excel (Legacy)',        '📊'),
    '.csv':  ('CSV File',              '📋'),
    '.md':   ('Markdown File',         '📄'),
    '.rtf':  ('Rich Text File',        '📄'),
    '.odt':  ('OpenDocument Text',     '📄'),
    '.pptx': ('PowerPoint',            '🗂'),
    '.ppt':  ('PowerPoint (Legacy)',   '🗂'),
    '.json': ('JSON File',             '📄'),
    '.xml':  ('XML File',              '📄'),
    '.html': ('HTML File',             '🌐'),
}

MONITORED_EXTENSIONS = frozenset(FILE_TYPES.keys())


def fmt_size(n: int) -> str:
    if n < 1_024:        return f"{n} B"
    if n < 1_048_576:    return f"{n / 1_024:.1f} KB"
    return f"{n / 1_048_576:.1f} MB"


def get_file_info(filepath: str) -> dict:
    """Return a dict of metadata for the given file path."""
    path = Path(filepath)
    ext  = path.suffix.lower()
    stat = path.stat()

    ftype, icon = FILE_TYPES.get(ext, (f"{ext.upper()} File" if ext else "File", "📄"))

    info = {
        'name':     path.name,
        'ext':      ext,
        'type':     ftype,
        'icon':     icon,
        'size':     fmt_size(stat.st_size),
        'size_raw': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%b %d, %Y  %H:%M'),
        'path':     str(path.resolve()),
        'extra':    {},
    }

    # ── Per-format enrichment ────────────────────────────────────
    try:
        if ext == '.txt':
            text = path.read_text(encoding='utf-8', errors='ignore')
            info['extra'] = {
                'Lines':      f"{len(text.splitlines()):,}",
                'Words':      f"{len(text.split()):,}",
                'Characters': f"{len(text):,}",
            }
        elif ext == '.csv':
            lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
            cols  = len(lines[0].split(',')) if lines else 0
            info['extra'] = {
                'Rows':    f"{max(0, len(lines) - 1):,}",
                'Columns': str(cols),
            }
        elif ext == '.docx' and _DOCX:
            doc   = _DocxDoc(filepath)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            words = sum(len(p.split()) for p in paras)
            info['extra'] = {
                'Paragraphs': str(len(paras)),
                'Words':      f"{words:,}",
            }
        elif ext == '.md':
            text = path.read_text(encoding='utf-8', errors='ignore')
            headings = [l for l in text.splitlines() if l.startswith('#')]
            info['extra'] = {
                'Lines':    f"{len(text.splitlines()):,}",
                'Words':    f"{len(text.split()):,}",
                'Headings': str(len(headings)),
            }
    except Exception:
        pass   # enrichment is best-effort

    return info


def get_folder_summary(folder: str, exclude_path: str | None = None) -> dict:
    """Count existing files in *folder* grouped by extension."""
    exclude = str(Path(exclude_path).resolve()) if exclude_path else None
    counts: dict[str, int] = {}
    total = 0

    for f in Path(folder).iterdir():
        if not f.is_file():
            continue
        if exclude and str(f.resolve()) == exclude:
            continue
        ext = f.suffix.lower() or '.other'
        counts[ext] = counts.get(ext, 0) + 1
        total += 1

    # Sort by count descending
    counts = dict(sorted(counts.items(), key=lambda kv: kv[1], reverse=True))
    return {'total': total, 'by_type': counts}
