from pathlib import Path
import tkinter as tk

ICON=Path(__file__).resolve().parent/'assets/fretglow.ico'

def set_icon(window):
    def apply():
        try:window.iconbitmap(str(ICON))
        except tk.TclError:pass
    # CustomTkinter applies its default icon shortly after creating a window.
    window.after(250,apply)
