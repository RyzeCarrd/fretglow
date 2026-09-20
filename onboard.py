"""FretGlow firmware protocol v1; no flashing or driver changes."""
import re
import struct
import time
import zlib

HID = {chr(65+i): 4+i for i in range(26)}
HID.update({str(i): 29+i for i in range(1,10)})
HID.update({'0':39,'Enter':40,'Backspace':42,'Tab':43,'Space':44,
            'Right':79,'Left':80,'Down':81,'Up':82,'None':0})
MODES = ['Off', 'While held', 'Toggle']

def validate(data):
    if len(data)!=64 or data[:5]!=b'FGL1\x01' or data[5]>31 or data[6]>2 or data[7]:
        raise ValueError('Invalid firmware settings')
    if any(k not in HID.values() for k in data[23:32]) or data[32:34]!=b'\x88\x13' or any(data[34:60]):
        raise ValueError('Unsupported firmware settings')
    if struct.unpack_from('<I',data,60)[0]!=zlib.crc32(data[:60]):
        raise ValueError('Firmware settings checksum failed')
    return data

def encode(colours, brightness, mode, keys):
    if len(colours)!=5 or len(keys)!=9 or not 0<=brightness<=100 or mode not in MODES:
        raise ValueError('Invalid guitar settings')
    data=bytearray(64); data[:4]=b'FGL1'; data[4]=1
    data[5]=round(brightness*31/100); data[6]=MODES.index(mode)
    for i,colour in enumerate(colours):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',colour): raise ValueError('Invalid hex colour')
        data[8+3*i:11+3*i]=bytes.fromhex(colour[1:])
    data[23:32]=bytes(HID[k] for k in keys)
    struct.pack_into('<H',data,32,5000)
    struct.pack_into('<I',data,60,zlib.crc32(data[:60]))
    return bytes(data)

def info(dev, interface):
    result=bytes(dev.ctrl_transfer(0xa1,0x70,0,interface,16,timeout=700))
    if len(result)!=16 or result[:5]!=b'FGLW\x01':
        raise RuntimeError('This guitar needs the FretGlow firmware update.')
    return result

def push(dev, interface, data):
    info(dev,interface)
    if dev.ctrl_transfer(0x21,0x72,0,interface,data,timeout=700)!=64:
        raise RuntimeError('The guitar did not receive all settings.')
    deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        state=info(dev,interface)
        if state[6] in (2,3): raise RuntimeError('The guitar could not save the settings.')
        if state[6]==0 and state[5]&8 and state[8:12]==data[60:64]:
            actual=bytes(dev.ctrl_transfer(0xa1,0x71,0,interface,64,timeout=700))
            if actual!=data: raise RuntimeError('Saved settings did not match. Please retry.')
            return 'Saved on guitar · hold Start or Select for 5 seconds to switch modes'
        time.sleep(.05)
    raise RuntimeError('Save not confirmed. Reconnect and retry before relying on it.')
