"""Single physical-key bindings shared by the app and USB firmware."""
# name, Windows virtual key, USB HID usage, PC scan code (E0 prefix if extended)
_rows=[
    ('None',0,0,0),('Enter',13,40,0x1c),('Escape',27,41,0x01),
    ('Backspace',8,42,0x0e),('Tab',9,43,0x0f),('Space',32,44,0x39),
    ('Minus',0xbd,45,0x0c),('Equals',0xbb,46,0x0d),
    ('Left bracket',0xdb,47,0x1a),('Right bracket',0xdd,48,0x1b),
    ('Backslash',0xdc,49,0x2b),('Semicolon',0xba,51,0x27),
    ('Quote',0xde,52,0x28),('Backtick',0xc0,53,0x29),
    ('Comma',0xbc,54,0x33),('Period',0xbe,55,0x34),('Slash',0xbf,56,0x35),
    ('Caps Lock',20,57,0x3a),('Print Screen',44,70,0xe037),('Scroll Lock',145,71,0x46),
    ('Insert',45,73,0xe052),('Home',36,74,0xe047),('Page Up',33,75,0xe049),
    ('Delete',46,76,0xe053),('End',35,77,0xe04f),('Page Down',34,78,0xe051),
    ('Right',39,79,0xe04d),('Left',37,80,0xe04b),('Down',40,81,0xe050),('Up',38,82,0xe048),
    ('Num Lock',144,83,0x45),('Num /',111,84,0xe035),('Num *',106,85,0x37),
    ('Num -',109,86,0x4a),('Num +',107,87,0x4e),('Num Enter',0x10d,88,0xe01c),
    ('Num .',110,99,0x53),('ISO key',0xe2,100,0x56),('Menu',93,101,0xe05d),
    ('Ctrl',162,224,0x1d),('Shift',160,225,0x2a),('Alt',164,226,0x38),('Win',91,227,0xe05b),
    ('Right Ctrl',163,228,0xe01d),('Right Shift',161,229,0x36),
    ('Right Alt',165,230,0xe038),('Right Win',92,231,0xe05c),
]
_letter_scans=[0x1e,0x30,0x2e,0x20,0x12,0x21,0x22,0x23,0x17,0x24,0x25,0x26,0x32,0x31,0x18,0x19,0x10,0x13,0x1f,0x14,0x16,0x2f,0x11,0x2d,0x15,0x2c]
_rows += [(chr(65+i),65+i,4+i,s) for i,s in enumerate(_letter_scans)]
_rows += [(str(i),48+i,29+i,1+i) for i in range(1,10)]+[('0',48,39,0x0b)]
_rows += [(f'F{i}',111+i,57+i,0x3a+i if i<=10 else 0x57+i-11) for i in range(1,13)]
_num_scans=[0x52,0x4f,0x50,0x51,0x4b,0x4c,0x4d,0x47,0x48,0x49]
_rows += [(f'Num {i}',96+i,98 if i==0 else 88+i,s) for i,s in enumerate(_num_scans)]
VK={name:vk for name,vk,_,_ in _rows}
HID={name:hid for name,_,hid,_ in _rows}
SCAN={vk:scan for _,vk,_,scan in _rows}
_by_scan={scan:name for name,_,_,scan in _rows if scan}
_by_vk={vk:name for name,vk,_,_ in _rows if vk}
_special={'Shift_L':'Shift','Shift_R':'Right Shift','Control_L':'Ctrl','Control_R':'Right Ctrl',
    'Alt_L':'Alt','Alt_R':'Right Alt','ISO_Level3_Shift':'Right Alt','Super_L':'Win','Super_R':'Right Win',
    'KP_Enter':'Num Enter','KP_Decimal':'Num .','KP_Delete':'Num .','KP_Insert':'Num 0',
    'KP_End':'Num 1','KP_Down':'Num 2','KP_Next':'Num 3','KP_Left':'Num 4','KP_Begin':'Num 5',
    'KP_Right':'Num 6','KP_Home':'Num 7','KP_Up':'Num 8','KP_Prior':'Num 9',
    'KP_Divide':'Num /','KP_Multiply':'Num *','KP_Subtract':'Num -','KP_Add':'Num +',
    **{f'KP_{i}':f'Num {i}' for i in range(10)}}

def capture(keysym,keycode,map_scan=None):
    name=_special.get(keysym)
    if name is None and map_scan is not None: name=_by_scan.get(map_scan(keycode))
    if name is None: name=_by_vk.get(keycode)
    if name is None: raise ValueError('That key is not supported. Press another key.')
    if name=='F8': raise ValueError('F8 stops app keyboard mode. Choose another key.')
    return name
