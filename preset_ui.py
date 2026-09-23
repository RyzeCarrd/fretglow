"""Local preset library with draggable guitar slots."""
import customtkinter as ctk
from app_icon import set_icon

class PresetDialog:
    def __init__(self,app,palette):
        self.app=app;self.library=app.library;self.p=palette;self.selected=None;self.drag=None;self.targets=[]
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('Presets');w.geometry('860x680');w.minsize(820,640);w.transient(app.root);w.configure(fg_color=palette['bg']);set_icon(w)
        w.grid_columnconfigure(0,weight=1);w.grid_columnconfigure(1,weight=1);w.grid_rowconfigure(2,weight=1)
        self.label(w,'Presets',24,True).grid(row=0,column=0,columnspan=2,sticky='w',padx=24,pady=(20,4))
        self.label(w,'Save your current colours, keys and press effect together.').grid(row=1,column=0,columnspan=2,sticky='w',padx=24,pady=(0,16))
        left=ctk.CTkFrame(w,fg_color=palette['panel']);left.grid(row=2,column=0,sticky='nsew',padx=(24,8));left.grid_columnconfigure(0,weight=1);left.grid_rowconfigure(3,weight=1)
        self.label(left,'Saved on this PC',17,True).grid(row=0,column=0,sticky='w',padx=16,pady=(16,8))
        self.name=ctk.CTkEntry(left,placeholder_text='New preset name',fg_color=palette['bg'],text_color=palette['text'],border_color=palette['line']);self.name.grid(row=1,column=0,sticky='ew',padx=16,pady=(0,8))
        self.button(left,'Save current as preset',self.save_current).grid(row=2,column=0,sticky='ew',padx=16,pady=(0,12))
        self.list=ctk.CTkScrollableFrame(left,fg_color='transparent');self.list.grid(row=3,column=0,sticky='nsew',padx=8,pady=(0,8))
        actions=ctk.CTkFrame(left,fg_color='transparent');actions.grid(row=4,column=0,sticky='ew',padx=16,pady=(0,16))
        self.button(actions,'Load selected',self.load,True,width=135).pack(side='left')
        self.button(actions,'Replace selected',self.replace,True,width=135).pack(side='right')
        right=ctk.CTkFrame(w,fg_color=palette['panel']);right.grid(row=2,column=1,sticky='nsew',padx=(8,24));right.grid_columnconfigure(0,weight=1)
        self.label(right,'On the guitar',17,True).grid(row=0,column=0,sticky='w',padx=16,pady=(16,8))
        self.label(right,'Drag a saved preset into a slot.\nOr select it and click Assign.',wrap=310).grid(row=1,column=0,sticky='w',padx=16,pady=(0,14))
        self.slot_area=ctk.CTkFrame(right,fg_color='transparent');self.slot_area.grid(row=2,column=0,sticky='ew',padx=12);self.slot_area.grid_columnconfigure(0,weight=1)
        self.start=ctk.StringVar(value=str(self.library.start));self.save_button=self.button(right,'Save slots to guitar',self.save_slots);self.save_button.grid(row=3,column=0,sticky='ew',padx=16,pady=(16,12))
        self.label(right,'The startup slot loads when you plug in.\nHold both bottom buttons together for\n5 seconds to cycle 1 → 2 → 3 → 1.\nEmpty slots are skipped.',wrap=325).grid(row=4,column=0,sticky='w',padx=16,pady=(0,16))
        self.status=self.label(w,'Slots are saved on this PC until you click Save slots to guitar.',wrap=810);self.status.grid(row=3,column=0,columnspan=2,sticky='ew',padx=24,pady=16)
        self.refresh()
    def label(self,parent,text,size=12,bold=False,wrap=0):return ctk.CTkLabel(parent,text=text,font=('Segoe UI',size,'bold' if bold else 'normal'),text_color=self.p['text'] if bold else self.p['muted'],anchor='w',justify='left',wraplength=wrap)
    def button(self,parent,text,command,secondary=False,**kwargs):return ctk.CTkButton(parent,text=text,command=command,fg_color=self.p['line'] if secondary else self.p['accent'],hover_color=self.p['hover'] if secondary else self.p['accent_hover'],text_color=self.p['text'] if secondary else '#FFFFFF',**kwargs)
    def attempt(self,action):
        if self.app.firmware_busy:self.status.configure(text='Wait for the guitar update to finish.');return
        try:action()
        except Exception as error:self.status.configure(text=str(error))
    def save_current(self):
        def action():
            self.selected=self.library.add(self.name.get(),self.app.current_settings());self.name.delete(0,'end');self.refresh();self.status.configure(text='Preset saved on this PC. Drag it into a slot to take it with you.')
        self.attempt(action)
    def replace(self):
        def action():
            if not self.selected:raise ValueError('Select a saved preset first.')
            settings=self.app.current_settings();item=self.library.get(self.selected);old=item['settings'];item['settings']=settings
            try:self.library.save()
            except Exception:item['settings']=old;raise
            self.refresh();self.status.configure(text='Preset replaced on this PC. Save slots to guitar to update the controller too.')
        self.attempt(action)
    def load(self):
        if self.selected:self.app.load_preset(self.library.get(self.selected)['settings']);self.status.configure(text='Loaded in the main window. The guitar has not been saved yet.')
        else:self.status.configure(text='Select a saved preset first.')
    def assign(self,slot,id=None):
        def action():
            selected=id or self.selected
            if not selected:raise ValueError('Select a saved preset first.')
            self.library.assign(slot,selected);self.refresh();self.status.configure(text=f'Slot {slot+1} ready. Click Save slots to guitar to store it on the controller.')
        self.attempt(action)
    def clear(self,slot):
        def action():self.library.assign(slot,None);self.refresh();self.status.configure(text='Slot cleared on this PC. Save slots to guitar to update the controller.')
        self.attempt(action)
    def set_start(self):
        def action():
            old=self.library.start;self.library.start=int(self.start.get())
            try:self.library.save()
            except Exception:self.library.start=old;self.start.set(str(old));raise
        self.attempt(action)
    def save_slots(self):
        def action():
            data=self.library.bank();self.app.send_settings(data);self.status.configure(text='Saving slots. The result appears in the main window.')
        self.attempt(action)
    def begin(self,event,id):
        self.selected=id;self.drag=id;self.status.configure(text='Drag to a guitar slot, or click Load selected to edit.')
        for row,row_id in self.rows:row.configure(border_color=self.p['accent'] if row_id==id else self.p['line'])
    def target_at(self,event):
        for i,frame in enumerate(self.targets):
            x,y=frame.winfo_rootx(),frame.winfo_rooty()
            if x<=event.x_root<x+frame.winfo_width() and y<=event.y_root<y+frame.winfo_height():return i
        return None
    def motion(self,event):
        target=self.target_at(event)
        for i,frame in enumerate(self.targets):frame.configure(border_color=self.p['accent'] if i==target else self.p['line'])
    def drop(self,event):
        target=self.target_at(event);id=self.drag;self.drag=None
        if id and target is not None:self.assign(target,id)
        else:
            for frame in self.targets:frame.configure(border_color=self.p['line'])
    def refresh(self):
        self.start.set(str(self.library.start))
        for widget in self.list.winfo_children():widget.destroy()
        self.rows=[]
        if not self.library.items:self.label(self.list,'Save a preset above to get started.',wrap=280).pack(pady=20)
        for item in self.library.items:
            row=ctk.CTkFrame(self.list,fg_color=self.p['bg'],border_width=1,border_color=self.p['accent'] if item['id']==self.selected else self.p['line']);row.pack(fill='x',pady=4);self.rows.append((row,item['id']))
            name=self.label(row,item['name'],14,True,280);name.pack(anchor='w',padx=12,pady=(10,4));colours=ctk.CTkFrame(row,fg_color='transparent');colours.pack(anchor='w',padx=12,pady=(0,10))
            handles=[row,name,colours]
            for colour in item['settings']['colours']:
                chip=ctk.CTkLabel(colours,text='',width=32,height=10,fg_color=colour,corner_radius=3);chip.pack(side='left',padx=(0,4));handles.append(chip)
            for widget in handles:
                widget.bind('<ButtonPress-1>',lambda e,id=item['id']:self.begin(e,id));widget.bind('<B1-Motion>',self.motion);widget.bind('<ButtonRelease-1>',self.drop)
        for widget in self.slot_area.winfo_children():widget.destroy()
        self.targets=[]
        for i,id in enumerate(self.library.slots):
            frame=ctk.CTkFrame(self.slot_area,fg_color=self.p['bg'],border_width=1,border_color=self.p['line']);frame.grid(row=i,column=0,sticky='ew',pady=4);self.targets.append(frame)
            self.label(frame,f'{i+1}   '+(self.library.get(id)['name'] if id else 'Empty slot'),14,True,300).pack(anchor='w',padx=12,pady=(10,8))
            controls=ctk.CTkFrame(frame,fg_color='transparent');controls.pack(fill='x',padx=12,pady=(0,10))
            ctk.CTkRadioButton(controls,text='Startup',variable=self.start,value=str(i),command=self.set_start,state='normal' if id else 'disabled',width=92,font=('Segoe UI',11),text_color=self.p['text'],fg_color=self.p['accent'],hover_color=self.p['accent_hover']).pack(side='left')
            self.button(controls,'Assign',lambda i=i:self.assign(i),True,width=65,height=26).pack(side='left',padx=(8,5))
            self.button(controls,'Clear',lambda i=i:self.clear(i),True,width=55,height=26).pack(side='left')
