# main.py  ─  FolderGuardian  entry point
#
# Usage
# ─────
#   python main.py                       # watches ./watched_folder (auto-created)
#   python main.py /path/to/your/folder
#
# Requirements
# ────────────
#   pip install watchdog
#   pip install python-docx   (optional – richer .docx metadata)

import sys
import os
import shutil
import threading
import queue
import time
import logging
from pathlib import Path

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from file_info import MONITORED_EXTENSIONS
from popup import GuardianPopup

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s  %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('FolderGuardian')

# ── Quarantine folder (files go here on Deny if no origin known) ─
QUARANTINE_SUBDIR = '.guardian_quarantine'

# ── macOS / system files to always ignore ───────────────────────
IGNORED_NAMES = {
    '.DS_Store', '.DS_Store?', '._DS_Store',
    'Thumbs.db', 'desktop.ini',        # Windows equivalents
    '.localized', '.Spotlight-V100',
    '.fseventsd', '.Trashes',
}


# ═══════════════════════════════════════════════════════════════
#  Allow / Deny callbacks
# ═══════════════════════════════════════════════════════════════

def handle_allow(filepath: str):
    log.info(f"✓ ALLOWED  →  {Path(filepath).name}")


def handle_deny(filepath: str, folder: str, origin: str | None = None):
    """
    Deny logic:
      • If we know where the file came from (drag-move), send it back there.
      • If the file was copied in (no known origin), quarantine it.
    """
    src = Path(filepath)

    # ── Case 1: origin known → restore to original location ──────
    if origin:
        origin_path = Path(origin)
        # If original file now exists at origin (shouldn't, but safety check),
        # rename destination to avoid collision
        dest = origin_path
        if dest.exists():
            ts   = int(time.time())
            dest = origin_path.parent / f"{origin_path.stem}_{ts}{origin_path.suffix}"
        try:
            shutil.move(str(src), str(dest))
            log.info(f"✕ DENIED   →  {src.name}  (returned to {dest.parent})")
            return
        except Exception as e:
            log.warning(f"Could not return {src.name} to origin ({e}), quarantining instead.")

    # ── Case 2: no origin (file was copied) → quarantine ─────────
    quarantine = Path(folder) / QUARANTINE_SUBDIR
    quarantine.mkdir(exist_ok=True)

    dest = quarantine / src.name
    if dest.exists():
        ts   = int(time.time())
        dest = quarantine / f"{src.stem}_{ts}{src.suffix}"

    try:
        shutil.move(str(src), str(dest))
        log.info(f"✕ DENIED   →  {src.name}  (moved to quarantine — no origin known)")
    except Exception as e:
        log.warning(f"Could not quarantine {src.name}: {e}")


# ═══════════════════════════════════════════════════════════════
#  File-system event handler
# ═══════════════════════════════════════════════════════════════

class FolderHandler(FileSystemEventHandler):
    """
    Watches a single flat folder (non-recursive).
    Tracks origin path for moved files so Deny can restore them.
    Ignores macOS system files, quarantine dir, and temp files.
    """

    TEMP_SUFFIXES = {'.tmp', '.part', '.crdownload', '.download',
                     '.swp', '.lock', '~'}

    def __init__(self, folder: str, file_queue: queue.Queue):
        super().__init__()
        self.folder     = str(Path(folder).resolve())
        self.file_queue = file_queue
        self._seen: set[str] = set()
        # Maps resolved dest_path → original src_path for moved files
        self._origins: dict[str, str] = {}

    def _is_relevant(self, path_str: str) -> bool:
        p   = Path(path_str)
        ext = p.suffix.lower()

        # Must be directly inside the watched folder
        if str(p.parent.resolve()) != self.folder:
            return False

        # Ignore quarantine subfolder
        if QUARANTINE_SUBDIR in p.parts:
            return False

        # Ignore macOS / OS system files by name
        if p.name in IGNORED_NAMES or p.name.startswith('._'):
            return False

        # Must match a monitored extension
        if ext not in MONITORED_EXTENSIONS:
            return False

        # Ignore temp / partial files
        if ext in self.TEMP_SUFFIXES or p.name.startswith('~'):
            return False

        return True

    def _enqueue(self, dest_str: str, origin_str: str | None = None):
        resolved = str(Path(dest_str).resolve())
        if resolved in self._seen:
            return
        self._seen.add(resolved)

        if origin_str:
            self._origins[resolved] = origin_str

        def _delayed():
            time.sleep(0.4)
            if Path(resolved).exists():
                origin = self._origins.get(resolved)        # may be None
                self.file_queue.put((resolved, origin))
                log.info(f"Queued  →  {Path(resolved).name}"
                         + (f"  (from {Path(origin).parent})" if origin else "  (copied in)"))

        threading.Thread(target=_delayed, daemon=True).start()

    def on_created(self, event):
        """File copied/created inside the folder — no known origin."""
        if not event.is_directory and self._is_relevant(event.src_path):
            self._enqueue(event.src_path, origin_str=None)

    def on_moved(self, event):
        """File dragged/moved into the folder — origin is event.src_path."""
        if not event.is_directory and self._is_relevant(event.dest_path):
            self._enqueue(event.dest_path, origin_str=event.src_path)


# ═══════════════════════════════════════════════════════════════
#  Popup dispatcher  (runs on main thread for Tkinter safety)
# ═══════════════════════════════════════════════════════════════

def dispatch_popups(file_queue: queue.Queue, folder: str):
    log.info("Dispatcher ready — waiting for incoming files …\n")

    while True:
        try:
            item = file_queue.get(timeout=1)
        except queue.Empty:
            continue

        filepath, origin = item

        if not Path(filepath).exists():
            log.warning(f"File vanished before popup: {filepath}")
            file_queue.task_done()
            continue

        log.info(f"Showing popup for  →  {Path(filepath).name}")

        try:
            popup = GuardianPopup(
                filepath = filepath,
                folder   = folder,
                on_allow = handle_allow,
                on_deny  = lambda fp, orig=origin, f=folder: handle_deny(fp, f, orig),
            )
            popup.run()
        except Exception as e:
            log.error(f"Popup error: {e}")

        file_queue.task_done()


# ═══════════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'watched_folder')

    folder_path = Path(folder)
    folder_path.mkdir(parents=True, exist_ok=True)
    folder = str(folder_path.resolve())

    log.info(f"FolderGuardian  🛡")
    log.info(f"Watching  →  {folder}")
    log.info("Drop a supported file into the folder to test.\n")

    file_queue: queue.Queue = queue.Queue()
    handler    = FolderHandler(folder, file_queue)
    observer   = Observer()
    observer.schedule(handler, folder, recursive=False)
    observer.start()

    try:
        dispatch_popups(file_queue, folder)
    except KeyboardInterrupt:
        log.info("\nStopping …")
    finally:
        observer.stop()
        observer.join()
        log.info("FolderGuardian stopped. Goodbye.")


if __name__ == '__main__':
    main()