"""Small firmware dialog, using the app's chosen theme."""
from pathlib import Path
import os
from tkinter import filedialog
import customtkinter as ctk
import onboard
from firmware import FirmwareManager, write_json

class FirmwareDialog:
    def __init__(self,app,palette):
        self.app=app; self.manager=app.firmware_manager; self.job=None; self.image=None
        self.window=ctk.CTkToplevel(app.root)
        w=self.window; w.title('Firmware'); w.geometry('600x515'); w.resizable(False,False)
        w.configure(fg_color=palette['bg']); w.transient(app.root)
        w.grid_columnconfigure(0,weight=1)
        def label(text,row,size=13):
            result=ctk.CTkLabel(w,text=text,text_color=palette['text'],font=('Segoe UI',size),anchor='w',justify='left',wraplength=540)
            result.grid(row=row,column=0,sticky='ew',padx=28,pady=(14,0)); return result
        label('Firmware',0,23)
        label('Build a file from your current colours, white effect and keys.\nHold Start for colours or Select for keyboard mode (5 seconds).\nMatched to the supported Pico guitar configuration.',1)
        row=ctk.CTkFrame(w,fg_color='transparent'); row.grid(row=2,column=0,sticky='ew',padx=28,pady=(22,0))
        self.controls=[]
        def button(parent,text,command,secondary=False,width=150):
            result=app.btn(parent,text,command,secondary=secondary,width=width)
            result.configure(fg_color=palette['bg'] if secondary else palette['accent'],
                text_color=palette['text'] if secondary else '#FFFFFF',
                hover_color=palette['hover'] if secondary else palette['accent_hover'])
            return result
        for text,command in [('Generate file',self.generate),('Choose file',self.choose)]:
            b=button(row,text,command,secondary=True,width=150); b.pack(side='left',padx=(0,12)); self.controls.append(b)
        self.path_label=label('No file selected',3,12)
        row=ctk.CTkFrame(w,fg_color='transparent'); row.grid(row=4,column=0,sticky='ew',padx=28,pady=(20,0))
        for text,command in [('Install firmware',lambda:self.launch('install')),('Undo firmware',lambda:self.launch('undo'))]:
            b=button(row,text,command,width=160); b.pack(side='left',padx=(0,12)); self.controls.append(b)
        label('Install verifies a full backup first. Undo restores the firmware\nand settings from before your last installation. Keep USB connected.',5,12)
        self.status=label('Ready',6,12)
        button(w,'Open backups',self.open_backups,secondary=True,width=130).grid(row=7,column=0,sticky='w',padx=28,pady=(16,22))
        self.set_busy(app.firmware_busy)
    def set_busy(self,busy):
        for button in self.controls: button.configure(state='disabled' if busy else 'normal')
    def generate(self):
        a=self.app
        if not a.commit_all(): self.status.configure(text='Fix the highlighted hex colour first.'); return
        path=filedialog.asksaveasfilename(parent=self.window,title='Generate firmware',defaultextension='.uf2',initialfile='FretGlow-custom.uf2',filetypes=[('Pico firmware','*.uf2')])
        if not path: return
        try:
            settings=onboard.encode(a.colours,a.brightness.get(),a.white_mode.get(),[v.get() for v in a.bindings])
            self.image=self.manager.generate(settings,path); self.path_label.configure(text=str(self.image))
            self.status.configure(text='File generated. Install it here or copy it to RPI-RP2 manually.')
        except Exception as error: self.status.configure(text=str(error))
    def choose(self):
        path=filedialog.askopenfilename(parent=self.window,title='Choose generated firmware',filetypes=[('Pico firmware','*.uf2')])
        if path: self.image=Path(path); self.path_label.configure(text=path)
    def launch(self,action):
        a=self.app
        if a.firmware_busy or a.pending: self.status.configure(text='Please wait for the current operation.'); return
        if action=='install' and not self.image: self.status.configure(text='Generate or choose a firmware file first.'); return
        try: job=self.manager.prepare(action,self.image)
        except Exception as error: self.status.configure(text=str(error)); return
        a.active=False; a.stop_keyboard(); a.firmware_busy=True; self.set_busy(True)
        def start():
            try: a.guitar.close()
            except Exception: pass # Undo can also start while the guitar is in recovery.
            try: self.manager.start(job)
            except Exception as error:
                write_json(job.with_name('state.json'),dict(status='failed',message=str(error)))
            return 'Firmware helper started'
        a.pending=a.pool.submit(start)
        a.after_job=lambda:a.watch_firmware(job)
        a.status.set('Preparing firmware transfer…')
    def open_backups(self):
        self.manager.root.mkdir(parents=True,exist_ok=True); os.startfile(str(self.manager.root))
