import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import onboard
from presets import Library,packet

SETTINGS=dict(colours=['#AABBCC']*5,brightness=45,mode='Toggle',keys=['A','S','K','L','M','Up','Down','Enter','Backspace'],effect_colour='#123456')

class PresetTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'presets.json';self.library=Library(self.path)
    def test_save_slots_and_settings_survive_restart(self):
        settings=copy.deepcopy(SETTINGS);id=self.library.add('Evening',settings);settings['colours'][0]='#000000'
        self.library.assign(2,id);other=Library(self.path)
        self.assertEqual(other.get(id)['settings'],SETTINGS);self.assertEqual(other.slots,[None,None,id]);self.assertEqual(other.start,2)
        data=other.bank();self.assertEqual(data[5:7],bytes([4,2]));self.assertEqual(data[192:256],packet(SETTINGS))
    def test_duplicate_and_blank_names_do_not_replace_existing(self):
        self.library.add('Evening',SETTINGS)
        for name in ('',' evening '):
            with self.assertRaises(ValueError):self.library.add(name,SETTINGS)
        self.assertEqual(len(Library(self.path).items),1)
    def test_clear_startup_selects_an_occupied_slot(self):
        id=self.library.add('Preset',SETTINGS);self.library.assign(0,id);self.library.assign(2,id);self.library.assign(0,None)
        self.assertEqual(self.library.start,2);self.library.assign(2,None)
        with self.assertRaises(ValueError):self.library.bank()
    def test_failed_save_leaves_memory_unchanged(self):
        id=self.library.add('Preset',SETTINGS)
        with patch.object(self.library,'save',side_effect=OSError('Disk full')):
            with self.assertRaises(OSError):self.library.assign(2,id)
        self.assertEqual(self.library.slots,[None]*3);self.assertEqual(self.library.start,0)
    def test_invalid_library_is_not_overwritten(self):
        self.path.write_text('{broken')
        with self.assertRaises(ValueError):Library(self.path)
        self.assertEqual(self.path.read_text(),'{broken')

class BankTests(unittest.TestCase):
    def setUp(self):self.data=onboard.encode_bank([packet(SETTINGS)]*3,7,2)
    def test_corruption_and_empty_startup_are_rejected(self):
        broken=bytearray(self.data);broken[200]^=1
        with self.assertRaises(ValueError):onboard.validate_bank(broken)
        with self.assertRaises(ValueError):onboard.encode_bank([packet(SETTINGS)]*3,1,2)
    def test_bank_transfer_commits_only_after_all_chunks(self):
        data=self.data
        class Device:
            def __init__(self):self.writes=[];self.saved=None;self.chunks=[]
            def ctrl_transfer(self,type,req,value,index,arg,**kw):
                if req==0x70:return b'FGLW\x03'+bytes([24 if self.saved else 8,0,2])+data[252:256]+(data[60:64] if self.saved else bytes(4))
                if 0x75<=req<=0x78:self.writes.append(req);self.chunks.append(bytes(arg));return 64
                if req==0x79:
                    assert self.writes==list(range(0x75,0x79));self.saved=b''.join(self.chunks);self.writes.append(req);return 1
                if 0x7a<=req<=0x7d:return self.saved[(req-0x7a)*64:(req-0x7a+1)*64]
        device=Device();onboard.push_bank(device,2,data);self.assertEqual(device.saved,data)
    def test_partial_transfer_never_sends_commit(self):
        class Device:
            def ctrl_transfer(self,type,req,*args,**kw):
                if req==0x70:return b'FGLW\x03'+bytes(11)
                if req==0x75:return 64
                if req==0x76:return 12
                raise AssertionError('Partial bank must not commit')
        with self.assertRaisesRegex(RuntimeError,'interrupted'):onboard.push_bank(Device(),2,self.data)
    def test_legacy_firmware_never_receives_bank_writes(self):
        class Device:
            def ctrl_transfer(self,type,req,*args,**kw):
                assert req==0x70
                return b'FGLW\x02'+bytes(11)
        with self.assertRaisesRegex(RuntimeError,'new firmware'):onboard.push_bank(Device(),2,self.data)
