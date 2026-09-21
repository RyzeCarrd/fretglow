"""FretGlow saved profiles, with compatibility for the original firmware."""
import re
import struct
import time
import zlib
from keybinds import HID

MODES = ['Off', 'While held', 'Toggle']

def validate(data):
    if len(data)!=64 or data[:4]!=b'FGL1' or data[4] not in (1,2) or data[5]>31 or data[6]>2 or data[7]:
        raise ValueError('Invalid firmware settings')
    keys_valid=all(k==0 or 4<=k<=82 for k in data[23:32]) if data[4]==1 else all(k in HID.values() for k in data[23:32])
    if not keys_valid or data[32:34]!=b'\x88\x13' or any(data[34 if data[4]==1 else 37:60]):
        raise ValueError('Unsupported firmware settings')
    if struct.unpack_from('<I',data,60)[0]!=zlib.crc32(data[:60]):
        raise ValueError('Firmware settings checksum failed')
    return data

def encode(colours, brightness, mode, keys, effect_colour='#FFFFFF'):
    if len(colours)!=5 or len(keys)!=9 or not 0<=brightness<=100 or mode not in MODES:
        raise ValueError('Invalid guitar settings')
    if not re.fullmatch(r'#[0-9a-fA-F]{6}',effect_colour): raise ValueError('Invalid effect colour')
    data=bytearray(64); data[:4]=b'FGL1'; data[4]=2
    data[5]=round(brightness*31/100); data[6]=MODES.index(mode)
    for i,colour in enumerate(colours):
        if not re.fullmatch(r'#[0-9a-fA-F]{6}',colour): raise ValueError('Invalid hex colour')
        data[8+3*i:11+3*i]=bytes.fromhex(colour[1:])
    data[23:32]=bytes(HID[k] for k in keys)
    struct.pack_into('<H',data,32,5000)
    data[34:37]=bytes.fromhex(effect_colour[1:])
    struct.pack_into('<I',data,60,zlib.crc32(data[:60]))
    return bytes(data)

def info(dev, interface):
    result=bytes(dev.ctrl_transfer(0xa1,0x70,0,interface,16,timeout=700))
    if len(result)!=16 or result[:4]!=b'FGLW' or result[4] not in (1,2):
        raise RuntimeError('This guitar needs the FretGlow firmware update.')
    return result

def push(dev, interface, data):
    validate(data)
    state=info(dev,interface)
    if state[4]==1 and data[4]==2:
        if data[34:37]!=b'\xff\xff\xff' or any(k>82 for k in data[23:32]):
            raise RuntimeError('Install the latest firmware from Guitar setup > Install update to save effect colours or these keys on the guitar.')
        legacy=bytearray(data); legacy[4]=1; legacy[34:37]=bytes(3)
        struct.pack_into('<I',legacy,60,zlib.crc32(legacy[:60])); data=bytes(legacy)
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
