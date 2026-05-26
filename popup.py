# popup.py  ─  FolderGuardian  notification popup (Tkinter)
#
# Design direction: Sharp, modern dark UI — macOS-native feel
# with a frosted-glass card aesthetic. Clean typography,
# precise spacing, subtle animations. Nothing Intel-update about it.

import tkinter as tk
from tkinter import font as tkfont
from pathlib import Path
from file_info import get_file_info, get_folder_summary, FILE_TYPES

# ── Palette ─────────────────────────────────────────────────────
C = {
    # Backgrounds
    'bg':           '#0F0F13',      # near-black base
    'card':         '#17171F',      # card surface
    'card_border':  '#2C2C3E',      # subtle border
    'section':      '#1C1C26',      # inner section bg
    'detail_bg':    '#13131A',      # detail panel bg
    'input_bg':     '#1F1F2B',      # chip / tag bg

    # Text
    'text_primary': '#F0F0F8',      # main text
    'text_secondary':'#9898B8',     # muted / labels
    'text_dim':     '#55556A',      # very muted

    # Accents
    'accent':       '#6B6BF5',      # indigo
    'accent_glow':  '#4A4ABF',      # darker indigo

    # Actions
    'allow':        '#1A8A55',      # deep green
    'allow_hover':  '#22A866',      # green hover
    'allow_text':   '#D4F5E3',
    'deny':         '#8A1A2A',      # deep red
    'deny_hover':   '#B02235',      # red hover
    'deny_text':    '#F5D4D8',

    # Misc
    'divider':      '#22222E',
    'tab_accent':   '#6B6BF5',
    'tag_border':   '#2E2E42',
    'warning':      '#E5A228',
}

POPUP_W   = 340
POPUP_H   = 360
TAB_W     = 30
ANIM_STEP = 22
ANIM_MS   = 8


class GuardianPopup:
    def __init__(self, filepath: str, folder: str, on_allow, on_deny):
        self.filepath      = filepath
        self.folder        = folder
        self.on_allow      = on_allow
        self.on_deny       = on_deny
        self._collapsed    = False
        self._detail_open  = False

        self.info    = get_file_info(filepath)
        self.summary = get_folder_summary(folder, exclude_path=filepath)

        self._build()
        self._slide_in()

    # ── Window ──────────────────────────────────────────────────
    def _build(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg=C['bg'])
        self.root.resizable(False, False)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self._sw, self._sh = sw, sh
        self._full_x  = sw - POPUP_W - 16
        self._tab_x   = sw - TAB_W - 2
        self._y       = sh - POPUP_H - 52
        self._cur_x   = sw + 20

        self.root.geometry(f"{POPUP_W}x{POPUP_H}+{self._cur_x}+{self._y}")
        self._build_ui()
        self._bind_focus()

    # ── Full UI ─────────────────────────────────────────────────
    def _build_ui(self):
        # Outer container with border simulation
        outer = tk.Frame(self.root, bg=C['card_border'], padx=1, pady=1)
        outer.pack(fill='both', expand=True)

        self.frame = tk.Frame(outer, bg=C['card'])
        self.frame.pack(fill='both', expand=True)

        self._build_header()
        self._build_file_row()
        self._build_detail_panel()   # hidden initially
        self._build_folder_row()
        self._build_actions()

    # ── Header ──────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self.frame, bg=C['card'], padx=16, pady=12)
        hdr.pack(fill='x')

        left = tk.Frame(hdr, bg=C['card'])
        left.pack(side='left', fill='both', expand=True)

        # Brand row
        brand = tk.Frame(left, bg=C['card'])
        brand.pack(anchor='w')

        tk.Label(brand, text='●', fg=C['accent'], bg=C['card'],
                 font=('Helvetica Neue', 9)).pack(side='left', padx=(0, 5))
        tk.Label(brand, text='FolderGuardian',
                 fg=C['text_primary'], bg=C['card'],
                 font=('Helvetica Neue', 11, 'bold')).pack(side='left')

        tk.Label(left, text='New file is requesting entry',
                 fg=C['text_secondary'], bg=C['card'],
                 font=('Helvetica Neue', 9)).pack(anchor='w', pady=(2, 0))

        # Close button
        close = tk.Label(hdr, text='✕', fg=C['text_dim'], bg=C['card'],
                         font=('Helvetica Neue', 12), cursor='hand2')
        close.pack(side='right', anchor='n')
        close.bind('<Button-1>', lambda e: self._dismiss())
        close.bind('<Enter>',    lambda e: close.config(fg=C['text_primary']))
        close.bind('<Leave>',    lambda e: close.config(fg=C['text_dim']))

        # Thin accent line under header
        tk.Frame(self.frame, bg=C['divider'], height=1).pack(fill='x')

    # ── File row ────────────────────────────────────────────────
    def _build_file_row(self):
        sec = tk.Frame(self.frame, bg=C['card'], padx=16, pady=12)
        sec.pack(fill='x')

        # Label
        tk.Label(sec, text='INCOMING FILE', fg=C['text_dim'], bg=C['card'],
                 font=('Helvetica Neue', 7, 'bold')).pack(anchor='w')

        row = tk.Frame(sec, bg=C['card'])
        row.pack(fill='x', pady=(7, 0))

        # Icon block
        icon_box = tk.Frame(row, bg=C['input_bg'], width=40, height=40)
        icon_box.pack(side='left', padx=(0, 12))
        icon_box.pack_propagate(False)
        tk.Label(icon_box, text=self.info['icon'], bg=C['input_bg'],
                 fg=C['text_primary'],
                 font=('Helvetica Neue', 18)).place(relx=.5, rely=.5, anchor='center')

        # Name + chips
        meta = tk.Frame(row, bg=C['card'])
        meta.pack(side='left', fill='both', expand=True)

        name = self.info['name']
        if len(name) > 28: name = name[:25] + '…'
        tk.Label(meta, text=name, fg=C['text_primary'], bg=C['card'],
                 font=('Helvetica Neue', 10, 'bold'),
                 anchor='w').pack(fill='x')

        chips = tk.Frame(meta, bg=C['card'])
        chips.pack(anchor='w', pady=(3, 0))
        self._chip(chips, self.info['type'])
        self._chip(chips, self.info['size'], accent=True)

        # Info button — right side
        info_btn = tk.Label(row, text='  ⓘ  ', fg=C['accent'],
                            bg=C['input_bg'],
                            font=('Helvetica Neue', 9),
                            cursor='hand2', padx=2, pady=3)
        info_btn.pack(side='right', anchor='center')
        info_btn.bind('<Button-1>', lambda e: self._toggle_detail())
        info_btn.bind('<Enter>',    lambda e: info_btn.config(bg=C['accent'], fg='white'))
        info_btn.bind('<Leave>',    lambda e: info_btn.config(bg=C['input_bg'], fg=C['accent']))

        tk.Frame(self.frame, bg=C['divider'], height=1).pack(fill='x')

    # ── Detail panel (hidden until ⓘ clicked) ───────────────────
    def _build_detail_panel(self):
        self._detail_frame = tk.Frame(self.frame, bg=C['detail_bg'],
                                      padx=16, pady=10)
        # Not packed yet

    def _populate_detail(self):
        for w in self._detail_frame.winfo_children():
            w.destroy()

        tk.Label(self._detail_frame, text='FILE DETAILS',
                 fg=C['text_dim'], bg=C['detail_bg'],
                 font=('Helvetica Neue', 7, 'bold')).pack(anchor='w', pady=(0, 5))

        rows = [
            ('Name',     self.info['name']),
            ('Path',     self._truncate(self.info['path'], 36)),
            ('Modified', self.info['modified']),
        ]
        for k, v in rows:
            self._detail_row(k, v)
        for k, v in self.info['extra'].items():
            self._detail_row(k, v)

        tk.Frame(self.frame, bg=C['divider'], height=1).pack(fill='x')

    def _detail_row(self, key, val):
        row = tk.Frame(self._detail_frame, bg=C['detail_bg'])
        row.pack(fill='x', pady=2)
        tk.Label(row, text=key, fg=C['text_secondary'], bg=C['detail_bg'],
                 font=('Helvetica Neue', 8), width=9, anchor='w').pack(side='left')
        tk.Label(row, text=val, fg=C['text_primary'], bg=C['detail_bg'],
                 font=('Helvetica Neue', 8), anchor='w').pack(side='left')

    def _toggle_detail(self):
        if self._detail_open:
            self._detail_frame.pack_forget()
            # Remove extra divider if packed
            self._detail_open = False
            self.root.geometry(f"{POPUP_W}x{POPUP_H}+{self._full_x}+{self._y}")
        else:
            self._populate_detail()
            # Pack after file row divider (index ~3 in frame children)
            self._detail_frame.pack(fill='x', before=self.frame.winfo_children()[4])
            self._detail_open = True
            extra = max(60, len(self.info['extra']) * 22 + 60)
            new_h = POPUP_H + extra
            new_y = max(8, self._sh - new_h - 52)
            self.root.geometry(f"{POPUP_W}x{new_h}+{self._full_x}+{new_y}")

    # ── Folder summary row ──────────────────────────────────────
    def _build_folder_row(self):
        sec = tk.Frame(self.frame, bg=C['card'], padx=16, pady=11)
        sec.pack(fill='x')

        tk.Label(sec, text='FOLDER CONTENTS', fg=C['text_dim'], bg=C['card'],
                 font=('Helvetica Neue', 7, 'bold')).pack(anchor='w')

        total    = self.summary['total']
        by_type  = self.summary['by_type']
        count_lbl = f"{total} existing file{'s' if total != 1 else ''}"

        tk.Label(sec, text=count_lbl, fg=C['text_primary'], bg=C['card'],
                 font=('Helvetica Neue', 9, 'bold')).pack(anchor='w', pady=(5, 3))

        if by_type:
            wrap = tk.Frame(sec, bg=C['card'])
            wrap.pack(anchor='w')
            for ext, cnt in list(by_type.items())[:5]:
                _, icon = FILE_TYPES.get(ext, ('', '📄'))
                self._chip(wrap, f"{icon} {ext}  {cnt}", small=True)
            if len(by_type) > 5:
                self._chip(wrap, f"+{len(by_type)-5} more", small=True, dim=True)
        else:
            tk.Label(sec, text='Folder is empty', fg=C['text_dim'], bg=C['card'],
                     font=('Helvetica Neue', 8)).pack(anchor='w')

        tk.Frame(self.frame, bg=C['divider'], height=1).pack(fill='x')

    # ── Action buttons ──────────────────────────────────────────
    def _build_actions(self):
        bar = tk.Frame(self.frame, bg=C['card'], padx=12, pady=11)
        bar.pack(fill='x', side='bottom')

        deny_btn = tk.Label(
            bar, text='✕  Deny',
            bg=C['deny'], fg=C['deny_text'],
            font=('Helvetica Neue', 9, 'bold'),
            padx=0, pady=8, cursor='hand2', anchor='center')
        deny_btn.pack(side='left', expand=True, fill='x', padx=(0, 5))
        deny_btn.bind('<Button-1>', lambda e: self._do_deny())
        deny_btn.bind('<Enter>', lambda e: deny_btn.config(bg=C['deny_hover']))
        deny_btn.bind('<Leave>', lambda e: deny_btn.config(bg=C['deny']))

        allow_btn = tk.Label(
            bar, text='✓  Allow',
            bg=C['allow'], fg=C['allow_text'],
            font=('Helvetica Neue', 9, 'bold'),
            padx=0, pady=8, cursor='hand2', anchor='center')
        allow_btn.pack(side='right', expand=True, fill='x', padx=(5, 0))
        allow_btn.bind('<Button-1>', lambda e: self._do_allow())
        allow_btn.bind('<Enter>', lambda e: allow_btn.config(bg=C['allow_hover']))
        allow_btn.bind('<Leave>', lambda e: allow_btn.config(bg=C['allow']))

    # ── Chip ────────────────────────────────────────────────────
    def _chip(self, parent, text, small=False, accent=False, dim=False):
        size = 7 if small else 8
        fg   = C['text_dim'] if dim else (C['accent'] if accent else C['text_secondary'])
        bg   = C['input_bg']
        tk.Label(parent, text=text, bg=bg, fg=fg,
                 font=('Helvetica Neue', size),
                 padx=7, pady=2,
                 relief='flat').pack(side='left', padx=(0, 4), pady=1)

    # ── Collapse / Tab ──────────────────────────────────────────
    def _bind_focus(self):
        self.root.bind('<FocusOut>', self._on_focus_out)
        self.root.bind('<FocusIn>',  self._on_focus_in)

    def _on_focus_out(self, _):
        if not self._collapsed:
            self._collapse()

    def _on_focus_in(self, _):
        if self._collapsed:
            self._expand()

    def _collapse(self):
        self._collapsed = True
        self.frame.pack_forget()
        self._build_tab()
        self.root.geometry(f"{TAB_W}x{64}+{self._tab_x}+{self._y}")

    def _expand(self):
        if hasattr(self, '_tab_frame'):
            self._tab_frame.destroy()
        self._collapsed = False
        self.frame.pack(fill='both', expand=True)
        h = POPUP_H
        if self._detail_open:
            extra = max(60, len(self.info['extra']) * 22 + 60)
            h += extra
        self.root.geometry(f"{POPUP_W}x{h}+{self._full_x}+{self._y}")
        self.root.focus_force()

    def _build_tab(self):
        self._tab_frame = tk.Frame(self.root, bg=C['tab_accent'],
                                   width=TAB_W, cursor='hand2')
        self._tab_frame.pack(fill='both', expand=True)
        self._tab_frame.bind('<Button-1>', lambda e: self._expand())

        c = tk.Canvas(self._tab_frame, bg=C['tab_accent'],
                      width=TAB_W, height=64, highlightthickness=0)
        c.pack()
        c.create_text(TAB_W // 2, 32, text='🛡',
                      font=('Helvetica Neue', 13),
                      fill='white', anchor='center')
        c.bind('<Button-1>', lambda e: self._expand())

    # ── Slide-in ────────────────────────────────────────────────
    def _slide_in(self):
        if self._cur_x > self._full_x:
            self._cur_x = max(self._full_x, self._cur_x - ANIM_STEP)
            self.root.geometry(f"{POPUP_W}x{POPUP_H}+{self._cur_x}+{self._y}")
            self.root.after(ANIM_MS, self._slide_in)
        else:
            self.root.focus_force()

    # ── Actions ─────────────────────────────────────────────────
    def _do_allow(self):
        self._dismiss()
        self.on_allow(self.filepath)

    def _do_deny(self):
        self._dismiss()
        self.on_deny(self.filepath)

    def _dismiss(self):
        self.root.destroy()

    @staticmethod
    def _truncate(s, n):
        return s if len(s) <= n else '…' + s[-(n-1):]

    def run(self):
        self.root.mainloop()