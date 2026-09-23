"""Guided guitar update, with manual exports kept optional."""
from pathlib import Path
import os
from tkinter import filedialog
import customtkinter as ctk
import onboard
from app_icon import set_icon
from firmware import write_json

class FirmwareDialog:
    def __init__(self,app,palette):
        self.app=app;self.manager=app.firmware_manager;self.image=None;self.controls=[]
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('Guitar setup');w.geometry('640x530');w.resizable(False,False);w.transient(app.root);w.configure(fg_color=palette['bg']);w.grid_columnconfigure(0,weight=1)
        set_icon(w)
        def label(parent,text,size=13,muted=False):
            return ctk.CTkLabel(parent,text=text,text_color=palette['muted' if muted else 'text'],font=('Segoe UI',size),anchor='w',justify='left',wraplength=570)
        def button(parent,text,action,secondary=False,width=165):
            b=ctk.CTkButton(parent,text=text,command=action,width=width,height=35,corner_radius=8,font=('Segoe UI',12),fg_color=palette['line'] if secondary else palette['accent'],hover_color=palette['hover'] if secondary else palette['accent_hover'],text_color=palette['text'] if secondary else '#FFFFFF')
            self.controls.append(b);return b
        label(w,'Guitar setup',24).grid(row=0,column=0,sticky='ew',padx=28,pady=(24,12))
        label(w,'Firmware is the software inside your guitar. Install an update to add features. For everyday colours and keys, use Save to guitar in the main window.').grid(row=1,column=0,sticky='ew',padx=28,pady=(0,20))
        button(w,'Install update',self.install_current).grid(row=2,column=0,sticky='w',padx=28)
        label(w,'Includes your assigned preset slots, or current settings if no slots are assigned. Saves a recovery backup first.',muted=True).grid(row=3,column=0,sticky='ew',padx=28,pady=(8,20))
        button(w,'Undo last update',lambda:self.launch('undo'),secondary=True).grid(row=4,column=0,sticky='w',padx=28)
        label(w,'Restores the previous software and the settings from its backup.',muted=True).grid(row=5,column=0,sticky='ew',padx=28,pady=(8,20))
        self.manual_button=button(w,'Manual file options',self.toggle_manual,secondary=True)
        self.manual_button.grid(row=6,column=0,sticky='w',padx=28)
        self.manual=ctk.CTkFrame(w,fg_color='transparent')
        button(self.manual,'Export file…',self.generate,secondary=True).pack(side='left',padx=(0,12))
        button(self.manual,'Install from file…',self.choose,secondary=True).pack(side='left')
        self.status=label(w,'Ready. Keep USB connected during an update.');self.status.grid(row=8,column=0,sticky='ew',padx=28,pady=(20,12))
        button(w,'Open backups',self.open_backups,secondary=True,width=130).grid(row=9,column=0,sticky='w',padx=28,pady=(0,24))
        self.set_busy(app.firmware_busy)
    def set_busy(self,busy):
        for b in self.controls:b.configure(state='disabled' if busy else 'normal')
    def settings(self):
        a=self.app
        if not a.commit_all():raise ValueError('Fix the highlighted hex colour in the main window first.')
        return a.firmware_settings()
    def install_current(self):
        if self.app.firmware_busy or self.app.pending:return
        try:
            self.image=self.manager.generate(self.settings(),self.manager.root/'generated/current-settings.uf2')
            self.app.save_profile()
        except Exception as error:self.status.configure(text=str(error));return
        self.launch('install')
    def toggle_manual(self):
        if self.manual.winfo_manager():self.manual.grid_remove();self.window.geometry('640x530')
        else:self.manual.grid(row=7,column=0,sticky='ew',padx=28,pady=(12,0));self.window.geometry('640x585')
    def generate(self):
        try:settings=self.settings()
        except Exception as error:self.status.configure(text=str(error));return
        path=filedialog.asksaveasfilename(parent=self.window,title='Export guitar firmware',defaultextension='.uf2',initialfile='FretGlow-custom.uf2',filetypes=[('Pico firmware','*.uf2')])
        if not path:return
        try:
            self.manager.generate(settings,path)
            self.status.configure(text='File exported. Your guitar has not been changed.')
        except Exception as error:self.status.configure(text=str(error))
    def choose(self):
        path=filedialog.askopenfilename(parent=self.window,title='Install an exported firmware file',filetypes=[('Pico firmware','*.uf2')])
        if path:self.image=Path(path);self.launch('install')
    def launch(self,action):
        a=self.app
        if a.firmware_busy or a.pending:self.status.configure(text='Please wait for the current operation.');return
        try:job=self.manager.prepare(action,self.image)
        except Exception as error:self.status.configure(text=str(error));return
        a.active=False;a.stop_keyboard();a.firmware_busy=True;self.set_busy(True)
        def start():
            try:a.guitar.close()
            except Exception:pass
            try:self.manager.start(job)
            except Exception as error:write_json(job.with_name('state.json'),dict(status='failed',message=str(error)))
            return 'Update helper started'
        a.pending=a.pool.submit(start);a.after_job=lambda:a.watch_firmware(job)
        a.status.set('Preparing guitar update…');self.status.configure(text='Preparing guitar update…')
    def open_backups(self):
        self.manager.root.mkdir(parents=True,exist_ok=True);os.startfile(str(self.manager.root))
