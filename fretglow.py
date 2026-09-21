"""FretGlow: temporary Santroller RGB control and Windows keyboard mapping."""
import ctypes as ct
from ctypes import wintypes as wt
import json
import os
from pathlib import Path
import re
import sys
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
from concurrent.futures import ThreadPoolExecutor
import customtkinter as ctk

import onboard
import firmware
import keybinds
import brotli
import usb.core
import usb.util
import libusb_package

NAMES = ['Green', 'Red', 'Yellow', 'Blue', 'Orange']
CLASSIC = ['#30df72', '#ff4168', '#ffe34c', '#428aff', '#ff9438']
MASKS = [0x1000, 0x2000, 0x8000, 0x4000, 0x0100, 0x0001, 0x0002, 0x0010, 0x0020]
CONTROLS = NAMES + ['Strum up', 'Strum down', 'Start', 'Select']
DEFAULT_KEYS = ['A', 'S', 'K', 'L', 'M', 'Up', 'Down', 'Enter', 'Backspace']
KEYS = keybinds.VK

def fields(data):
    p = 0
    def varint():
        nonlocal p
        v = 0
        for shift in range(0, 70, 7):
            if p >= len(data): raise ValueError('Incomplete controller configuration')
            b = data[p]; p += 1; v |= (b & 127) << shift
            if b < 128: return v
        raise ValueError('Invalid controller configuration')
    while p < len(data):
        tag = varint(); wire = tag & 7
        if not tag >> 3: raise ValueError('Invalid configuration field')
        if wire == 0: value = varint()
        elif wire in (1, 2, 5):
            size = varint() if wire == 2 else (8 if wire == 1 else 4)
            if p + size > len(data): raise ValueError('Incomplete configuration field')
            value = data[p:p+size]; p += size
        else: raise ValueError('Unsupported configuration encoding')
        yield tag >> 3, value

def light_config(data):
    all_fields = list(fields(data)); cfg = dict(all_fields)
    # Only accept the APA102 legacy configuration verified for this guitar.
    if cfg.get(1) not in range(1, 7) or cfg.get(10) != 5 or 48 not in cfg:
        raise ValueError('This app supports your five-light APA102 Santroller setup. This configuration differs.')
    mapping = {}
    for tag, value in all_fields:
        if tag != 7: continue
        for subtype, payload in fields(value):
            if subtype != 115: continue
            f = dict(fields(payload)); fret = f.get(5, 0)
            indices = f.get(6, b'')
            if fret in range(5) and isinstance(indices, bytes) and len(indices) == 1:
                mapping[fret] = indices[0] - 1
    if set(mapping) != set(range(5)) or set(mapping.values()) != set(range(5)):
        raise ValueError('Could not identify the five fret lights. No lights were changed.')
    return [mapping[i] for i in range(5)]

def packet(index, colour, percent):
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', colour): raise ValueError('Use a colour such as #FF0099')
    if not 0 <= percent <= 100 or not 0 <= index < 5: raise ValueError('Invalid light setting')
    rgb = [int(colour[i:i+2], 16) for i in (1, 3, 5)]
    brightness = round(percent * 31 / 100)
    # All-zero RGB means release override in this firmware. Use zero brightness
    # with a nonzero channel for an actual black/off setting.
    if not any(rgb) or brightness == 0: return bytes([index, 0, 1, 0, 0])
    return bytes([index, brightness, *rgb])

class Guitar:
    def __init__(self): self.dev = None; self.interface = None; self.mapping = []; self.changed = False; self.last_packets = {}; self.onboard = False; self.preview = False
    def connect(self):
        try: self.close()
        except RuntimeError: pass  # Replugging already clears temporary overrides.
        devices = list(usb.core.find(find_all=True, idVendor=0x1209, idProduct=0x2882,
                                    backend=libusb_package.get_libusb1_backend()))
        if len(devices) != 1: raise RuntimeError('Connect one Santroller guitar, then click Connect.')
        d = devices[0]
        # WinUSB configuration interface in the verified XInput layout.
        candidates = [i for i in d[0] if (i.bInterfaceClass, i.bInterfaceSubClass, i.bInterfaceProtocol) == (255, 93, 2)]
        if len(candidates) != 1: raise RuntimeError('The guitar must be in its original Windows controller mode.')
        interface = candidates[0].bInterfaceNumber
        try:
            usb.util.claim_interface(d, interface)
            board = bytes(d.ctrl_transfer(0xa1, 0x36, 0, interface, 64, timeout=700)).rstrip(b'\0')
            if board != b'pico': raise RuntimeError('This controller is not the expected Pico guitar.')
            compressed = bytearray()
            for offset in range(0, 65536, 64):
                chunk = bytes(d.ctrl_transfer(0xa1, 0x34, offset, interface, 64, timeout=700))
                compressed.extend(chunk)
                if len(chunk) < 64: break
            else: raise RuntimeError('Controller configuration is too large.')
            self.mapping = light_config(brotli.decompress(compressed))
        except Exception:
            usb.util.dispose_resources(d); raise
        self.dev = d; self.interface = interface; self.last_packets.clear()
        self.onboard=False; self.preview=False
        try: onboard.info(d,interface); self.onboard=True
        except (usb.core.USBError,RuntimeError): pass
        return 'Connected · Santroller Pico · 5 RGB frets'
    def write(self, data):
        if self.dev is None: raise RuntimeError('Connect your guitar first.')
        sent = self.dev.ctrl_transfer(0x21, 0x41, 0, self.interface, data, timeout=700)
        if sent != len(data): raise RuntimeError('The guitar did not accept the complete light command.')
    def apply(self, colours, brightness):
        if len(colours) != 5 or len(self.mapping) != 5: raise RuntimeError('Connect your guitar first.')
        packets = [packet(i, c, brightness) for i, c in zip(self.mapping, colours)]
        if self.onboard and not self.preview:
            self.dev.ctrl_transfer(0x21,0x74,0,self.interface,bytes([1]),timeout=700); self.preview=True
        self.changed = True
        for data in packets:
            if self.last_packets.get(data[0]) != data:
                self.write(data); self.last_packets[data[0]] = data
        return 'Colours applied to your guitar'
    def restore(self):
        if self.dev and self.changed:
            errors = []
            for i in self.mapping:
                try: self.write(bytes([i, 0, 0, 0, 0]))
                except Exception as e: errors.append(e)
            if errors: raise RuntimeError('Could not restore lights. Reconnect the USB cable to restore them.')
            self.changed = False
            self.last_packets.clear()
        if self.dev and self.onboard:
            self.dev.ctrl_transfer(0x21,0x74,0,self.interface,bytes([0]),timeout=700); self.preview=False
            return 'Guitar lighting resumed'
        return 'Original guitar lighting restored'
    def push(self, data):
        if not self.dev: raise RuntimeError('Connect your guitar first.')
        if not self.onboard: raise RuntimeError('This guitar needs the FretGlow firmware update before saving on the guitar.')
        result=onboard.push(self.dev,self.interface,data)
        self.changed=False; self.preview=False; self.last_packets.clear()
        return result
    def close(self):
        try: self.restore()
        finally:
            if self.dev: usb.util.dispose_resources(self.dev)
            self.dev = None

class Gamepad(ct.Structure):
    _fields_ = [('buttons', wt.WORD), ('lt', ct.c_ubyte), ('rt', ct.c_ubyte),
                ('lx', ct.c_short), ('ly', ct.c_short), ('rx', ct.c_short), ('ry', ct.c_short)]
class State(ct.Structure): _fields_ = [('packet', wt.DWORD), ('pad', Gamepad)]
class Vibration(ct.Structure): _fields_ = [('left', wt.WORD), ('right', wt.WORD)]
class Caps(ct.Structure): _fields_ = [('type', ct.c_ubyte), ('subtype', ct.c_ubyte), ('flags', wt.WORD), ('pad', Gamepad), ('vibration', Vibration)]
class KeyInput(ct.Structure): _fields_ = [('vk', wt.WORD), ('scan', wt.WORD), ('flags', wt.DWORD), ('time', wt.DWORD), ('extra', ct.c_size_t)]
class MouseInput(ct.Structure): _fields_ = [('dx', wt.LONG), ('dy', wt.LONG), ('data', wt.DWORD), ('flags', wt.DWORD), ('time', wt.DWORD), ('extra', ct.c_size_t)]
class InputUnion(ct.Union): _fields_ = [('ki', KeyInput), ('mi', MouseInput)]
class Input(ct.Structure): _fields_ = [('type', wt.DWORD), ('u', InputUnion)]

class Keyboard:
    def __init__(self, sender=None):
        self.x = ct.WinDLL('xinput1_4'); self.user = ct.WinDLL('user32', use_last_error=True)
        self.user.SendInput.argtypes = [wt.UINT, ct.POINTER(Input), ct.c_int]
        self.user.SendInput.restype = wt.UINT
        self.sender = sender or self.send; self.held = set(); self.slot = None
    def send(self, vk, down):
        scan = keybinds.SCAN[vk]
        flags = 8 | (0 if down else 2) | (1 if scan & 0xff00 else 0)
        event = Input(type=1, u=InputUnion(ki=KeyInput(scan=scan & 0xff, flags=flags)))
        if self.user.SendInput(1, ct.byref(event), ct.sizeof(Input)) != 1:
            raise RuntimeError('Windows blocked keyboard input. Run the target game normally, without administrator mode.')
    def find(self):
        slots = []
        for i in range(4):
            c = Caps()
            if self.x.XInputGetCapabilities(i, 0, ct.byref(c)) == 0 and c.subtype in (6, 7, 11): slots.append(i)
        if len(slots) != 1: raise RuntimeError('Keyboard mode needs exactly one connected XInput guitar.')
        self.slot = slots[0]
    def transition(self, buttons, bindings):
        wanted = {KEYS[key] for mask, key in zip(MASKS, bindings) if buttons & mask and KEYS[key]}
        for vk in self.held - wanted:
            self.sender(vk, False); self.held.remove(vk)
        for vk in wanted - self.held:
            self.sender(vk, True); self.held.add(vk)
    def poll(self, bindings):
        buttons = self.read_buttons()
        self.transition(buttons, bindings)
        return buttons
    def read_buttons(self):
        s = State()
        if self.slot is None or self.x.XInputGetState(self.slot, ct.byref(s)) != 0:
            self.release(); raise RuntimeError('Guitar disconnected. Keyboard mode stopped.')
        return s.pad.buttons
    def release(self):
        errors = []
        for vk in list(self.held):
            try: self.sender(vk, False); self.held.remove(vk)
            except Exception as e: errors.append(e)
        if errors: raise errors[0]

THEMES = {
    'Graphite': dict(bg=('#F2F2F3','#171719'),panel=('#FFFFFF','#232326'),text=('#27272B','#EEEEF0'),muted=('#75757D','#AAAAB2'),accent=('#51515D','#60606F'),line=('#E1E1E5','#39393F'),hover=('#E6E6EA','#323239'),accent_hover=('#41414E','#767687'),off=('#D2D2D8','#494952')),
    'Slate': dict(bg=('#EEF1F5','#151A24'),panel=('#FFFFFF','#202938'),text=('#263249','#EDF2FF'),muted=('#68788F','#A4B3CD'),accent=('#3D64A9','#416DBB'),line=('#DCE3EC','#334259'),hover=('#E1E8F3','#2C3B52'),accent_hover=('#30538F','#5481D1'),off=('#C9D3E1','#42516B')),
    'Violet': dict(bg=('#F3F0F7','#1B1722'),panel=('#FFFEFF','#292330'),text=('#382B43','#F4EDF9'),muted=('#807189','#B6A8C3'),accent=('#765193','#8760A8'),line=('#E6DEED','#42354D'),hover=('#EDE3F4','#3B2E46'),accent_hover=('#63417E','#9B72BD'),off=('#D9CCE2','#55435E')),
    'Sand': dict(bg=('#F4F0E9','#201B18'),panel=('#FFFCF7','#2E2722'),text=('#41362E','#F4EBE2'),muted=('#8C7B6D','#BBAB9C'),accent=('#856044','#966E4D'),line=('#E7DDD1','#493C31'),hover=('#EEE2D4','#403329'),accent_hover=('#715035','#AC805A'),off=('#D9CBBB','#5B4939')),
}
BASE_THEME = THEMES['Graphite']
BG=BASE_THEME['bg']; PANEL=BASE_THEME['panel']; FG=BASE_THEME['text']; MUTED=BASE_THEME['muted']; ACCENT=BASE_THEME['accent']; LINE=BASE_THEME['line']
HOVER=BASE_THEME['hover']; ACCENT_HOVER=BASE_THEME['accent_hover']; OFF=BASE_THEME['off']

def normalise_hex(value):
    value = value.strip().lstrip('#')
    if re.fullmatch(r'[0-9a-fA-F]{3}', value): value = ''.join(c*2 for c in value)
    if not re.fullmatch(r'[0-9a-fA-F]{6}', value): raise ValueError('Enter a 6-digit hex colour, such as #FF0099.')
    return '#' + value.upper()

def reactive_colours(colours, buttons, white_pressed, effect_colour='#FFFFFF'):
    return [effect_colour if white_pressed and buttons & mask else colour for mask, colour in zip(MASKS, colours)]

class WhiteEffect:
    def __init__(self): self.reset()
    def reset(self, buttons=0): self.previous=buttons; self.latched=0
    def update(self, buttons, mode):
        rising=buttons & ~self.previous & sum(MASKS[:5]); self.previous=buttons
        if mode=='Toggle': self.latched ^= rising; return self.latched
        self.latched=0
        return buttons if mode=='While held' else 0

class App:
    def __init__(self, root, profile=None, autoconnect=True):
        self.root = root; root.title('FretGlow'); root.geometry('1000x860'); root.minsize(940, 850)
        root.configure(fg_color=BG)
        self.guitar = Guitar(); self.keyboard = Keyboard(); self.pool = ThreadPoolExecutor(max_workers=1)
        self.pending = None; self.after_job = None; self.light_future = None; self.closing = False
        self.active = False; self.last_frame = None; self.dirty = False
        self.profile = profile or Path(os.environ['LOCALAPPDATA']) / 'FretGlow' / 'profile.json'
        self.firmware_manager=firmware.FirmwareManager(self.profile.parent/'firmware')
        self.firmware_busy=False; self.firmware_dialog=None
        self.tutorial=None;self.credits=None
        self.colours = CLASSIC.copy(); self.brightness = tk.IntVar(value=30)
        self.white_pressed = tk.BooleanVar(value=True); self.auto_apply = tk.BooleanVar(value=False)
        self.white_mode=tk.StringVar(value='While held'); self.effect=WhiteEffect()
        self.effect_colour='#FFFFFF'; self.effect_hex=tk.StringVar(value='#FFFFFF'); self.key_capture=None
        self.dark_mode = tk.BooleanVar(value=True)
        self.theme = tk.StringVar(value='Graphite')
        self.enabled = tk.BooleanVar(value=False); self.bindings = [tk.StringVar(value=k) for k in DEFAULT_KEYS]
        self.status = tk.StringVar(value='Ready'); self.connection = tk.StringVar(value='Not connected')
        self.save_state = tk.StringVar(value='Saved'); self.key_status = tk.StringVar(value='F8 to stop')
        self.load_profile(); ctk.set_appearance_mode('dark' if self.dark_mode.get() else 'light'); self.hexes = [tk.StringVar(value=c.upper()) for c in self.colours]
        root.grid_columnconfigure(0, weight=1); root.grid_rowconfigure(1, weight=1)
        header = ctk.CTkFrame(root, fg_color='transparent'); header.grid(row=0, column=0, sticky='ew', padx=30, pady=(26,20))
        self.label(header,'FretGlow',25,bold=True).pack(side='left')
        self.switch(header,'Dark mode',self.dark_mode,self.change_theme).pack(side='left',padx=(24,0))
        self.theme_menu=ctk.CTkOptionMenu(header,values=list(THEMES),variable=self.theme,command=self.select_theme,width=108,height=30,fg_color=LINE,button_color=LINE,button_hover_color=HOVER,text_color=FG,dropdown_fg_color=PANEL,dropdown_text_color=FG,dropdown_hover_color=HOVER,font=('Segoe UI',12))
        self.theme_menu.pack(side='left',padx=(6,0))
        self.btn(header,'Tutorial',self.open_tutorial,secondary=True,width=75).pack(side='left',padx=(14,6))
        self.btn(header,'Credits',self.open_credits,secondary=True,width=68).pack(side='left')
        self.btn(header,'Connect',self.connect,secondary=True,width=95).pack(side='right')
        self.label(header,'',12,MUTED,textvariable=self.connection).pack(side='right',padx=16)
        body=ctk.CTkFrame(root,fg_color='transparent'); body.grid(row=1,column=0,sticky='nsew',padx=30)
        body.grid_columnconfigure(0,weight=1); body.grid_columnconfigure(1,weight=0,minsize=310); body.grid_rowconfigure(0,weight=1)
        left=self.card(body); left.grid(row=0,column=0,sticky='nsew',padx=(0,18))
        left.grid_columnconfigure(1,weight=1)
        self.label(left,'Frets',20,bold=True).grid(row=0,column=0,columnspan=3,sticky='w',padx=24,pady=(20,4))
        self.label(left,'Colour and keyboard assignment',12,MUTED).grid(row=1,column=0,columnspan=3,sticky='w',padx=24,pady=(0,20))
        for col,title in enumerate(['FRET','HEX COLOUR','KEY']):
            self.label(left,title,10,MUTED,bold=True).grid(row=2,column=col,sticky='w',padx=(24 if col==0 else 10,10),pady=(0,6))
        self.swatches=[];self.hex_entries=[];self.combos=[]
        for i,name in enumerate(NAMES):
            r=i+3
            fret=ctk.CTkFrame(left,fg_color='transparent');fret.grid(row=r,column=0,sticky='w',padx=(24,12),pady=12)
            b=ctk.CTkButton(fret,text='',width=32,height=32,corner_radius=10,border_width=1,border_color=LINE,fg_color=self.colours[i],hover_color=self.colours[i],command=lambda i=i:self.pick(i))
            b.pack(side='left');self.swatches.append(b);self.label(fret,name,13).pack(side='left',padx=(12,0))
            entry=ctk.CTkEntry(left,textvariable=self.hexes[i],width=125,height=36,fg_color=BG,border_width=1,border_color=LINE,text_color=FG,font=('Consolas',13),corner_radius=8)
            entry.grid(row=r,column=1,sticky='ew',padx=10);entry.bind('<Return>',lambda e,i=i:self.commit_hex(i));entry.bind('<FocusOut>',lambda e,i=i:self.commit_hex(i));self.hex_entries.append(entry)
            self.hexes[i].trace_add('write',lambda *args:self.mark_dirty())
            combo=self.key_menu(left,self.bindings[i]);combo.grid(row=r,column=2,padx=(10,24));self.combos.append(combo)
        presets=ctk.CTkFrame(left,fg_color='transparent');presets.grid(row=8,column=0,columnspan=3,sticky='ew',padx=24,pady=(18,8))
        self.label(presets,'Presets',12,MUTED).pack(side='left',padx=(0,12))
        for name,values in [('Classic',CLASSIC),('Pastel',['#A9D6B0','#F2ADBC','#F5DDA1','#A4C7E8','#EBC29B']),('White',['#FFFFFF']*5)]:
            self.btn(presets,name,lambda v=values:self.preset(v),secondary=True,width=68).pack(side='left',padx=3)
        self.label(left,'Click a colour to edit it. Click a key, then press your keyboard.',11,MUTED,wraplength=470).grid(row=9,column=0,columnspan=3,sticky='w',padx=24,pady=(5,20))
        self.btn(left,'Guitar setup',self.open_firmware,secondary=True,width=145).grid(row=10,column=0,columnspan=3,sticky='w',padx=24,pady=(0,20))
        right=ctk.CTkFrame(body,fg_color='transparent');right.grid(row=0,column=1,sticky='nsew');right.grid_columnconfigure(0,weight=1)
        lighting=self.card(right);lighting.grid(row=0,column=0,sticky='ew');lighting.grid_columnconfigure(0,weight=1)
        self.label(lighting,'Lighting',17,bold=True).grid(row=0,column=0,sticky='w',padx=20,pady=(18,12))
        brightness_row=ctk.CTkFrame(lighting,fg_color='transparent');brightness_row.grid(row=1,column=0,sticky='ew',padx=20)
        self.label(brightness_row,'Brightness',12).pack(side='left');self.bright_text=self.label(brightness_row,f'{self.brightness.get()}%',12,MUTED);self.bright_text.pack(side='right')
        self.slider=ctk.CTkSlider(lighting,from_=0,to=100,number_of_steps=100,variable=self.brightness,command=self.change_brightness,progress_color=ACCENT,button_color=ACCENT,button_hover_color=ACCENT_HOVER,fg_color=LINE)
        self.slider.grid(row=2,column=0,sticky='ew',padx=20,pady=(12,20))
        effect_row=ctk.CTkFrame(lighting,fg_color='transparent');effect_row.grid(row=3,column=0,sticky='ew',padx=20,pady=(0,14))
        self.label(effect_row,'Press effect',12).pack(side='left')
        self.white_menu=ctk.CTkOptionMenu(effect_row,values=['Off','While held','Toggle'],variable=self.white_mode,command=lambda v:self.change_white(),width=125,height=30,fg_color=LINE,button_color=LINE,button_hover_color=HOVER,text_color=FG,dropdown_fg_color=PANEL,dropdown_text_color=FG,dropdown_hover_color=HOVER,font=('Segoe UI',12))
        self.white_menu.pack(side='right')
        effect_colour_row=ctk.CTkFrame(lighting,fg_color='transparent');effect_colour_row.grid(row=4,column=0,sticky='ew',padx=20,pady=(0,14))
        self.label(effect_colour_row,'Colour',12).pack(side='left')
        self.effect_entry=ctk.CTkEntry(effect_colour_row,textvariable=self.effect_hex,width=110,height=32,fg_color=BG,border_color=LINE,text_color=FG,font=('Consolas',12))
        self.effect_entry.pack(side='right');self.effect_entry.bind('<Return>',lambda e:self.commit_effect());self.effect_entry.bind('<FocusOut>',lambda e:self.commit_effect())
        self.effect_swatch=ctk.CTkButton(effect_colour_row,text='',width=32,height=32,corner_radius=8,fg_color=self.effect_colour,hover_color=self.effect_colour,border_color=LINE,border_width=1,command=self.pick_effect)
        self.effect_swatch.pack(side='right',padx=(0,8));self.effect_hex.trace_add('write',lambda *args:self.mark_dirty())
        self.switch(lighting,'Apply saved lights on connect',self.auto_apply,self.mark_dirty).grid(row=5,column=0,sticky='w',padx=20,pady=(0,18))
        buttons=ctk.CTkFrame(lighting,fg_color='transparent');buttons.grid(row=6,column=0,sticky='ew',padx=20,pady=(0,18))
        self.btn(buttons,'Preview',self.apply,width=123).pack(side='left')
        self.btn(buttons,'End preview',self.restore,secondary=True,width=100).pack(side='right')
        self.btn(lighting,'Save to guitar',self.push_to_guitar,width=220).grid(row=7,column=0,sticky='ew',padx=20,pady=(0,10))
        self.label(lighting,'Stores colours and keys · works without the app',11,MUTED,wraplength=267).grid(row=8,column=0,sticky='w',padx=20,pady=(0,16))
        keyboard=self.card(right);keyboard.grid(row=1,column=0,sticky='ew',pady=(16,0));keyboard.grid_columnconfigure(0,weight=1)
        top=ctk.CTkFrame(keyboard,fg_color='transparent');top.grid(row=0,column=0,columnspan=2,sticky='ew',padx=20,pady=(18,10))
        self.label(top,'Keyboard',17,bold=True).pack(side='left')
        self.key_switch=self.switch(top,'',self.enabled,self.toggle_keyboard);self.key_switch.configure(width=42);self.key_switch.pack(side='right')
        for i in range(5,9):
            self.label(keyboard,CONTROLS[i],12).grid(row=i-4,column=0,sticky='w',padx=20,pady=3)
            combo=self.key_menu(keyboard,self.bindings[i]);combo.configure(height=30);combo.grid(row=i-4,column=1,padx=(0,20),pady=3);self.combos.append(combo)
        self.label(keyboard,'',11,MUTED,textvariable=self.key_status,wraplength=265).grid(row=5,column=0,columnspan=2,sticky='w',padx=20,pady=(10,16))
        footer=ctk.CTkFrame(root,fg_color='transparent');footer.grid(row=2,column=0,sticky='ew',padx=30,pady=(18,24))
        self.label(footer,'',12,MUTED,textvariable=self.status,wraplength=590).pack(side='left')
        self.btn(footer,'Save on this PC',self.save_profile,width=124).pack(side='right')
        self.label(footer,'',11,MUTED,textvariable=self.save_state).pack(side='right',padx=15)
        self.theme_targets=[];self.register_theme_widgets(root);self.apply_theme()
        root.protocol('WM_DELETE_WINDOW',self.close);root.after(8,self.tick)
        if autoconnect:root.after(250,self.connect)
    def label(self,parent,text,size,colour=FG,bold=False,**kwargs):
        return ctk.CTkLabel(parent,text=text,text_color=colour,font=('Segoe UI',size,'bold' if bold else 'normal'),anchor='w',justify='left',**kwargs)
    def card(self,parent):return ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=16,border_width=1,border_color=LINE)
    def btn(self,parent,text,command,secondary=False,width=100):
        return ctk.CTkButton(parent,text=text,command=command,width=width,height=36,corner_radius=8,font=('Segoe UI',12),fg_color=BG if secondary else ACCENT,text_color=FG if secondary else '#FFFFFF',hover_color=HOVER if secondary else ACCENT_HOVER)
    def switch(self,parent,text,var,command):
        return ctk.CTkSwitch(parent,text=text,variable=var,command=command,font=('Segoe UI',12),text_color=FG,progress_color=ACCENT,fg_color=OFF,button_color='#FFFFFF',button_hover_color='#F3F3F3',switch_width=34,switch_height=20,border_width=0)
    def key_menu(self,parent,var):
        return ctk.CTkButton(parent,textvariable=var,text=var.get(),width=105,height=36,corner_radius=8,fg_color=BG,border_color=LINE,border_width=1,hover_color=HOVER,text_color=FG,font=('Segoe UI',12),command=lambda:self.capture_key(var))
    def capture_key(self,var):
        if self.firmware_busy:return
        if self.key_capture and self.key_capture.winfo_exists():self.key_capture.lift();return
        self.stop_keyboard();palette=THEMES[self.theme.get()]
        window=ctk.CTkToplevel(self.root);self.key_capture=window
        window.title('Set key');window.geometry('360x190');window.resizable(False,False);window.transient(self.root);window.configure(fg_color=palette['bg'])
        ctk.CTkLabel(window,text='Press a key on your keyboard',text_color=palette['text'],font=('Segoe UI',17)).pack(pady=(24,8))
        hint=ctk.CTkLabel(window,text='One key per binding. F8 is reserved.',text_color=palette['muted'],font=('Segoe UI',12),wraplength=325);hint.pack()
        def finish(key=None):
            if key is not None:var.set(key);self.mark_dirty();self.status.set(f'Key set to {key}')
            window.grab_release();window.destroy();self.key_capture=None
        def pressed(event):
            try:key=keybinds.capture(event.keysym,event.keycode,lambda vk:self.keyboard.user.MapVirtualKeyW(vk,4))
            except ValueError as error:hint.configure(text=str(error));return 'break'
            finish(key);return 'break'
        window.bind('<KeyPress>',pressed)
        row=ctk.CTkFrame(window,fg_color='transparent');row.pack(pady=20)
        for text,action in [('Clear binding',lambda:finish('None')),('Cancel',finish)]:
            ctk.CTkButton(row,text=text,command=action,width=130,height=32,fg_color=palette['accent'],hover_color=palette['accent_hover']).pack(side='left',padx=6)
        window.protocol('WM_DELETE_WINDOW',finish);window.grab_set();window.after(80,window.focus_force)
    def register_theme_widgets(self,widget):
        if isinstance(widget,(ctk.CTk,ctk.CTkBaseClass)):
            properties={}
            for prop in ('fg_color','bg_color','text_color','border_color','hover_color','progress_color','button_color','button_hover_color','dropdown_fg_color','dropdown_text_color','dropdown_hover_color'):
                try:value=widget.cget(prop)
                except (ValueError,tk.TclError):continue
                if isinstance(value,(tuple,list)):
                    for role,colour in BASE_THEME.items():
                        if tuple(value)==colour:properties[prop]=role;break
            if properties:self.theme_targets.append((widget,properties))
        for child in widget.winfo_children():self.register_theme_widgets(child)
    def apply_theme(self):
        palette=THEMES[self.theme.get()]
        for widget,properties in self.theme_targets:widget.configure(**{prop:palette[role] for prop,role in properties.items()})
    def select_theme(self,value):self.apply_theme();self.mark_dirty()
    def change_theme(self):ctk.set_appearance_mode('dark' if self.dark_mode.get() else 'light');self.mark_dirty()
    def mark_dirty(self,*args):self.dirty=True;self.save_state.set('Unsaved changes')
    def commit_hex(self,i):
        try:colour=normalise_hex(self.hexes[i].get())
        except ValueError:
            self.hex_entries[i].configure(border_color='#C24D42');self.status.set(f'{NAMES[i]}: enter a valid hex colour.');return False
        changed=self.colours[i]!=colour;self.colours[i]=colour
        if self.hexes[i].get()!=colour:self.hexes[i].set(colour)
        self.hex_entries[i].configure(border_color=THEMES[self.theme.get()]['line']);self.swatches[i].configure(fg_color=colour,hover_color=colour)
        if changed:
            self.mark_dirty()
            if self.active:self.applied_colours=self.colours.copy()
        return True
    def commit_effect(self):
        try:colour=normalise_hex(self.effect_hex.get())
        except ValueError:
            self.effect_entry.configure(border_color='#C24D42');self.status.set('Effect: enter a valid hex colour.');return False
        if colour!=self.effect_colour:self.effect_colour=colour;self.mark_dirty()
        if self.effect_hex.get()!=colour:self.effect_hex.set(colour)
        self.effect_entry.configure(border_color=THEMES[self.theme.get()]['line']);self.effect_swatch.configure(fg_color=colour,hover_color=colour)
        return True
    def pick_effect(self):
        colour=colorchooser.askcolor(self.effect_colour,parent=self.root,title='Press effect colour')[1]
        if colour:self.effect_hex.set(colour);self.commit_effect()
    def commit_all(self):return all([self.commit_hex(i) for i in range(5)]+[self.commit_effect()])
    def pick(self,i):
        colour=colorchooser.askcolor(self.colours[i],parent=self.root,title=f'{NAMES[i]} fret')[1]
        if colour:self.hexes[i].set(colour);self.commit_hex(i)
    def preset(self,colours):
        for i,c in enumerate(colours):self.hexes[i].set(c);self.commit_hex(i)
    def change_brightness(self,value):
        self.bright_text.configure(text=f'{self.brightness.get()}%');self.mark_dirty()
        if self.active:self.applied_brightness=self.brightness.get()
    def change_white(self):
        self.white_pressed.set(self.white_mode.get()!='Off')
        self.effect.reset(self.effect.previous)
        self.mark_dirty()
        if not self.active:self.apply()
    def run(self,action,after=None):
        if self.firmware_busy:self.status.set('Firmware transfer in progress. Keep USB connected.');return
        if self.pending or self.closing:self.status.set('Please wait for the current operation.');return
        self.pending=self.pool.submit(action);self.after_job=after;self.status.set('Working…')
    def connect(self):
        if self.firmware_busy:return
        self.active=False;self.stop_keyboard();self.connection.set('Connecting…')
        def connected():
            self.connection.set('Connected · Pico')
            if self.auto_apply.get():self.apply()
        self.run(self.guitar.connect,connected)
    def apply(self):
        if self.firmware_busy:return
        if not self.commit_all():return
        if not self.guitar.dev:self.status.set('Connect the guitar first.');return
        if self.pending:self.status.set('Please wait for the current operation.');return
        try:self.keyboard.find()
        except Exception as e:self.status.set(str(e));return
        self.applied_colours=self.colours.copy();self.applied_brightness=self.brightness.get()
        self.effect.reset();self.last_frame=None;self.active=True;self.status.set('Lights active · changes apply live')
    def restore(self):
        self.active=False;self.last_frame=None;self.run(self.guitar.restore)
    def push_to_guitar(self):
        if self.firmware_busy:return
        if self.pending: self.status.set('Please wait for the current operation.'); return
        if not self.commit_all(): return
        try: data=onboard.encode(self.colours,self.brightness.get(),self.white_mode.get(),[v.get() for v in self.bindings],self.effect_colour)
        except (ValueError,KeyError) as e: self.status.set(str(e)); return
        self.active=False; self.last_frame=None; self.stop_keyboard()
        self.save_profile()
        self.run(lambda:self.guitar.push(data))
    def open_firmware(self):
        if self.firmware_dialog and self.firmware_dialog.window.winfo_exists():
            self.firmware_dialog.window.lift();return
        from firmware_ui import FirmwareDialog
        self.firmware_dialog=FirmwareDialog(self,THEMES[self.theme.get()])
    def open_tutorial(self):
        if self.tutorial and self.tutorial.window.winfo_exists():self.tutorial.window.lift();return
        from help_ui import Tutorial
        self.tutorial=Tutorial(self,THEMES[self.theme.get()])
    def open_credits(self):
        if self.credits and self.credits.window.winfo_exists():self.credits.window.lift();return
        from help_ui import Credits
        self.credits=Credits(self,THEMES[self.theme.get()])
    def watch_firmware(self,job):
        state=self.firmware_manager.state(job);message=state['message'];self.status.set(message)
        dialog=self.firmware_dialog
        if dialog and dialog.window.winfo_exists():dialog.status.configure(text=message)
        if state['status']=='running':self.root.after(300,lambda:self.watch_firmware(job));return
        self.firmware_busy=False
        if dialog and dialog.window.winfo_exists():dialog.set_busy(False)
        self.connection.set('Click Connect')
        if state['status']=='complete':
            def connected():self.connection.set('Connected · Pico');self.status.set(message)
            self.run(self.guitar.connect,connected)
    def load_profile(self):
        try:
            d=json.loads(self.profile.read_text());colours=[normalise_hex(c) for c in d['colours']];keys=d['keys'];b=d['brightness']
            if len(colours)!=5 or len(keys)!=9 or not all(k in KEYS for k in keys) or type(b)is not int or not 0<=b<=100:raise ValueError()
            if type(d.get('white_pressed',True))is not bool or type(d.get('auto_apply',False))is not bool:raise ValueError()
            if type(d.get('dark_mode',True))is not bool:raise ValueError()
            self.effect_colour=normalise_hex(d.get('effect_colour','#FFFFFF'));self.effect_hex.set(self.effect_colour)
            theme=d.get('theme','Graphite')
            if theme not in THEMES:theme='Graphite'
            self.theme.set(theme)
            self.dark_mode.set(d.get('dark_mode',True))
            self.colours=colours;self.brightness.set(b);self.white_pressed.set(d.get('white_pressed',True));self.auto_apply.set(d.get('auto_apply',False))
            mode=d.get('white_mode','While held' if self.white_pressed.get() else 'Off')
            self.white_mode.set(mode if mode in ('Off','While held','Toggle') else 'While held')
            for v,k in zip(self.bindings,keys):v.set(k)
        except FileNotFoundError:self.save_state.set('Not saved yet')
        except (OSError,ValueError,KeyError,TypeError,AttributeError):self.status.set('Saved settings could not be loaded. Defaults are shown.')
    def save_profile(self):
        if not self.commit_all():return False
        try:
            self.profile.parent.mkdir(parents=True,exist_ok=True)
            d=dict(version=5,colours=self.colours,brightness=self.brightness.get(),keys=[v.get() for v in self.bindings],white_pressed=self.white_pressed.get(),white_mode=self.white_mode.get(),effect_colour=self.effect_colour,auto_apply=self.auto_apply.get(),dark_mode=self.dark_mode.get(),theme=self.theme.get())
            temp=self.profile.with_suffix('.tmp');temp.write_text(json.dumps(d,indent=2));temp.replace(self.profile)
            self.dirty=False;self.save_state.set('Saved on PC');self.status.set('Settings saved on this PC');return True
        except OSError as e:self.status.set(f'Could not save: {e}');return False
    def stop_keyboard(self,text='F8 to stop'):
        self.enabled.set(False)
        try:self.keyboard.release()
        except Exception as e:text=str(e)
        self.key_status.set(text)
        for c in self.combos:c.configure(state='normal')
    def toggle_keyboard(self):
        if self.firmware_busy:self.stop_keyboard('Firmware transfer in progress');return
        if not self.enabled.get():self.stop_keyboard();return
        try:self.keyboard.find()
        except Exception as e:self.stop_keyboard(str(e));return
        self.key_status.set('Active · F8 to stop')
        for c in self.combos:c.configure(state='disabled')
    def tick(self):
        if self.closing:return
        if self.pending and self.pending.done():
            job=self.pending;after=self.after_job;self.pending=None;self.after_job=None
            try:
                self.status.set(job.result())
                if after:after()
            except Exception as e:self.connection.set('Connection needs attention');self.status.set(str(e))
        if self.light_future and self.light_future.done():
            job=self.light_future;self.light_future=None
            try:job.result()
            except Exception as e:self.active=False;self.last_frame=None;self.status.set(f'Lights stopped: {e}')
        if self.active or self.enabled.get():
            try:
                buttons=self.keyboard.read_buttons()
                if self.enabled.get():
                    if self.keyboard.user.GetAsyncKeyState(0x77)&0x8000:self.stop_keyboard('Stopped with F8')
                    else:self.keyboard.transition(buttons,[v.get() for v in self.bindings])
                white_buttons=self.effect.update(buttons,self.white_mode.get()) if self.active else 0
                if self.active and not self.pending and not self.light_future:
                    colours=reactive_colours(self.applied_colours,white_buttons,True,self.effect_colour)
                    frame=(tuple(colours),self.applied_brightness)
                    if frame!=self.last_frame:
                        self.light_future=self.pool.submit(self.guitar.apply,colours,self.applied_brightness);self.last_frame=frame
            except Exception as e:
                self.active=False;self.last_frame=None;self.stop_keyboard(str(e));self.connection.set('Disconnected');self.status.set(str(e))
        self.root.after(8,self.tick)
    def close(self):
        if self.closing:return
        if self.firmware_busy:self.status.set('Please wait for the firmware transfer to finish. Keep USB connected.');return
        self.stop_keyboard()
        if self.dirty and not self.save_profile():return
        self.active=False;self.closing=True;self.status.set('Restoring lights…');future=self.pool.submit(self.guitar.close)
        def finish():
            if not future.done():self.root.after(50,finish);return
            try:future.result()
            except Exception as e:messagebox.showwarning('Restore lighting',str(e),parent=self.root)
            self.pool.shutdown(wait=False);self.root.destroy()
        finish()


def main():
    if len(sys.argv)==3 and sys.argv[1]=='--firmware-job':
        firmware.run_worker(Path(sys.argv[2]));return
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        g = Guitar()
        try:
            result = {'usb': g.connect(), 'lights': g.mapping}
            k = Keyboard(); k.find(); result['keyboard_slot'] = k.slot
            Path(sys.argv[2]).write_text(json.dumps(result))
        finally: g.close()
        return
    # Prevent two copies from competing for USB access or keyboard key releases.
    kernel = ct.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ct.c_void_p, wt.BOOL, wt.LPCWSTR]; kernel.CreateMutexW.restype = wt.HANDLE
    mutex = kernel.CreateMutexW(None, False, 'Local\\FretGlowApp')
    already_running = ct.get_last_error() == 183
    ctk.set_appearance_mode("light")
    root = ctk.CTk()
    if already_running:
        root.withdraw(); messagebox.showinfo('FretGlow', 'FretGlow is already open. Check your taskbar.'); root.destroy(); return
    try: App(root); root.mainloop()
    finally:
        kernel.CloseHandle.argtypes = [wt.HANDLE]
        if mutex: kernel.CloseHandle(mutex)

if __name__ == '__main__': main()
