"""Themed HSV colour picker with a hex field."""
import colorsys
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
from app_icon import set_icon

class ColourPicker:
    def __init__(self,app,colour,title,callback,palette):
        self.callback=callback;self.colour=colour;self.palette=palette
        self.h,self.s,self.v=colorsys.rgb_to_hsv(*(int(colour[i:i+2],16)/255 for i in (1,3,5)))
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title(title);w.geometry('360x460');w.resizable(False,False);w.transient(app.root);w.configure(fg_color=palette['bg']);set_icon(w)
        ctk.CTkLabel(w,text=title,font=('Segoe UI',20,'bold'),text_color=palette['text']).pack(anchor='w',padx=24,pady=(20,14))
        self.canvas=tk.Canvas(w,width=310,height=190,highlightthickness=0,bd=0,cursor='crosshair');self.canvas.pack(padx=24)
        self.canvas.bind('<Button-1>',self.choose);self.canvas.bind('<B1-Motion>',self.choose)
        ctk.CTkLabel(w,text='Hue',text_color=palette['muted'],font=('Segoe UI',12)).pack(anchor='w',padx=24,pady=(12,0))
        self.hue=ctk.CTkSlider(w,from_=0,to=1,command=self.set_hue,progress_color=palette['accent'],button_color=palette['accent'],button_hover_color=palette['accent_hover'],fg_color=palette['line']);self.hue.set(self.h);self.hue.pack(fill='x',padx=24,pady=(4,12))
        row=ctk.CTkFrame(w,fg_color='transparent');row.pack(fill='x',padx=24)
        self.swatch=ctk.CTkFrame(row,width=48,height=36,fg_color=colour,corner_radius=8);self.swatch.pack(side='left')
        self.hex=tk.StringVar(value=colour);self.entry=ctk.CTkEntry(row,textvariable=self.hex,width=150,height=36,font=('Consolas',14),fg_color=palette['panel'],text_color=palette['text'],border_color=palette['line']);self.entry.pack(side='right');self.entry.bind('<Return>',self.from_hex);self.entry.bind('<FocusOut>',self.from_hex)
        self.message=ctk.CTkLabel(w,text='Drag to choose, or enter a hex colour.',font=('Segoe UI',11),text_color=palette['muted']);self.message.pack(pady=(8,8))
        row=ctk.CTkFrame(w,fg_color='transparent');row.pack(fill='x',padx=24)
        ctk.CTkButton(row,text='Cancel',width=130,command=w.destroy,fg_color=palette['line'],hover_color=palette['hover'],text_color=palette['text']).pack(side='left')
        ctk.CTkButton(row,text='Use colour',width=130,command=self.accept,fg_color=palette['accent'],hover_color=palette['accent_hover']).pack(side='right')
        self.draw();w.grab_set()
    def draw(self):
        pixels=[tuple(round(c*255) for c in colorsys.hsv_to_rgb(self.h,x/309,1-y/189)) for y in range(190) for x in range(310)]
        picture=Image.new('RGB',(310,190));picture.putdata(pixels);self.picture=ImageTk.PhotoImage(picture,master=self.window)
        self.canvas.delete('all');self.canvas.create_image(0,0,anchor='nw',image=self.picture);self.marker()
    def marker(self):
        self.canvas.delete('marker');x=self.s*309;y=(1-self.v)*189
        self.canvas.create_oval(x-6,y-6,x+6,y+6,outline='black',width=3,tags='marker');self.canvas.create_oval(x-5,y-5,x+5,y+5,outline='white',width=1,tags='marker')
    def update(self):
        self.colour='#'+''.join(f'{round(c*255):02X}' for c in colorsys.hsv_to_rgb(self.h,self.s,self.v));self.hex.set(self.colour);self.swatch.configure(fg_color=self.colour);self.entry.configure(border_color=self.palette['line']);self.message.configure(text='Drag to choose, or enter a hex colour.');self.marker()
    def choose(self,event):self.s=max(0,min(1,event.x/309));self.v=max(0,min(1,1-event.y/189));self.update()
    def set_hue(self,value):self.h=value;self.draw();self.update()
    def from_hex(self,event=None):
        value=self.hex.get().strip().lstrip('#')
        if len(value)==3:value=''.join(c*2 for c in value)
        try:
            if len(value)!=6:raise ValueError()
            rgb=[int(value[i:i+2],16)/255 for i in (0,2,4)]
        except ValueError:self.entry.configure(border_color='#D66A70');self.message.configure(text='Enter a hex colour, such as #A879E8.');return False
        self.h,self.s,self.v=colorsys.rgb_to_hsv(*rgb);self.hue.set(self.h);self.draw();self.update();return True
    def accept(self):
        if self.from_hex():self.callback(self.colour);self.window.destroy()
