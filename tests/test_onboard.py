import struct
import unittest
import zlib
from unittest.mock import patch
import onboard

class ProtocolTests(unittest.TestCase):
    def data(self):
        return onboard.encode(['#000000','#FFFFFF','#123456','#ABCDEF','#AABBCC'],30,'Toggle',['A','S','K','L','M','Up','Down','Enter','Backspace'])
    def test_packet_layout(self):
        d=self.data()
        self.assertEqual(len(d),64)
        self.assertEqual(d[:8],b'FGL1\x02\x09\x02\x00')
        self.assertEqual(d[8:11],bytes(3))
        self.assertEqual(d[23:32],bytes([4,22,14,15,16,82,81,40,42]))
        self.assertEqual(struct.unpack_from('<H',d,32)[0],5000)
        self.assertEqual(struct.unpack_from('<I',d,60)[0],zlib.crc32(d[:60]))
    def test_invalid(self):
        with self.assertRaises(ValueError): onboard.encode(['#GG0000']*5,50,'Off',['A']*9)
        with self.assertRaises(ValueError): onboard.encode(['#000000']*5,101,'Off',['A']*9)
    def test_save_requires_full_readback(self):
        data=self.data()
        class Device:
            def ctrl_transfer(self,type,req,value,index,arg,**kw):
                if req==0x70: return b'FGLW\x02\x08\x00\x00'+data[60:]+bytes(4)
                if req==0x72: return 64
                if req==0x71: return bytes(64)
        with self.assertRaisesRegex(RuntimeError,'did not match'): onboard.push(Device(),2,data)
    def test_wrong_firmware(self):
        class Device:
            def ctrl_transfer(self,*a,**kw): return bytes(16)
        with self.assertRaisesRegex(RuntimeError,'firmware update'): onboard.info(Device(),2)
    def test_custom_effect_colour_and_modifiers(self):
        data=onboard.encode(['#000000']*5,50,'Toggle',['Right Ctrl']*9,'#12ABEF')
        self.assertEqual(data[34:37],bytes.fromhex('12ABEF'))
        self.assertEqual(data[23:32],bytes([228])*9)
        self.assertEqual(onboard.validate(data),data)
    def test_old_saved_profile_remains_valid(self):
        data=bytearray(self.data());data[4]=1;data[34:37]=bytes(3)
        struct.pack_into('<I',data,60,zlib.crc32(data[:60]))
        self.assertEqual(onboard.validate(bytes(data)),bytes(data))
    def test_old_firmware_rejects_custom_effect_before_writing(self):
        class Device:
            def ctrl_transfer(self,type,req,*args,**kw):
                if req!=0x70: raise AssertionError('Must not write unsupported settings')
                return b'FGLW\x01'+bytes(11)
        data=onboard.encode(['#FFFFFF']*5,50,'Toggle',['A']*9,'#123456')
        with self.assertRaisesRegex(RuntimeError,'latest firmware'): onboard.push(Device(),2,data)
    def test_old_firmware_accepts_compatible_white_profile(self):
        class Device:
            data=None
            def ctrl_transfer(self,type,req,value,index,arg,**kw):
                if req==0x70: return b'FGLW\x01\x08\x00\x00'+(self.data[60:] if self.data else bytes(4))+bytes(4)
                if req==0x72:self.data=bytes(arg);return 64
                if req==0x71:return self.data
        device=Device();onboard.push(device,2,self.data())
        self.assertEqual(device.data[4],1);self.assertEqual(device.data[34:60],bytes(26))
        onboard.validate(device.data)

if __name__=='__main__': unittest.main()
