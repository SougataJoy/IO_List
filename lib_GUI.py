# lib_GUI.py

""" Reusable Library for GUI """

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter import simpledialog, colorchooser

DEFAULT_FONT = ("Segoe UI", 10)
TITLE_FONT = ("Segoe UI", 12, "bold")



# ----------------------------------------------------------------------------
# Internal helper
# ----------------------------------------------------------------------------
def _place(widget, pack=None, grid=None, place=None, 
           place_widget=True):
    """Place a widget using pack / grid / place (default: pack with pady=5)."""
    if not place_widget:
        return widget
    if grid is not None:
        widget.grid(**grid)
    elif place is not None:
        widget.place(**place)
    else:
        widget.pack(**(pack if pack is not None else {"pady": 5}))
    return widget

#----------------------------------------------------------
# Page
#----------------------------------------------------------
def _page(title, geometry="400x300", 
          resizable_width=False, resizable_height=False):
    root = tk.Tk()
    root.title(title)

    # 1. Extract width and height from the geometry string 

    width, height = map(int, geometry.lower().split("x"))

    # 2. Query monitor dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 3. Calculate center coordinates
    x = int((screen_width - width) / 2)
    y = int((screen_height - height) / 2)

    # 4. Set geometry with calculated offsets
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.resizable(resizable_width, resizable_height)

    return root

#----------------------------------------------------------
# Labels
#----------------------------------------------------------
def _label(parent, text="", font=DEFAULT_FONT, anchor="w", 
           textvariable=None,
           pack=None, grid=None, place=None, place_widget=True,
             **kw):
    w = ttk.Label(parent, text=text, font=font, anchor=anchor,
                  textvariable=textvariable, **kw)
    return _place(w, pack, grid, place, place_widget)

# ----------------------------------------------------------
# Namebox / Entry (Single-line Text Input)
# ----------------------------------------------------------
def _namebox(parent, width=25, textvariable=None, font=DEFAULT_FONT,
             pack=None, grid=None, place=None, place_widget=True, **kw):
    """
    Sizable text input box.
    'width' defines the size in character units.
    """
    w = ttk.Entry(parent, width=width, textvariable=textvariable, font=font, **kw)
    return _place(w, pack, grid, place, place_widget)

# ----------------------------------------------------------
# Dropbox / Combobox (Dropdown Menu)
# ----------------------------------------------------------
def _dropbox(parent, values=None, width=23, default_index=0, state="readonly",
             textvariable=None, font=DEFAULT_FONT, pack=None, grid=None, 
             place=None, place_widget=True, **kw):
    """
    Sizable dropdown menu.
    'values' takes a list/tuple of string options.
    'width' defines the width in character units.
    """
    if values is None:
        values = []
    w = ttk.Combobox(parent, values=values, width=width, state=state,
                     textvariable=textvariable, font=font, **kw)
    if values and default_index is not None and default_index < len(values):
        w.current(default_index)
    return _place(w, pack, grid, place, place_widget)

#----------------------------------------------------------
# Container Frame / LabelFrame
#----------------------------------------------------------
def _frame(parent, text=None, padding=10, 
           pack=None, grid=None, place=None, place_widget=True, **kw):
    """Creates a ttk.LabelFrame if text is provided, otherwise ttk.Frame."""
    if text:
        w = ttk.LabelFrame(parent, text=text, padding=padding, **kw)
    else:
        w = ttk.Frame(parent, padding=padding, **kw)
    return _place(w, pack, grid, place, place_widget)

# ----------------------------------------------------------
# Placeholder behaviour for Entry boxes
# ----------------------------------------------------------
def _add_placeholder(entry, placeholder, placeholder_color="grey",
                     normal_color="black"):
    """
    Shows 'placeholder' inside the Entry:
      - box not selected + empty  -> placeholder is shown (grey)
      - box selected              -> placeholder is cleared, ready to type
      - box left while still empty-> placeholder is shown again
    """
    entry._placeholder = placeholder
    entry._showing_placeholder = True

    # Show placeholder at start
    entry.delete(0, tk.END)
    entry.insert(0, placeholder)
    entry.config(fg=placeholder_color)

    def on_focus_in(event):
        # Box selected: clear it only if it is showing the placeholder
        if entry._showing_placeholder:
            entry.delete(0, tk.END)
            entry.config(fg=normal_color)
            entry._showing_placeholder = False

    def on_focus_out(event):
        # Box left: if nothing was written, bring the placeholder back
        if not entry.get().strip():
            entry.delete(0, tk.END)
            entry.insert(0, placeholder)
            entry.config(fg=placeholder_color)
            entry._showing_placeholder = True

    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    return entry


def _get_entry_value(entry):
    """Returns the real text typed by the user ('' if only placeholder is showing)."""
    if getattr(entry, "_showing_placeholder", False):
        return ""
    return entry.get()

def _set_entry_value(entry, value, normal_color="black"):
    """Puts a saved value into a placeholder Entry. Empty value keeps the placeholder."""
    if not value:
        return
    entry.delete(0, tk.END)
    entry.insert(0, value)
    entry.config(fg=normal_color)
    entry._showing_placeholder = False

# ----------------------------------------------------------
# JC NO entry:  ppp xxzz - abc   (e.g. PEI 2526 - 123)
# ----------------------------------------------------------
class JCNoEntry(tk.Frame):
    def __init__(self, parent, prefixes=("PEI", "PEW"), font=DEFAULT_FONT,
                 len_xx=2, len_zz=2, len_abc=3):
        super().__init__(parent)
        self._lens = (len_xx, len_zz, len_abc)

        self.prefix = ttk.Combobox(self, values=prefixes, width=5,
                                   state="readonly", font=font)
        self.prefix.current(0)
        self.prefix.pack(side="left")

        self.xx = self._digit_box(len_xx, font)
        self.xx.pack(side="left", padx=(8, 2))

        self.zz = self._digit_box(len_zz, font)
        self.zz.pack(side="left", padx=(2, 0))

        tk.Label(self, text=" - ", font=font).pack(side="left")

        self.abc = self._digit_box(len_abc, font)
        self.abc.pack(side="left")

    def _digit_box(self, max_len, font):
        """Entry that accepts digits only, up to max_len characters."""
        def check(proposed):
            return proposed == "" or (proposed.isascii() and proposed.isdigit()
                                      and len(proposed) <= max_len)
        vcmd = (self.register(check), "%P")
        box = tk.Entry(self, width=max_len + 2, font=font, justify="center",
                       validate="key", validatecommand=vcmd)
        _add_placeholder(box, "0" * max_len)      # <<< CHANGE 1: shows 00 / 00 / 000
        return box

    def is_valid(self):
        """True only when all three numeric parts are completely filled."""
        return True

    def get(self):
        """Returns e.g. 'PEI 2526 - 123'."""
        xx  = _get_entry_value(self.xx).zfill(self._lens[0])
        zz  = _get_entry_value(self.zz).zfill(self._lens[1])
        abc = _get_entry_value(self.abc).zfill(self._lens[2])
        return f"{self.prefix.get()} {xx}{zz} - {abc}"

    def _fill(self, box, value):
        """All-zero or empty means 'nothing typed', so the grey placeholder stays."""
        if value.strip("0"):
            _set_entry_value(box, value)

    def set(self, text):
        """Restores from text like 'PEW 2526 - 123'."""
        try:
            prefix, rest = text.split(" ", 1)
            left, abc = rest.split(" - ")
        except ValueError:
            return
        self.prefix.set(prefix)
        self._fill(self.xx, left[:self._lens[0]])
        self._fill(self.zz, left[self._lens[0]:])
        self._fill(self.abc, abc)

# ----------------------------------------------------------
# <prev / next> buttons: same position on every page
# ----------------------------------------------------------
def _nav_buttons(root, on_prev=None, on_next=None):
    """<prev at bottom-left, next> at bottom-right. Pass None to hide one."""
    def make(text, cmd):
        return tk.Button(root, text=text, bg="gray", fg="black",
                         activebackground="gray", activeforeground="black",
                         font=("Times New Roman", 12, "bold"),
                         width=8, pady=4, command=cmd)
    if on_prev:
        make("<prev", on_prev).place(relx=0.0, rely=1.0, x=30, y=-25, anchor="sw")
    if on_next:
        make("next>", on_next).place(relx=1.0, rely=1.0, x=-30, y=-25, anchor="se")

