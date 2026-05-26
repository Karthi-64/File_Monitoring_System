# File_Monitoring_System ---> (FolderGuardian) 🛡

A lightweight, cross-platform folder-watcher that pops up a clean alert
whenever a new file lands in your shared folder.

---

## Setup

### 1 — Install dependencies

```bash
pip install watchdog
pip install python-docx   # optional — richer .docx metadata
```

> **Tkinter** ships with standard Python on Windows and macOS.  
> On Linux: `sudo apt install python3-tk`

---

### 2 — Run

```bash
# Watch the default ./watched_folder  (auto-created next to main.py)
python main.py

# Watch a custom folder
python main.py "C:\Users\You\Shared\TeamDocs"
python main.py "/Users/you/shared/team_docs"
```

---

## How it works

| Action | Behaviour |
|--------|-----------|
| New file detected | Popup slides in from the right edge of the screen |
| Click **Allow ✓** | File stays; logged as allowed |
| Click **Deny ✕** | File is moved to `.guardian_quarantine/` inside the watched folder |
| Click **ⓘ** | Expands an inline detail panel (name, path, stats) |
| Click anywhere else | Popup collapses to a slim side-tab |
| Click the side-tab | Popup expands back |
| Click **×** | Dismisses the popup (treated as Allow) |

---

## Supported file types

`.txt` `.docx` `.doc` `.pdf` `.xlsx` `.xls` `.csv`  
`.md` `.rtf` `.odt` `.pptx` `.ppt` `.json` `.xml` `.html`

---

## File structure

```
folder_guardian/
├── main.py        ← entry point + watchdog observer + allow/deny logic
├── popup.py       ← Tkinter popup UI (collapsible, animated)
├── file_info.py   ← metadata extraction per file type
└── README.md
```

---

## Notes

- **One popup at a time** — if multiple files arrive simultaneously they
  are queued and shown sequentially.
- The quarantine folder (`.guardian_quarantine/`) is hidden from the
  watcher, so quarantined files won't re-trigger alerts.
- Temp/partial files (`.tmp`, `.part`, `.crdownload`, etc.) are
  automatically ignored.
