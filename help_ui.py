"""Getting-started guide and credits."""
from pathlib import Path
import customtkinter as ctk
from PIL import Image
from app_icon import set_icon

STEPS=[
    ('Connect your guitar',
     'Plug the guitar into this PC and click Connect.\n\nIf it is in keyboard mode, hold the button above the bottom Start button for 5 seconds to return to controller mode.'),
    ('Choose your lighting',
     'Click a fret colour, pick anywhere in the rainbow and click Use colour. Every fret can be any colour. The small colour squares are shortcuts; Light / dark adjusts the shade. Hex codes work too.\n\nThe press colour is what appears when you press a fret.\n\nOff: keep the normal colour.\nWhile held: show the press colour until you let go.\nToggle: press once to change colour; press again to go back.\n\nPreview tries your lighting. End preview resumes the saved lighting.'),
    ('Record your keys',
     'Click a key beside any fret or button, then press one key on your PC keyboard. Clear binding removes that assignment.\n\nThe Keyboard switch types while the app is open. F8 stops this app mode.\n\nHold the button above the bottom Start button for 5 seconds to use the saved keys without the app. Hold it again to return to controller mode.'),
    ('Save custom presets',
     'Open My presets. Enter a name and click Save current as preset. This saves your colours, press effect, brightness and keys together.\n\nDrag saved presets into the three guitar slots, or select a preset and click Assign. Choose a Startup slot, then click Save slots to guitar.\n\nHold both bottom buttons together for 5 seconds to move to the next preset: 1, 2, 3, then back to 1. Empty slots are skipped. Release both before repeating. Reconnecting loads the Startup slot.\n\nLoad selected opens a preset in the main window. After editing it, use Replace selected, then Save slots to guitar.'),
    ('Save in the right place',
     'Save to guitar in the main window updates the active guitar slot with the colours and keys currently on screen. The other slots stay as they are.\n\nSave slots to guitar in My presets sends the whole three-slot arrangement and activates the Startup slot.\n\nSave on this PC only remembers the app\'s current choices. Named presets are saved separately when you add or replace them.\n\nSaved guitar slots work without the app, including on another PC. Hold only the bottom Start button for 5 seconds to switch between the selected preset and original lighting.'),
    ('Updates and Undo',
     'Firmware is the software inside your guitar. Install an update once to add support for three slots.\n\nOpen Guitar setup and click Install update. It includes your assigned slots, or your current settings if no slots are assigned, and saves a recovery backup first.\n\nUndo last update restores the previous software AND the settings from that backup. Keep USB connected until it finishes.\n\nManual file options lets you export a firmware file or install one yourself.'),
]

class Tutorial:
    def __init__(self,app,palette):
        self.index=0
        self.window=ctk.CTkToplevel(app.root);w=self.window
        w.title('Tutorial');w.geometry('620x480');w.resizable(False,False);w.transient(app.root);w.configure(fg_color=palette['bg'])
        set_icon(w)
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
        set_icon(w)
        with Image.open(Path(__file__).resolve().parent/'assets/harley.png') as picture:
            self.picture=ctk.CTkImage(light_image=picture.copy(),dark_image=picture.copy(),size=(100,124))
        ctk.CTkLabel(w,text='',image=self.picture).pack(pady=(28,20))
        ctk.CTkLabel(w,text='Made by Harley',font=('Segoe UI',24,'bold'),text_color=palette['text']).pack()
        ctk.CTkLabel(w,text='discord: harleydabrit',font=('Segoe UI',15),text_color=palette['muted']).pack(pady=(8,22))
        ctk.CTkButton(w,text='Close',command=w.destroy,width=110,fg_color=palette['accent'],hover_color=palette['accent_hover']).pack()
