"""Getting-started guide and credits."""
from pathlib import Path
import customtkinter as ctk
from PIL import Image

STEPS=[
    ('Connect your guitar',
     'Plug the guitar into this PC and click Connect.\n\nIf it is in keyboard mode, hold Select / Back for 5 seconds to return to controller mode first.'),
    ('Choose your lighting',
     'Click a fret colour or type its hex code.\n\nPress effect changes a fret to the effect colour: While held lasts until you let go; Toggle stays until you press again; Off disables it. The effect can be any colour.\n\nPreview tries your settings while the app is open. End preview returns control to the guitar.'),
    ('Record your keys',
     'Click a key beside any fret or button, then press one key on your PC keyboard. Clear binding removes that assignment.\n\nThe Keyboard switch makes the app send those keys while it is open. F8 stops this app mode.\n\nWith updated guitar software, hold Select / Back for 5 seconds to use the saved keys without the app. Hold it again to return to controller mode.'),
    ('Save in the right place',
     'Save to guitar stores your colours, press effect and keys inside the controller. They work after unplugging it, including on another PC. This is the button to use for everyday changes.\n\nSave on this PC only remembers your choices in this app. It does not change what the guitar remembers.\n\nAfter saving to the guitar, hold Start for 5 seconds to switch between your saved colours and the original lighting. Release before repeating.'),
    ('Updates and Undo',
     'Firmware means the software running inside your guitar. Installing an update adds controller features; it is different from saving colours.\n\nOpen Guitar setup and click Install update. The app includes your current settings, saves a recovery backup, installs and checks the update. You do not have to generate a file first.\n\nUndo last update restores the previous software AND the settings from that backup. Keep USB connected during either operation. Manual file options are there if you want to export a file or install one yourself.'),
]

class Tutorial:
    def __init__(self,app,palette):
        self.index=0
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('Tutorial');w.geometry('620x480');w.resizable(False,False);w.transient(app.root);w.configure(fg_color=palette['bg'])
        w.grid_columnconfigure(0,weight=1);w.grid_rowconfigure(2,weight=1)
        self.step=ctk.CTkLabel(w,text='',text_color=palette['muted'],font=('Segoe UI',12),anchor='w');self.step.grid(row=0,column=0,sticky='ew',padx=28,pady=(24,8))
        self.title=ctk.CTkLabel(w,text='',text_color=palette['text'],font=('Segoe UI',23,'bold'),anchor='w');self.title.grid(row=1,column=0,sticky='ew',padx=28)
        self.body=ctk.CTkLabel(w,text='',text_color=palette['text'],font=('Segoe UI',14),anchor='nw',justify='left',wraplength=555);self.body.grid(row=2,column=0,sticky='nsew',padx=28,pady=20)
        buttons=ctk.CTkFrame(w,fg_color='transparent');buttons.grid(row=3,column=0,sticky='ew',padx=28,pady=(0,24))
        self.back=ctk.CTkButton(buttons,text='Back',width=100,command=lambda:self.move(-1),fg_color=palette['accent'],hover_color=palette['accent_hover']);self.back.pack(side='left')
        self.next=ctk.CTkButton(buttons,text='Next',width=100,command=lambda:self.move(1),fg_color=palette['accent'],hover_color=palette['accent_hover']);self.next.pack(side='right')
        self.show()
    def show(self):
        title,body=STEPS[self.index];self.title.configure(text=title);self.body.configure(text=body)
        self.step.configure(text=f'{self.index+1} of {len(STEPS)}');self.back.configure(state='disabled' if self.index==0 else 'normal')
        self.next.configure(text='Done' if self.index==len(STEPS)-1 else 'Next')
    def move(self,amount):
        if self.index+amount>=len(STEPS):self.window.destroy();return
        self.index=max(0,self.index+amount);self.show()

class Credits:
    def __init__(self,app,palette):
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('Credits');w.geometry('400x365');w.resizable(False,False);w.transient(app.root);w.configure(fg_color=palette['bg'])
        with Image.open(Path(__file__).resolve().parent/'assets/harley.png') as picture:
            self.picture=ctk.CTkImage(light_image=picture.copy(),dark_image=picture.copy(),size=(100,124))
        ctk.CTkLabel(w,text='',image=self.picture).pack(pady=(28,20))
        ctk.CTkLabel(w,text='Made by Harley',font=('Segoe UI',24,'bold'),text_color=palette['text']).pack()
        ctk.CTkLabel(w,text='discord: harleydabrit',font=('Segoe UI',15),text_color=palette['muted']).pack(pady=(8,22))
        ctk.CTkButton(w,text='Close',command=w.destroy,width=110,fg_color=palette['accent'],hover_color=palette['accent_hover']).pack()
