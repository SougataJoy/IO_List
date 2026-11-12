# interface_gui.py

""" Program for GUI """
import os
from tkinter import filedialog
from excel_export import generate_excel 
import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry 
#from typing import IO
from lib_GUI import _page, _label, _add_placeholder, _get_entry_value, JCNoEntry
import json                                                                  # <<< CHANGE 3
from lib_GUI import (_page, _label, _add_placeholder, _get_entry_value,
                     _set_entry_value, JCNoEntry, _nav_buttons)
import re
from datetime import date
from tkinter import messagebox

MAX_PAGES = 10
MIN_NODE = 0                                                                 # <<< CHANGE 2: node limits
MAX_NODE = 32                                                                # <<< CHANGE 2
DEFAULT_NODE = "1"                                                           # <<< CHANGE 2: start value of both node boxes
PAGES_DATA = []
PAGE_SIZE = "760x600"
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(BASE_DIR, "document_data.json")
LOGO_PATH = os.path.join(BASE_DIR, "logo.png")
# root = _page("CoverPage", PAGE_SIZE, False, False)
SAVED_DATA = {"rev": {}, "doc": {}}

def _read_widget(w):
    """Real value of any widget used on the pages."""
    if isinstance(w, (JCNoEntry, DateEntry, ttk.Combobox)):
        return w.get()
    return _get_entry_value(w)

def _restore_widget(w, value):
    if not value:
        return
    if isinstance(w, JCNoEntry):
        w.set(value)
    elif isinstance(w, DateEntry):
        w.set_date(value)
    elif isinstance(w, ttk.Combobox):
        w.set(value)
    else:
        _set_entry_value(w, value)

def _save_page(key, widgets):
    for label, w in widgets.items():
        SAVED_DATA[key][label] = _read_widget(w)

def save_to_file(path=JSON_PATH):
    """Writes the revision lists and the cover-page data to a JSON file."""
    data = {"rev": REV_DATA, "doc": {}, "pages": PAGES_DATA}                                # <<< CHANGE 2
    for label, default in TABLE_PRIMARY_INFO.items():
        data["doc"][label] = SAVED_DATA["doc"].get(label) or default
    if revision_count():                                               # <<< CHANGE 2
        # the cover page REV. is always the latest revision (R3 in your sheet)
        data["doc"]["Rev. No. :"] = REV_DATA["Rev. No. :"][-1]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

DESCRIPTION_OPTIONS = ["FOR APPROVAL", "AS BUILD"]
# Revision Information:
TABLE_REV_INFO = {
    "Rev. No. :" : "R0",
    "Date :" : "",
    "Description :" : "",
    "Prepared By :" : "SP",
    "Approved By :" : "SR",
    "Checked By :" : "PKR",
    }

# Same index in every list = same revision, oldest first.
REV_DATA = {label: [] for label in TABLE_REV_INFO}

# <<< CHANGE 1: "rev" removed, because REV_DATA replaces it
SAVED_DATA = {"doc": {}}

def revision_count():
    return len(REV_DATA["Rev. No. :"])

def add_revision(values):
    """values = {'Rev. No. :': 'R3', 'Date :': ..., ...}"""
    for label in REV_DATA:
        REV_DATA[label].append(values.get(label, ""))

def delete_revision(index):
    for lst in REV_DATA.values():
        del lst[index]

def clear_revisions():
    for lst in REV_DATA.values():
        lst.clear()

def set_revisions(rows):
    """For your future 'load existing IO List' feature: rows = list of dicts, oldest first."""
    clear_revisions()
    for row in rows:
        add_revision(row)

def revision_rows_newest_first():
    return [[REV_DATA[label][i] for label in REV_DATA]
            for i in reversed(range(revision_count()))]

def next_rev_no(last):
    """'R3' -> 'R4'. Returns '' if the pattern is not letters+digits."""
    m = re.match(r"^(\D*)(\d+)$", last or "")
    return f"{m.group(1)}{int(m.group(2)) + 1}" if m else ""

# Cover Page Information:
TABLE_PRIMARY_INFO = {
    "DWG/DOC TITLE :" : "IO LIST",
    "Rev. No. :" : "R0",
    "PROJECT NAME :" : "Project Name",
    "CLIENT :" : "Client",
    "END USER :" : "End User",
    "VENDOR :    M/s." : "Subtleweigh Electric (I) Pvt. Ltd.",
    "PO REFERENCE :" : "PO Reference",
    "JC NO :" : "JC No",
    "PACKAGE NAME :" : "-NIL-",
    "REFERENCE CLIENT DOC. NAME / NO. :" : "-NIL-",
    "REFERENCE VENDOR DOCUMENT NO :" : "-NIL-",
    "CUSTOMER PROJECT CODE :" : "-NIL-"
    }

def Interface_01():
    root = _page("WelcomePage", "460x460", False, False)

    # Callback to close Interface_01 and launch Interface_02
    def open_interface_02():
        clear_revisions()
        SAVED_DATA["doc"].clear()
        PAGES_DATA.clear()
        root.destroy()
        Interface_02().mainloop()

    # Main Title
    _label(root, "Welcome to the IO List Preparation Tool", 
           font=("Segoe UI", 12, "bold"), anchor="center", 
           pack={"pady": 10})
    # Button to navigate to the next page
    btn_next = tk.Button(
        root,
        text="Create New Document",
        bg="green",
        fg="white",
        activebackground="green",
        activeforeground="white",
        font=("Times New Roman", 12, "bold"),
        padx=12,
        pady=6,
        command=open_interface_02
    )
    btn_next.pack(pady=20)

 
    return root

def Interface_02():
    root = _page("CoverPageRevision", PAGE_SIZE, False, False)      # <<< CHANGE 4: taller window
    widgets = {}

    # ---- helpers -------------------------------------------------------
    def refresh_table():
        tree.delete(*tree.get_children())
        for row in revision_rows_newest_first():            # newest on top
            tree.insert("", "end", values=row)

    def reset_form():
        """Prepare the form for the NEXT revision."""
        n = revision_count()
        if not n:
            return                                          # first time: defaults stay
        last = {label: REV_DATA[label][-1] for label in REV_DATA}
        for label, w in widgets.items():
            if label == "Rev. No. :":
                _set_entry_value(w, next_rev_no(last[label]))
            elif label == "Date :":
                w.set_date(date.today())
            elif label == "Description :":
                w.set(last[label])
            else:
                _set_entry_value(w, last[label])            # names copied from last row

    def on_add():
        values = {label: (_read_widget(w) or TABLE_REV_INFO[label])
                  for label, w in widgets.items()}
        if values["Rev. No. :"] in REV_DATA["Rev. No. :"]:
            messagebox.showwarning("Revision",
                                   f"{values['Rev. No. :']} already exists.")
            return
        add_revision(values)
        refresh_table()
        reset_form()

    def on_delete():
        sel = tree.selection()
        if not sel:
            messagebox.showinfo("Revision", "Select a row in the table first.")
            return
        # table is shown newest first, data is stored oldest first
        delete_revision(revision_count() - 1 - tree.index(sel[0]))
        refresh_table()
        reset_form()

    def open_interface_01():
        root.destroy()
        Interface_01().mainloop()

    def open_interface_03():
        if revision_count() == 0:
            on_add()                                        # nothing added yet: use the form
        root.destroy()
        Interface_03().mainloop()

    # ---- layout --------------------------------------------------------
    container = tk.Frame(root)
    container.pack(side="top", pady=(20, 0))

    tk.Label(container, text="Details of the Revision",
             font=("Segoe UI", 12, "bold"), anchor="center"
             ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)

    # Form for one revision
    for i, (label_text, default_value) in enumerate(TABLE_REV_INFO.items(), start=1):
        tk.Label(container, text=label_text,
                 font=("Segoe UI", 10), anchor="w"
                 ).grid(row=i, column=0, sticky="w", padx=(20, 5), pady=3)

        if label_text == "Date :":
            entry = DateEntry(container, width=43,
                              date_pattern="dd.mm.yyyy")    # <<< CHANGE 4: 14.01.2026 style
        elif label_text == "Description :":
            entry = ttk.Combobox(container, values=DESCRIPTION_OPTIONS,
                                 font=("Segoe UI", 10), width=43, state="readonly")
            entry.current(0)
        else:
            entry = tk.Entry(container, font=("Segoe UI", 10), width=45)
            _add_placeholder(entry, default_value)
        widgets[label_text] = entry
        entry.grid(row=i, column=1, sticky="w", padx=(5, 20), pady=3)

    # Add / Delete buttons
    r = len(TABLE_REV_INFO) + 1
    bar = tk.Frame(container)
    bar.grid(row=r, column=0, columnspan=2, sticky="e", padx=20, pady=8)
    tk.Button(bar, text="Add Revision", bg="green", fg="white",
              font=("Segoe UI", 10, "bold"), command=on_add).pack(side="left", padx=5)
    tk.Button(bar, text="Delete Selected", bg="firebrick", fg="white",
              font=("Segoe UI", 10, "bold"), command=on_delete).pack(side="left", padx=5)

    # Revision table (like the lower part of your Excel cover page)
    cols = [f"c{i}" for i in range(len(TABLE_REV_INFO))]
    tree = ttk.Treeview(container, columns=cols, show="headings", height=6)
    widths = [70, 100, 150, 110, 110, 110]
    for c, label, wd in zip(cols, TABLE_REV_INFO, widths):
        tree.heading(c, text=label.replace(" :", "").upper())   # REV. NO., DATE, ...
        tree.column(c, width=wd, anchor="center")
    tree.grid(row=r + 1, column=0, columnspan=2, padx=20, pady=5)

    # Navigation
    _nav_buttons(root, open_interface_01, open_interface_03)

    refresh_table()          # shows existing revisions when you come back with <prev
    reset_form()
    return root

def Interface_03():
    root = _page("CoverPageDetails", PAGE_SIZE, False, False)

    # Callback to close Interface_03 and launch Interface_02
    def open_interface_02():
        _save_page("doc", widgets)
        root.destroy()
        Interface_02().mainloop()

    # Callback to close Interface_03 and launch Interface_04
    def open_interface_04():
        _save_page("doc", widgets)
        save_to_file()
        root.destroy()
        Interface_04().mainloop()
    
    container = tk.Frame(root)
    container.pack(side="top", pady=(20, 0))

    # Main Title
    tk.Label(container, text="Cover Page Details",
             font=("Segoe UI", 12, "bold"), anchor="center"
             ).grid(row=0, column=0, columnspan=2, sticky="ew", pady=10)
    
    widgets = {}

    # Input Table for Document Details
    for i, (label_text, default_value) in enumerate(
        TABLE_PRIMARY_INFO.items(), start=1):   # start=1: row 0 is the title
        tk.Label(container, text=label_text,
                 font=("Segoe UI", 10), anchor="w"
                 ).grid(row=i, column=0, sticky="w", padx=(20, 5), pady=3)

        if label_text == "JC NO :":
            entry = JCNoEntry(container)
            jc_widget = entry              # keep a reference for validation/saving
        else:
            entry = tk.Entry(container, font=("Segoe UI", 10), width=45)
            _add_placeholder(entry, default_value)
        widgets[label_text] = entry
        _restore_widget(entry, SAVED_DATA["doc"].get(label_text))
        if label_text == "Rev. No. :" and revision_count():
            _set_entry_value(entry, REV_DATA["Rev. No. :"][-1])      # <<< CHANGE 5
        entry.grid(row=i, column=1, sticky="w", padx=(20, 5), pady=3)

    _nav_buttons(root, open_interface_02, open_interface_04)
    return root

def Interface_04():
    root = _page("DocumentDetails", PAGE_SIZE, False, False)
    rows = []

    def row_ok(s, e):
        """True if either box is empty, or Ending >= Starting."""
        sv, ev = _get_entry_value(s), _get_entry_value(e)
        if sv == "" or ev == "":
            return True
        return int(ev) >= int(sv)

    def mark(s, e):
        """Ending box turns light red while the range is wrong."""
        e.config(bg="white" if row_ok(s, e) else "#ffb3b3")

    def snapshot():
        """Current values typed in the rows ('' if a box still shows its placeholder)."""
        return [{"Panel Name":    _get_entry_value(n),
                 "Starting Node": _get_entry_value(s) or DEFAULT_NODE,   # <<< CHANGE 2: empty -> 1
                 "Ending Node":   _get_entry_value(e) or DEFAULT_NODE}   # <<< CHANGE 2: empty -> 1
                for n, s, e in rows]                                     # <<< CHANGE 1: Cluster removed

    def save_pages():
        PAGES_DATA[:] = snapshot()

    # Callback to close Interface_04 and launch Interface_03
    def open_interface_03():
        save_pages()
        root.destroy()
        Interface_03().mainloop()

    # Callback to close Interface_04 and launch Interface_05
    def open_interface_05():
        for k, (n, s, e) in enumerate(rows, start=1):                    # <<< CHANGE 1: Cluster removed
            if not row_ok(s, e):
                mark(s, e)
                messagebox.showwarning(
                    "Node range",
                    f"Page {k}: Ending Node must be greater than or equal to "
                    f"Starting Node.")
                e.focus_set()
                return                      # stay on this page
        save_pages()
        save_to_file()
        root.destroy()
        Interface_05().mainloop()

    def node_ok(proposed):                                               # <<< CHANGE 2: replaces only_digits
        """Digits only, at most 2 characters, value between MIN_NODE and MAX_NODE."""
        if proposed == "":
            return True                                                  # allow clearing while typing
        return (proposed.isascii() and proposed.isdigit() and len(proposed) <= 2
                and MIN_NODE <= int(proposed) <= MAX_NODE)

    vcmd = (root.register(node_ok), "%P")                                # <<< CHANGE 2: registered once

    def node_box(row, column, saved_value):                              # <<< CHANGE 2: node entry starting at 1
        """Entry for a node number. Starts at 1; an empty box goes back to 1 when left."""
        box = tk.Entry(rows_frame, font=("Segoe UI", 10), width=8, justify="center",
                       validate="key", validatecommand=vcmd)
        box.insert(0, saved_value or DEFAULT_NODE)
        box.grid(row=row, column=column, padx=(0, 10), pady=3)

        def on_leave(_event):
            if not box.get().strip():
                box.insert(0, DEFAULT_NODE)
        box.bind("<FocusOut>", on_leave, add="+")
        return box

    def rebuild(saved=None):
        """Draw one row per page and refill what was typed before."""
        old = saved if saved is not None else snapshot()
        for child in rows_frame.winfo_children():
            child.destroy()
        rows.clear()
        font = ("Segoe UI", 10)

        for k in range(int(pages_var.get())):
            saved_row = old[k] if k < len(old) else {}                   # <<< CHANGE 2: values typed before

            tk.Label(rows_frame, text=f"Panel Name {k + 1} :", font=font, anchor="w"
                     ).grid(row=k, column=0, sticky="w", padx=(10, 3), pady=3)
            n = tk.Entry(rows_frame, font=font, width=20)
            _add_placeholder(n, "Panel Name")
            n.grid(row=k, column=1, padx=(0, 10), pady=3)

            tk.Label(rows_frame, text=f"Starting Node {k + 1} :", font=font, anchor="w"
                     ).grid(row=k, column=2, sticky="w", padx=(0, 3), pady=3)
            s = node_box(k, 3, saved_row.get("Starting Node"))           # <<< CHANGE 2: starts at 1, limit 0-32

            tk.Label(rows_frame, text=f"Ending Node {k + 1} :", font=font, anchor="w"
                     ).grid(row=k, column=4, sticky="w", padx=(0, 3), pady=3)
            e = node_box(k, 5, saved_row.get("Ending Node"))             # <<< CHANGE 2: starts at 1, limit 0-32

            for box in (s, e):
                box.bind("<KeyRelease>", lambda ev, s=s, e=e: mark(s, e), add="+")
                box.bind("<FocusOut>",   lambda ev, s=s, e=e: mark(s, e), add="+")

            _set_entry_value(n, saved_row.get("Panel Name", ""))         # keep what was typed before
            mark(s, e)
            rows.append((n, s, e))                                       # <<< CHANGE 1: Cluster removed, 3 boxes again

    container = tk.Frame(root)
    container.pack(side="top", pady=(20, 0))

    tk.Label(container, text="Document Details", font=("Segoe UI", 12, "bold")
             ).grid(row=0, column=0, columnspan=2, pady=10)

    top = tk.Frame(container)
    top.grid(row=1, column=0, pady=5)
    tk.Label(top, text="No. of Pages :", font=("Segoe UI", 10)).pack(side="left", padx=5)

    pages_var = tk.StringVar(value=str(len(PAGES_DATA) or 1))
    # readonly: only the arrows change the value, so it can never go below 1
    tk.Spinbox(top, from_=1, to=MAX_PAGES, width=5, textvariable=pages_var,
               state="readonly", font=("Segoe UI", 10)).pack(side="left")

    rows_frame = tk.Frame(container)
    rows_frame.grid(row=2, column=0, pady=10)

    rebuild(saved=PAGES_DATA)                     # restore when coming back with <prev
    pages_var.trace_add("write", lambda *a: rebuild())   # rebuild on every change

    _nav_buttons(root, open_interface_03, open_interface_05)
    return root

def Interface_05():
    root = _page("Interface_05", PAGE_SIZE, False, False)

    # Callback to close Interface_05 and launch Interface_04
    def open_interface_04():
        root.destroy()
        Interface_04().mainloop()

    # Callback to close Interface_05 and launch Interface_06
    def open_interface_06():
        root.destroy()
        Interface_06().mainloop()

    container = tk.Frame(root)
    container.pack(side="top", pady=(20, 0))

    # Main Title
    tk.Label(container, text="Details of the Document",
             font=("Segoe UI", 12, "bold"), anchor="center"
             ).grid(row=0, column=0, pady=10)

    _nav_buttons(root, open_interface_04, open_interface_06)
    return root

def Interface_06():
    root = _page("Interface_06", PAGE_SIZE, False, False)

    # Callback to close Interface_06 and launch Interface_05
    def open_interface_05():
        root.destroy()
        Interface_05().mainloop()


    def on_generate():
        path = filedialog.asksaveasfilename(
            parent=root, title="Save Excel file", defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")], initialfile="IO_List.xlsx")
        if not path:
            return                                     # user cancelled
        try:
            if not os.path.exists(JSON_PATH):
                save_to_file()
            generate_excel(JSON_PATH, path, LOGO_PATH)
        except PermissionError:
            messagebox.showerror("Excel", "Cannot write the file.\n"
                                 "Close it in Excel/WPS first, then try again.")
            return                                     # JSON is kept
        except Exception as e:
            messagebox.showerror("Excel", f"Could not generate the file:\n{e}")
            return
        messagebox.showinfo("Excel", f"Saved:\n{path}\n\ndocument_data.json was deleted.")

    container = tk.Frame(root)
    container.pack(side="top", pady=(20, 0))

    # Main Title
    tk.Label(container, text="Generate Excel File",
             font=("Segoe UI", 12, "bold"), anchor="center"
             ).grid(row=0, column=0, pady=10)
    

    # Input Table for Document Details
    tk.Button(container, text="Generate Excel", bg="green", fg="white",
              activebackground="green", activeforeground="white",
              font=("Times New Roman", 12, "bold"), padx=12, pady=6,
              command=on_generate).grid(row=1, column=0, pady=20)

    _nav_buttons(root, open_interface_05, None)
    return root

def run():
    Interface_01().mainloop()

if __name__ == "__main__":
    run()

