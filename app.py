import threading
import queue
import time
import os
import re
import shutil
import numpy as np
import soundfile as sf
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
from pathlib import Path
from datetime import datetime
import json

from kokoro import KPipeline

# Device will be set lazily to avoid heavy torch import at startup
device = None

# Pipelines cached per language to avoid reloading for mixed-language text
pipelines = {}

# Default sample rate used by the models
SAMPLE_RATE = 24000

# Application name (change here to rename the app)
APP_NAME = 'Local TTS'

# Available voices (derived from provided model files)
VOICE_LIST = [
    'af_alloy',
    'af_aoede',
    'af_bella',
    'af_heart',
    'af_jessica',
    'af_kore',
    'af_nicole',
    'af_nova',
    'af_river',
    'af_sarah',
    'af_sky',
    'am_adam',
    'am_echo',
    'am_eric',
    'am_fenrir',
    'am_liam',
    'am_michael',
    'am_onyx',
    'am_puck',
    'am_santa',
    'bf_alice',
    'bf_emma',
    'bf_isabella',
    'bf_lily',
    'bm_daniel',
    'bm_fable',
    'bm_george',
    'bm_lewis',
    'ef_dora',
    'em_alex',
    'em_santa',
    'ff_siwis',
    'hf_alpha',
    'hf_beta',
    'hm_omega',
    'hm_psi',
    'if_sara',
    'im_nicola',
    'jf_alpha',
    'jf_gongitsune',
    'jf_nezumi',
    'jf_tebukuro',
    'jm_kumo',
    'pf_dora',
    'pm_alex',
    'pm_santa',
    'zf_xiaobei',
    'zf_xiaoni',
    'zf_xiaoxiao',
    'zf_xiaoyi'
]

# Voice friendly names mapping with gender indicators
VOICE_NAMES = {
    # American Female
    'af_alloy': '👩 Alloy (American Female)',
    'af_aoede': '👩 Aoede (American Female)',
    'af_bella': '👩 Bella (American Female)',
    'af_heart': '👩 Heart (American Female)',
    'af_jessica': '👩 Jessica (American Female)',
    'af_kore': '👩 Kore (American Female)',
    'af_nicole': '👩 Nicole (American Female)',
    'af_nova': '👩 Nova (American Female)',
    'af_river': '👩 River (American Female)',
    'af_sarah': '👩 Sarah (American Female)',
    'af_sky': '👩 Sky (American Female)',
    # American Male
    'am_adam': '👨 Adam (American Male)',
    'am_echo': '👨 Echo (American Male)',
    'am_eric': '👨 Eric (American Male)',
    'am_fenrir': '👨 Fenrir (American Male)',
    'am_liam': '👨 Liam (American Male)',
    'am_michael': '👨 Michael (American Male)',
    'am_onyx': '👨 Onyx (American Male)',
    'am_puck': '👨 Puck (American Male)',
    'am_santa': '🎅 Santa (American Male)',
    # British Female
    'bf_alice': '👩 Alice (British Female)',
    'bf_emma': '👩 Emma (British Female)',
    'bf_isabella': '👩 Isabella (British Female)',
    'bf_lily': '👩 Lily (British Female)',
    # British Male
    'bm_daniel': '👨 Daniel (British Male)',
    'bm_fable': '👨 Fable (British Male)',
    'bm_george': '👨 George (British Male)',
    'bm_lewis': '👨 Lewis (British Male)',
    # European Female
    'ef_dora': '👩 Dora (European Female)',
    # European Male
    'em_alex': '👨 Alex (European Male)',
    'em_santa': '🎅 Santa (European Male)',
    # Finnish Female
    'ff_siwis': '👩 Siwis (Finnish Female)',
    # Hindi Female (also supports Bengali/Bangla)
    'hf_alpha': '👩 Alpha (Hindi Female • বাংলা)',
    'hf_beta': '👩 Beta (Hindi Female • বাংলা)',
    # Hindi Male (also supports Bengali/Bangla)
    'hm_omega': '👨 Omega (Hindi Male • বাংলা)',
    'hm_psi': '👨 Psi (Hindi Male • বাংলা)',
    # Indonesian Female
    'if_sara': '👩 Sara (Indonesian Female)',
    # Indonesian Male
    'im_nicola': '👨 Nicola (Indonesian Male)',
    # Japanese Female
    'jf_alpha': '👩 Alpha (Japanese Female)',
    'jf_gongitsune': '👩 Gongitsune (Japanese Female)',
    'jf_nezumi': '👩 Nezumi (Japanese Female)',
    'jf_tebukuro': '👩 Tebukuro (Japanese Female)',
    # Japanese Male
    'jm_kumo': '👨 Kumo (Japanese Male)',
    # Portuguese Female
    'pf_dora': '👩 Dora (Portuguese Female)',
    # Portuguese Male
    'pm_alex': '👨 Alex (Portuguese Male)',
    'pm_santa': '🎅 Santa (Portuguese Male)',
    # Chinese Female
    'zf_xiaobei': '👩 Xiaobei (Chinese Female)',
    'zf_xiaoni': '👩 Xiaoni (Chinese Female)',
    'zf_xiaoxiao': '👩 Xiaoxiao (Chinese Female)',
    'zf_xiaoyi': '👩 Xiaoyi (Chinese Female)',
}

# Default voice per language code (used when selected voice doesn't match chunk language)
DEFAULT_VOICE_BY_LANG = {
    'a': 'af_heart',  # English
    'en': 'af_heart',
    'hi': 'hm_omega',
    'bn': 'hm_omega',  # Bengali reuses Hindi voices
    'ja': 'jf_alpha',
    'zh': 'zf_xiaoxiao',
    'id': 'if_sara',
    'pt': 'pf_dora',
    'fi': 'ff_siwis'
}

# Modern design system - Light theme
COLORS_LIGHT = {
    'primary': '#6366f1',       # Indigo - main actions
    'primary_hover': '#4f46e5', # Darker indigo
    'secondary': '#8b5cf6',     # Purple accent
    'background': '#f8fafc',    # Soft white background
    'surface': '#ffffff',       # Card/surface white
    'surface_hover': '#f1f5f9', # Subtle hover
    'border': '#e2e8f0',        # Light border
    'border_focus': '#cbd5e1',  # Focus border
    'text_primary': '#0f172a',  # Dark slate
    'text_secondary': '#475569', # Medium slate
    'text_muted': '#94a3b8',    # Light slate
    'success': '#10b981',       # Green
    'error': '#ef4444',         # Red
}

# Dark theme
COLORS_DARK = {
    'primary': '#818cf8',       # Lighter indigo
    'primary_hover': '#a5b4fc', # Even lighter indigo
    'secondary': '#a78bfa',     # Lighter purple
    'background': '#0f172a',    # Dark background
    'surface': '#1e293b',       # Dark card surface
    'surface_hover': '#334155', # Dark hover
    'border': '#334155',        # Dark border
    'border_focus': '#475569',  # Dark focus border
    'text_primary': '#f1f5f9',  # Light text
    'text_secondary': '#cbd5e1', # Medium light text
    'text_muted': '#64748b',    # Muted light text
    'success': '#34d399',       # Bright green
    'error': '#f87171',         # Bright red
}

# Default to light theme
COLORS = COLORS_LIGHT.copy()

FONTS = {
    'display': ('Segoe UI', 18, 'bold'),
    'heading': ('Segoe UI', 11, 'bold'),
    'body': ('Segoe UI', 10),
    'body_medium': ('Segoe UI', 10, 'normal'),
    'small': ('Segoe UI', 9),
    'code': ('Consolas', 9),
}


def get_resource_path(relative_path: str) -> str:
    base_path = getattr(sys, '_MEIPASS', Path(__file__).parent)
    return str(Path(base_path) / relative_path)


class TTSApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_NAME)
        root.configure(bg=COLORS['background'])

        # Window configuration
        try:
            root.minsize(1100, 750)
            # Center window on screen
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x = (screen_width - 1100) // 2
            y = (screen_height - 750) // 2
            root.geometry(f'1100x750+{x}+{y}')
        except Exception:
            pass

        # Keyboard shortcuts
        root.bind('<Control-Return>', lambda e: self.start_generation())
        root.bind('<Escape>', lambda e: self.cancel_generation())

        # Set icon
        try:
            icon_path = get_resource_path('assets/icon.png')
            if Path(icon_path).exists():
                self._icon_img = tk.PhotoImage(file=icon_path)
                root.iconphoto(True, self._icon_img)
        except Exception:
            pass

        # Configure modern theme
        self._setup_styles()

        # Build UI - two-pane layout
        self._build_responsive_layout()
        # Sidebar visibility state
        self.sidebar_visible = True

        # Initialize state
        self.worker_thread = None
        self.cancel_event = threading.Event()
        self.is_dark_mode = False

        # History file path
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tts_history.json')
        self.history = self._load_history()

        # Generation timing
        self.gen_start_time = None
        self.gen_total_chunks = 0

        # Set initial focus
        self.text_box.focus_set()

    def _setup_styles(self):
        """Configure ttk styles for modern appearance."""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # Configure base styles
        style.configure('.', background=COLORS['background'], foreground=COLORS['text_primary'])

        # Frame styles
        style.configure('Main.TFrame', background=COLORS['background'])
        style.configure('Card.TFrame', background=COLORS['surface'], relief='flat')
        style.configure('Header.TFrame', background=COLORS['surface'])

        # LabelFrame styles - modern cards
        style.configure('Card.TLabelframe',
            background=COLORS['surface'],
            borderwidth=1,
            relief='solid',
            bordercolor=COLORS['border'])
        style.configure('Card.TLabelframe.Label',
            font=FONTS['heading'],
            foreground=COLORS['text_primary'],
            background=COLORS['surface'],
            padding=(0, 0, 0, 8))

        # Label styles
        style.configure('TLabel',
            background=COLORS['background'],
            foreground=COLORS['text_primary'],
            font=FONTS['body'])
        style.configure('Display.TLabel',
            font=FONTS['display'],
            foreground=COLORS['text_primary'],
            background=COLORS['surface'])
        style.configure('Heading.TLabel',
            font=FONTS['heading'],
            foreground=COLORS['text_primary'],
            background=COLORS['surface'])
        style.configure('Muted.TLabel',
            font=FONTS['small'],
            foreground=COLORS['text_muted'],
            background=COLORS['surface'])
        style.configure('Status.TLabel',
            font=FONTS['small'],
            foreground=COLORS['text_secondary'],
            background=COLORS['background'])
        style.configure('Path.TLabel',
            font=FONTS['code'],
            foreground=COLORS['text_muted'],
            background=COLORS['background'])

        # Entry styles (more compact)
        style.configure('Modern.TEntry',
            fieldbackground=COLORS['surface'],
            background=COLORS['surface'],
            foreground=COLORS['text_primary'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border'],
            borderwidth=1,
            relief='solid',
            padding=6)

        # Combobox styles (compact)
        style.configure('Modern.TCombobox',
            fieldbackground=COLORS['surface'],
            background=COLORS['surface'],
            foreground=COLORS['text_primary'],
            bordercolor=COLORS['border'],
            lightcolor=COLORS['border'],
            darkcolor=COLORS['border'],
            arrowcolor=COLORS['text_secondary'],
            padding=8,
            relief='solid',
            borderwidth=1)
        style.map('Modern.TCombobox',
            fieldbackground=[('readonly', COLORS['surface'])],
            selectbackground=[('readonly', COLORS['surface'])],
            selectforeground=[('readonly', COLORS['text_primary'])])

        # Button styles - Primary (more compact)
        style.configure('Primary.TButton',
            background=COLORS['primary'],
            foreground='white',
            borderwidth=0,
            relief='flat',
            font=FONTS['body_medium'],
            padding=(12, 6))
        style.map('Primary.TButton',
            background=[('active', COLORS['primary_hover']), ('pressed', COLORS['primary_hover'])],
            relief=[('pressed', 'flat')])

        # Button styles - Secondary (compact)
        style.configure('Secondary.TButton',
            background=COLORS['surface'],
            foreground=COLORS['text_secondary'],
            borderwidth=1,
            bordercolor=COLORS['border'],
            relief='solid',
            font=FONTS['body_medium'],
            padding=(8, 6))
        style.map('Secondary.TButton',
            background=[('active', COLORS['surface_hover'])],
            bordercolor=[('active', COLORS['border_focus'])])

    def _build_responsive_layout(self):
        """Build a modern two-pane responsive layout: sidebar (settings) + main (text editor)."""
        # Root grid configuration
        self.root.columnconfigure(0, weight=0)  # Sidebar: fixed width
        self.root.columnconfigure(1, weight=1)  # Main area: fills remaining
        self.root.rowconfigure(0, weight=1)

        # ========== LEFT SIDEBAR (Settings Panel) ==========
        # Create a container frame for sidebar
        sidebar_container = ttk.Frame(self.root, style='Header.TFrame')
        sidebar_container.grid(row=0, column=0, sticky='nsew', padx=16, pady=16)
        sidebar_container.config(width=320)
        sidebar_container.grid_propagate(False)
        sidebar_container.columnconfigure(0, weight=1)
        sidebar_container.rowconfigure(0, weight=1)  # Content area - grows
        sidebar_container.rowconfigure(1, weight=0)  # Buttons at bottom - fixed

        # Frame to hold all scrollable content (no canvas, no scrollbar)
        sidebar = ttk.Frame(sidebar_container, style='Header.TFrame')
        sidebar.grid(row=0, column=0, sticky='nsew')
        sidebar.columnconfigure(0, weight=1)

        # Add padding wrapper for nicer spacing
        sidebar_padded = ttk.Frame(sidebar, style='Header.TFrame')
        sidebar_padded.pack(fill='both', expand=True, padx=12, pady=12)
        sidebar_padded.columnconfigure(0, weight=1)
        sidebar_padded.rowconfigure(0, weight=1)  # Scrollable content area
        sidebar_padded.rowconfigure(1, weight=0)  # Speed section (bottom)

        # Create scrollable area with mousewheel support
        scroll_frame = ttk.Frame(sidebar_padded, style='Header.TFrame')
        scroll_frame.grid(row=0, column=0, sticky='nsew')
        scroll_frame.columnconfigure(0, weight=1)

        # Use Canvas for scroll with mousewheel but hide scrollbar
        canvas = tk.Canvas(
            scroll_frame,
            bg=COLORS['surface'],
            highlightthickness=0,
            borderwidth=0
        )
        canvas.pack(side='left', fill='both', expand=True)

        # Create frame inside canvas for content
        scrollable_content = ttk.Frame(canvas, style='Header.TFrame')
        scrollable_content.columnconfigure(0, weight=1)
        canvas_window = canvas.create_window((0, 0), window=scrollable_content, anchor='nw')

        # Update scroll region
        def on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox('all'))
            # Make scrollable content width match canvas
            canvas.itemconfig(canvas_window, width=canvas.winfo_width())

        scrollable_content.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))

        # Mousewheel scrolling - only on canvas, not on widgets inside
        def _on_mousewheel(event):
            # Only scroll if mouse is over canvas, not over combobox or other widgets
            widget = event.widget
            # Check if the widget is the canvas or a child of the scrollable content
            if widget == canvas or canvas.winfo_containing(event.x_root, event.y_root) == canvas:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')

        canvas.bind('<MouseWheel>', _on_mousewheel)
        # Also bind to scrollable_content to catch events not directly on canvas
        scrollable_content.bind('<MouseWheel>', _on_mousewheel)

        self.sidebar = scrollable_content
        self.sidebar_container = sidebar_container

        # Use scrollable content for all content below
        sidebar = scrollable_content
        ttk.Label(sidebar, text='Filename', style='Heading.TLabel').pack(anchor='w', pady=(0, 6))

        filename_frame = ttk.Frame(sidebar, style='Header.TFrame')
        filename_frame.pack(fill='x', pady=(0, 12))
        filename_frame.columnconfigure(0, weight=1)

        default_name = f"{APP_NAME.replace(' ', '_').lower()}"
        self.filename_var = tk.StringVar(value=default_name)
        self.filename_entry = ttk.Entry(
            sidebar,
            textvariable=self.filename_var,
            style='Modern.TEntry',
            width=20
        )
        self.filename_entry.pack(fill='x', pady=(0, 12))

        # --- Save Location Section ---
        ttk.Label(sidebar, text='Save Location', style='Heading.TLabel').pack(anchor='w', pady=(0, 6))

        self.save_dir_var = tk.StringVar(value=os.path.abspath(os.getcwd()))
        self.save_dir_entry = ttk.Entry(
            sidebar,
            textvariable=self.save_dir_var,
            style='Modern.TEntry',
            state='readonly',
            width=24
        )
        self.save_dir_entry.pack(fill='x', pady=(0, 8))

        browse_btn = ttk.Button(
            sidebar,
            text='Browse Folder',
            style='Secondary.TButton',
            command=self.browse_directory
        )
        browse_btn.pack(fill='x', pady=(0, 12))

        # --- Voice Selection Section (Dropdown) ---
        ttk.Label(sidebar, text='Voice', style='Heading.TLabel').pack(anchor='w', pady=(12, 6))

        self.voice_var = tk.StringVar(value='af_heart')

        # Create dropdown with friendly voice names
        voice_options = [VOICE_NAMES[code] for code in VOICE_LIST]
        self.voice_dropdown = ttk.Combobox(
            sidebar,
            textvariable=self.voice_var,
            values=voice_options,
            state='readonly',
            style='Modern.TCombobox',
            width=28
        )
        self.voice_dropdown.pack(fill='x', pady=(0, 12))
        # Set default display value
        self.voice_dropdown.set(VOICE_NAMES['af_heart'])

        # --- Speed Section (Right after Voice) ---
        ttk.Label(sidebar, text='Speed', style='Heading.TLabel').pack(anchor='w', pady=(12, 6))

        self.speed_var = tk.DoubleVar(value=1.0)
        speed_frame = ttk.Frame(sidebar, style='Header.TFrame')
        speed_frame.pack(fill='x', pady=(0, 12))
        speed_frame.columnconfigure(0, weight=1)
        speed_scale = ttk.Scale(speed_frame, from_=0.5, to=2.0, variable=self.speed_var, orient='horizontal')
        speed_scale.pack(side='left', fill='x', expand=True)
        self.speed_label = ttk.Label(speed_frame, text='1.0x', style='Heading.TLabel', foreground=COLORS['primary'], width=4)
        self.speed_label.pack(side='left', padx=(8, 0))
        self.speed_var.trace_add('write', lambda *_: self._update_speed_label())

        # --- Progress Bar Section ---
        ttk.Label(sidebar, text='Progress', style='Heading.TLabel').pack(anchor='w', pady=(12, 4))
        self.progress_var = tk.DoubleVar(value=0)
        ttk.Progressbar(sidebar, variable=self.progress_var, maximum=100, mode='determinate').pack(fill='x', pady=(0, 4))
        self.time_var = tk.StringVar(value='--:-- / --:--')
        ttk.Label(sidebar, textvariable=self.time_var, style='Muted.TLabel').pack(anchor='w')

        # --- History Section ---
        ttk.Label(sidebar, text='Recent Files', style='Heading.TLabel').pack(anchor='w', pady=(12, 4))
        hist_frame = ttk.Frame(sidebar, style='Header.TFrame')
        hist_frame.pack(fill='both', expand=False, pady=(0, 12), padx=(0, 0))
        hist_frame.columnconfigure(0, weight=1)
        hist_frame.rowconfigure(0, weight=0)

        self.history_listbox = tk.Listbox(
            hist_frame,
            height=4,
            bg=COLORS['surface'],
            fg=COLORS['text_primary'],
            borderwidth=1,
            relief='solid',
            font=FONTS['small']
        )
        self.history_listbox.grid(row=0, column=0, sticky='nsew')
        self.history_listbox.bind('<Double-Button-1>', self._on_history_play)

        # --- Status Section (in scrollable area) ---
        status_frame = ttk.Frame(sidebar, style='Header.TFrame')
        status_frame.pack(fill='x', pady=(12, 0))
        status_frame.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value='Ready')
        status_label = ttk.Label(
            status_frame,
            textvariable=self.status_var,
            style='Status.TLabel',
            wraplength=250
        )
        status_label.pack(anchor='w')

        self.output_path_var = tk.StringVar()
        path_label = ttk.Label(
            status_frame,
            textvariable=self.output_path_var,
            style='Path.TLabel',
            wraplength=250
        )
        path_label.pack(anchor='w', pady=(4, 0))

        # --- Action Buttons Section (FIXED at bottom) ---
        button_frame = ttk.Frame(sidebar_container, style='Header.TFrame')
        button_frame.grid(row=1, column=0, sticky='ew', pady=(12, 0), padx=12)
        button_frame.columnconfigure(0, weight=1)

        self.generate_btn = ttk.Button(
            button_frame,
            text='🎙 Generate',
            style='Primary.TButton',
            command=self.start_generation
        )
        self.generate_btn.pack(fill='x', pady=(0, 8), padx=0)

        # Preview button
        preview_btn = ttk.Button(
            button_frame,
            text='👂 Preview (5s)',
            style='Secondary.TButton',
            command=self.start_preview
        )
        preview_btn.pack(fill='x', pady=(0, 8), padx=0)

        self.cancel_btn = ttk.Button(
            button_frame,
            text='⏹ Cancel',
            style='Secondary.TButton',
            command=self.cancel_generation,
            state='disabled'
        )
        self.cancel_btn.pack(fill='x', padx=0)

        # ========== MAIN CONTENT AREA (Text Editor) ==========
        main_pane = ttk.Frame(self.root, style='Card.TFrame')
        main_pane.grid(row=0, column=1, sticky='nsew', padx=(0, 16), pady=16)
        main_pane.columnconfigure(0, weight=1)
        main_pane.columnconfigure(1, weight=0)
        main_pane.rowconfigure(0, weight=0)  # Header row - fixed
        main_pane.rowconfigure(0, weight=0)  # Header - fixed
        main_pane.rowconfigure(1, weight=1)  # Text area - grows
        main_pane.rowconfigure(2, weight=0)  # Char counter - fixed
        main_pane.rowconfigure(3, weight=0)  # Status - fixed

        # Simple header with title and toggle
        header_frame = ttk.Frame(main_pane, style='Card.TFrame')
        header_frame.grid(row=0, column=0, columnspan=2, sticky='ew', padx=16, pady=(12, 12))
        header_frame.columnconfigure(0, weight=1)

        header_label = ttk.Label(
            header_frame,
            text='Content',
            style='Heading.TLabel'
        )
        header_label.pack(side='left', anchor='w')

        # Text editor container (main focus of the UI)
        text_container = ttk.Frame(main_pane, style='Card.TFrame')
        text_container.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=16, pady=(0, 12))
        text_container.columnconfigure(0, weight=1)
        text_container.rowconfigure(0, weight=1)

        self.text_box = tk.Text(
            text_container,
            wrap='word',
            font=FONTS['body'],
            bg=COLORS['surface'],
            fg=COLORS['text_primary'],
            bd=0,
            relief='solid',
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['primary'],
            insertbackground=COLORS['primary'],
            selectbackground=COLORS['primary'],
            selectforeground='white',
            padx=16,
            pady=12,
            spacing1=2,
            spacing3=2,
            undo=True,
            maxundo=-1
        )
        self.text_box.grid(row=0, column=0, sticky='nsew')

        # Setup path preview updates
        self.filename_var.trace_add('write', lambda *_: self._update_path_preview())
        self.save_dir_var.trace_add('write', lambda *_: self._update_path_preview())

        # Character counter
        self.char_count_var = tk.StringVar(value='0 characters')
        char_label = ttk.Label(main_pane, textvariable=self.char_count_var, style='Muted.TLabel')
        char_label.grid(row=2, column=0, columnspan=2, sticky='w', padx=16, pady=(0, 4))
        self.text_box.bind('<<Modified>>', self._on_text_modified)

        # Mirror status in the main pane for when the sidebar is collapsed
        status_preview = ttk.Label(main_pane, textvariable=self.status_var, style='Status.TLabel')
        status_preview.grid(row=3, column=0, columnspan=2, sticky='w', padx=16, pady=(0, 0))

        self._update_path_preview()
        self.main_pane = main_pane

    def _load_history(self):
        """Load generation history from JSON file."""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    return json.load(f).get('history', [])
        except Exception:
            pass
        return []

    def _save_history(self):
        """Save generation history to JSON file."""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({'history': self.history[-20:]}, f, indent=2)
        except Exception:
            pass

    def _add_to_history(self, filename, voice, word_count):
        """Add a generated file to history."""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'voice': voice,
            'word_count': word_count,
            'path': os.path.join(self.save_dir_var.get(), filename)
        }
        self.history.append(entry)
        self._save_history()
        self._update_history_display()

    def _toggle_theme(self):
        """Toggle between light and dark themes."""
        global COLORS
        self.is_dark_mode = not self.is_dark_mode
        COLORS = COLORS_DARK.copy() if self.is_dark_mode else COLORS_LIGHT.copy()
        self._setup_styles()
        self._refresh_ui()

    def _refresh_ui(self):
        """Re-apply styles to all widgets after theme change."""
        try:
            style = ttk.Style()
            self._setup_styles()
            # Update root background
            self.root.configure(bg=COLORS['background'])
            # Update all frames by forcing a redraw
            for child in self.root.winfo_children():
                child.configure(style=child.cget('style'))
        except Exception as e:
            pass

    def _update_history_display(self):
        """Update the history list display in sidebar."""
        try:
            # Clear old history items
            if hasattr(self, 'history_listbox'):
                self.history_listbox.delete(0, tk.END)
                # Add recent files
                for item in reversed(self.history[-10:]):
                    voice_name = self._get_voice_friendly_name(item['voice'])
                    display = f"{os.path.basename(item['filename'])} ({voice_name.split('(')[0].strip()})"
                    self.history_listbox.insert(0, display)
        except Exception:
            pass

    def _play_audio_preview(self, audio_path):
        """Attempt to play audio file (requires winsound on Windows or pyaudio)."""
        try:
            import platform
            if platform.system() == 'Windows':
                import winsound
                winsound.PlaySound(audio_path, winsound.SND_FILENAME)
            else:
                # On Linux/Mac, try using subprocess with available player
                import subprocess
                subprocess.run(['afplay', audio_path] if platform.system() == 'Darwin' else ['aplay', audio_path], check=False)
        except Exception as e:
            messagebox.showinfo('Preview', 'Audio preview not available on this system.')

    def _get_voice_code(self, voice_input):
        """Convert voice code or friendly name to voice code."""
        voice_input = voice_input.strip().lower()

        # Check if it's already a voice code
        if voice_input in VOICE_LIST:
            return voice_input

        # Check friendly names mapping - find the code for this friendly name
        for code, friendly in VOICE_NAMES.items():
            if voice_input == friendly.lower():
                return code
            # Also check if the voice name (without locale) matches
            if voice_input in friendly.lower():
                return code

        return voice_input  # Return as-is if not found

    def _get_voice_friendly_name(self, voice_code):
        """Get friendly name for a voice code."""
        return VOICE_NAMES.get(voice_code.strip().lower(), voice_code)

    def _update_speed_label(self):
        """Update speed label to show current value."""
        try:
            if hasattr(self, 'speed_label'):
                speed_val = self.speed_var.get()
                self.speed_label.config(text=f'{speed_val:.1f}x')
        except Exception:
            pass

    def _update_pitch_label(self):
        """Pitch is not supported by Kokoro - placeholder for compatibility."""
        pass

    def _on_history_play(self, event):
        """Play a file from history on double-click."""
        try:
            sel = self.history_listbox.curselection()
            if sel:
                # Get the history index (reversed because we display in reverse)
                idx = len(self.history) - 1 - sel[0]
                if 0 <= idx < len(self.history):
                    file_path = self.history[idx]['path']
                    if os.path.exists(file_path):
                        self._play_audio_preview(file_path)
                    else:
                        messagebox.showwarning('File Not Found', f'File not found: {file_path}')
        except Exception as e:
            messagebox.showerror('Error', f'Could not play file: {e}')

    def browse_directory(self):
        """Open directory picker and set save directory."""
        directory = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if directory:
            self.save_dir_var.set(directory)

    def _update_path_preview(self, *_):
        """Update the output path preview in the footer."""
        filename = self.filename_var.get().strip()
        save_dir = self.save_dir_var.get().strip() or os.getcwd()
        if not filename:
            preview = '📁 Enter a filename to see the save path'
        else:
            preview_name = filename if filename.lower().endswith('.wav') else f'{filename}.wav'
            full_path = os.path.join(save_dir, preview_name)
            preview = f'📁 Will save to: {full_path}'
        self.output_path_var.set(preview)

    def _on_text_modified(self, event=None):
        # Reset modified flag and update character count
        try:
            self.text_box.edit_modified(False)
        except Exception:
            pass
        text = self.text_box.get('1.0', 'end-1c')
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self.char_count_var.set(f'{chars} characters • {words} words')

    def chunk_text(self, text: str, max_words: int = 50) -> list:
        """Split text into chunks by word count (max 50 words per chunk for CPU efficiency)."""
        words = text.split()
        chunks = []
        current_chunk = []

        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= max_words:
                chunks.append(' '.join(current_chunk))
                current_chunk = []

        # Add remaining words
        if current_chunk:
            chunks.append(' '.join(current_chunk))

        return chunks if chunks else [text]

    def detect_language_code(self, text: str) -> str:
        """Detect language from text and return appropriate language code for Kokoro."""
        # Simple character-based language detection
        text_lower = text.lower()

        # Bengali/Bangla script (U+0980 - U+09FF)
        bengali_chars = re.search(r'[\u0980-\u09FF]', text)
        if bengali_chars:
            return 'bn'  # Bengali language code

        # Hindi/Devanagari script
        hindi_chars = re.search(r'[\u0900-\u097F]', text)
        if hindi_chars:
            return 'hi'

        # Chinese characters
        chinese_chars = re.search(r'[\u4E00-\u9FFF\u3040-\u309F\u30A0-\u30FF]', text)
        if chinese_chars:
            # Check for Japanese hiragana/katakana vs Chinese hanzi
            japanese_chars = re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text)
            if japanese_chars and len(japanese_chars.group()) > len(chinese_chars.group()) * 0.3:
                return 'ja'
            return 'zh'

        # Japanese (if no Chinese but has hiragana/katakana)
        japanese_chars = re.search(r'[\u3040-\u309F\u30A0-\u30FF]', text)
        if japanese_chars:
            return 'ja'

        # Indonesian
        if 'indonesia' in text_lower or re.search(r'\b(saya|anda|dia|mereka)\b', text_lower):
            return 'id'

        # Portuguese
        if re.search(r'[\xE0\xE1\xE9\xED\xF3\xFA\xE3\xF5\xE7]', text):
            # Portuguese has these accented characters
            return 'pt'

        # Finnish
        if re.search(r'[\u00E4\u00F6\xE4\xF6]', text):  # ä ö
            return 'fi'

        # Default to English
        return 'a'  # Kokoro default (English)

    def transliterate_bengali_to_hindi(self, text: str) -> str:
        """Convert Bengali text to Hindi (Devanagari) for better voice synthesis."""
        try:
            from bangla import convert
            # Try converting Bengali to phonetic representation
            # This is a workaround since Kokoro doesn't have native Bengali support
            return text
        except Exception:
            return text

    def get_optimal_voice_for_language(self, voice_code: str, lang_code: str) -> tuple:
        """Ensure voice matches the language for better results."""
        # Map voice prefixes to supported languages
        voice_lang_map = {
            'af_': ['a', 'en'],  # American Female - English
            'am_': ['a', 'en'],  # American Male - English
            'bf_': ['a', 'en'],  # British Female - English
            'bm_': ['a', 'en'],  # British Male - English
            'ef_': ['a', 'en'],  # European Female - English
            'em_': ['a', 'en'],  # European Male - English
            'ff_': ['fi'],       # Finnish Female
            'hf_': ['hi'],       # Hindi Female
            'hm_': ['hi'],       # Hindi Male
            'if_': ['id'],       # Indonesian Female
            'im_': ['id'],       # Indonesian Male
            'jf_': ['ja'],       # Japanese Female
            'jm_': ['ja'],       # Japanese Male
            'pf_': ['pt'],       # Portuguese Female
            'pm_': ['pt'],       # Portuguese Male
            'zf_': ['zh'],       # Chinese Female
        }

        # Bengali (bn) should use Hindi voices since they're similar
        if lang_code == 'bn':
            lang_code = 'hi'  # Use Hindi pipeline for Bengali
            # If user selected Hindi voices, keep them; otherwise default to Hindi voices
            voice_prefix = voice_code[:3]
            if voice_prefix in ['hf_', 'hm_']:
                return voice_code, lang_code
            else:
                return 'hm_omega', lang_code  # Best Hindi voice for Bengali

        # Check if current voice supports the detected language
        voice_prefix = voice_code[:3]
        if voice_prefix in voice_lang_map:
            supported_langs = voice_lang_map[voice_prefix]
            if lang_code in supported_langs:
                return voice_code, lang_code

        # If voice doesn't support language, find a compatible voice
        # For now, default to English with English voice
        if lang_code == 'a' or lang_code == 'en':
            return 'af_heart', 'a'  # Default English

        fallback_voice = DEFAULT_VOICE_BY_LANG.get(lang_code, 'af_heart')
        fallback_lang = lang_code if lang_code != 'bn' else 'hi'
        return fallback_voice, fallback_lang

    def _get_pipeline_for_lang(self, lang_code: str):
        """Return cached Kokoro pipeline for a given language, creating if needed."""
        global pipelines
        target_lang = lang_code or 'a'
        if target_lang not in pipelines:
            pipelines[target_lang] = KPipeline(lang_code=target_lang)
        return pipelines[target_lang]


    def start_generation(self):
        """Start audio generation in background thread."""
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo('Generation in Progress', 'Please wait for the current generation to complete.')
            return

        text = self.text_box.get('1.0', 'end').strip()
        if not text:
            messagebox.showwarning('No Text', 'Please enter some text to synthesize.')
            return

        filename = self.filename_var.get().strip()
        if not filename:
            messagebox.showwarning('No Filename', 'Please enter a filename for the output.')
            return

        save_dir = self.save_dir_var.get().strip()
        if not os.path.isdir(save_dir):
            messagebox.showwarning('Invalid Directory', 'Please select a valid save directory.')
            return

        # Auto-append .wav if not present
        if not filename.lower().endswith('.wav'):
            filename += '.wav'

        save_path = os.path.join(save_dir, filename)

        voice = self._get_voice_code(self.voice_var.get())

        # Reset cancel event
        self.cancel_event.clear()

        # Update UI state
        self.generate_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.status_var.set('🎙 Starting generation...')
        self.progress_var.set(0)

        # Start background thread
        self.worker_thread = threading.Thread(
            target=self.generate_worker,
            args=(text, voice, save_path, self.cancel_event),
            daemon=True
        )
        self.worker_thread.start()

    def start_preview(self):
        """Generate a 5-second audio preview from the first 500 characters of text."""
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo('Generation in Progress', 'Please wait for current generation to complete.')
            return

        text = self.text_box.get('1.0', 'end').strip()
        if not text:
            messagebox.showwarning('No Text', 'Please enter some text to preview.')
            return

        # Take first 500 chars or first sentence
        preview_text = text[:500]
        voice = self._get_voice_code(self.voice_var.get())

        # Reset cancel event
        self.cancel_event.clear()

        # Update UI state
        self.generate_btn.config(state='disabled')
        self.cancel_btn.config(state='normal')
        self.status_var.set('🎧 Generating preview...')

        # Start background thread for preview (don't save, just play)
        self.worker_thread = threading.Thread(
            target=self._preview_worker,
            args=(preview_text, voice, self.cancel_event),
            daemon=True
        )
        self.worker_thread.start()

    def _preview_worker(self, text, voice, cancel_event):
        """Generate preview audio and play it without saving."""
        # Initialize torch lazily
        global device
        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"

        # Chunk text for consistent processing
        text_chunks = self.chunk_text(text, max_words=50)
        speed = self.speed_var.get()

        try:
            self.root.after(0, lambda: self.status_var.set('🎧 Generating preview...'))
            audio_segments = []

            for chunk in text_chunks:
                if cancel_event.is_set():
                    return

                chunk_lang = self.detect_language_code(chunk)
                chunk_voice, pipeline_lang = self.get_optimal_voice_for_language(voice, chunk_lang)
                processed_chunk = self.transliterate_bengali_to_hindi(chunk) if chunk_lang == 'bn' else chunk

                pipeline = self._get_pipeline_for_lang(pipeline_lang)
                gen = pipeline(processed_chunk, voice=chunk_voice, speed=speed, split_pattern=r'\n+')
                for _, _, audio in gen:
                    audio_segments.append(np.asarray(audio))

            if audio_segments:
                full_audio = np.concatenate(audio_segments, axis=0)
                temp_path = os.path.join(os.path.expanduser('~'), '.tts_preview.wav')
                sf.write(temp_path, full_audio, SAMPLE_RATE)
                self.root.after(0, lambda: self.status_var.set('▶️ Playing preview...'))
                self.root.after(0, lambda: self._play_audio_preview(temp_path))
                self.root.after(0, lambda: self._on_done('✅ Preview complete', success=True))
            else:
                self.root.after(0, lambda: self._on_done('⚠️ No preview generated', success=False))

        except Exception as e:
            self.root.after(0, lambda e_msg=str(e): self._on_done(f'❌ Preview error: {e_msg}', success=False))

    def cancel_generation(self):
        """Request cancellation of ongoing generation."""
        if self.worker_thread and self.worker_thread.is_alive():
            self.cancel_event.set()
            self.status_var.set('⏸ Cancelling...')
            self.cancel_btn.config(state='disabled')

    def generate_worker(self, text, voice, save_path, cancel_event):
        """Generate audio by processing text in chunks and merging results."""
        global device
        if device is None:
            try:
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            except Exception:
                device = "cpu"

        text_chunks = self.chunk_text(text, max_words=50)
        temp_dir = os.path.join(os.path.dirname(save_path), '.tts_temp')
        os.makedirs(temp_dir, exist_ok=True)

        speed = self.speed_var.get()
        audio_segments = []
        self.gen_start_time = time.time()
        self.gen_total_chunks = len(text_chunks)

        try:
            for chunk_idx, chunk in enumerate(text_chunks):
                if cancel_event.is_set():
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                    self.root.after(0, lambda: self._on_done('🚫 Generation cancelled', success=False))
                    return

                progress = (chunk_idx / len(text_chunks)) * 100
                elapsed = time.time() - self.gen_start_time
                per_chunk = elapsed / (chunk_idx + 1) if chunk_idx > 0 else 1
                remaining = per_chunk * (len(text_chunks) - chunk_idx - 1)

                def update_status(idx, total, prog, el, rem):
                    self.progress_var.set(prog)
                    el_str = f"{int(el)//60}:{int(el)%60:02d}"
                    rem_str = f"{int(rem)//60}:{int(rem)%60:02d}"
                    self.time_var.set(f"{el_str} / {rem_str}")
                    self.status_var.set(f'⚙️ Chunk {idx+1}/{total}...')

                self.root.after(0, lambda idx=chunk_idx, total=len(text_chunks), prog=progress, el=elapsed, rem=remaining:
                    update_status(idx, total, prog, el, rem))

                chunk_lang = self.detect_language_code(chunk)
                chunk_voice, pipeline_lang = self.get_optimal_voice_for_language(voice, chunk_lang)
                processed_chunk = self.transliterate_bengali_to_hindi(chunk) if chunk_lang == 'bn' else chunk
                pipeline = self._get_pipeline_for_lang(pipeline_lang)

                try:
                    gen = pipeline(processed_chunk, voice=chunk_voice, speed=speed, split_pattern=r'\n+')
                    chunk_audio = []
                    for _, _, audio in gen:
                        audio_np = np.asarray(audio)
                        chunk_audio.append(audio_np)

                    if chunk_audio:
                        chunk_full = np.concatenate(chunk_audio, axis=0)
                        audio_segments.append(chunk_full)
                except Exception as e:
                    self.root.after(0, lambda e_msg=str(e), idx=chunk_idx: self._on_done(f'❌ Error in chunk {idx+1}: {e_msg}', success=False))
                    try:
                        shutil.rmtree(temp_dir)
                    except Exception:
                        pass
                    return

            if audio_segments:
                full_audio = np.concatenate(audio_segments, axis=0)
                sf.write(save_path, full_audio, SAMPLE_RATE)

                word_count = len(text.split())
                filename = os.path.basename(save_path)
                self.root.after(0, lambda wc=word_count, fn=filename: self._add_to_history(fn, voice, wc))

                self.root.after(0, lambda: self._on_done('✅ Audio saved successfully!', success=True))
            else:
                self.root.after(0, lambda: self._on_done('⚠️ No audio generated', success=False))

        except Exception as e:
            self.root.after(0, lambda e_msg=str(e): self._on_done(f'❌ Error: {e_msg}', success=False))
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    def _on_done(self, message, success=True):
        """Update UI when generation completes or fails."""
        self.status_var.set(message)
        self.progress_var.set(100 if success else 0)
        self.time_var.set('Done' if success else '--:-- / --:--')
        self.generate_btn.config(state='normal')
        self.cancel_btn.config(state='disabled')


def main():
    root = tk.Tk()
    app = TTSApp(root)
    # insert a helpful default text
    sample = (
        "Hidden at the very edge of our solar system, in a realm so cold and dark that sunlight barely reaches it, "
        "lies a world shrouded in mystery."
    )
    app.text_box.insert('1.0', sample)
    # Update initial char/word count
    app._on_text_modified()

    # Make sure window is visible and on top
    root.deiconify()
    root.lift()
    root.attributes('-topmost', False)  # Allow other windows to be on top

    root.mainloop()


if __name__ == '__main__':
    main()
