from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import firmware as fw
import onboard

SETTINGS=onboard.encode(['#123456']*5,55,'Off',['A','S','K','L','M','Up','Down','Enter','Backspace'])

class FakeDevice:
    def __init__(self,backup,fail_load=False,fail_restart=False,config='compatible'):
        self.backup=backup; self.events=[]; self.fail_load=fail_load; self.fail_restart=fail_restart; self.config=config
    def normal(self,boot=False):
        self.events.append('boot' if boot else 'probe')
        return dict(device_id='1234567890ABCDEF',config_sha256=self.config)
    def recovery(self,device_id): self.events.append('recovery')
    def command(self,command,*args):
        self.events.append(command)
        if command=='save': Path(args[-1]).write_bytes(self.backup)
        if command=='load' and self.fail_load:
            self.fail_load=False; raise RuntimeError('Simulated interrupted write')
        return ''
    def return_normal(self,device_id,settings=None):
        self.events.append('verify new' if settings else 'verify old')
        if settings and self.fail_restart: raise RuntimeError('Simulated failed reconnect')

class FirmwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.full=fw.make_uf2({a:bytes([a//256%256])*256 for a in range(fw.FLASH,fw.END,256)})
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name); self.assets=self.root/'assets'; self.assets.mkdir()
        self.base={fw.FLASH:bytes(range(256)),fw.FLASH+256:b'x'*256}
        raw=fw.make_uf2(self.base); (self.assets/'base.uf2').write_bytes(raw)
        tool=b'test tool'; (self.assets/'picotool.exe').write_bytes(tool)
        fw.write_json(self.assets/'manifest.json',dict(template_sha256=fw.digest(raw),picotool_sha256=fw.digest(tool),compatible_config_sha256=['compatible']))
        self.manager=fw.FirmwareManager(self.root/'data',self.assets)
        self.image=self.manager.generate(SETTINGS,self.root/'custom.uf2')
    def install(self,io):
        job=self.manager.prepare('install',self.image); fw.execute_job(job,io); return job
    def test_generated_firmware_contains_exact_settings(self):
        self.assertEqual(fw.image_settings(self.image.read_bytes(),self.base),SETTINGS)
    def test_preserves_unrelated_eeprom(self):
        out=fw.parse_uf2(fw.build_image(SETTINGS,self.base,self.full))
        old=fw.parse_uf2(self.full)
        self.assertEqual(out[fw.EEPROM][:64],old[fw.EEPROM][:64])
        self.assertEqual(out[fw.EEPROM][128:],old[fw.EEPROM][128:])
        self.assertEqual(out[fw.EEPROM+256],old[fw.EEPROM+256])
    def test_rejects_incomplete_backup(self):
        with self.assertRaises(ValueError): fw.parse_uf2(self.full[:-512],full=True)
        with self.assertRaises(ValueError): fw.parse_uf2(fw.make_uf2(self.base),full=True)
    def test_rejects_duplicated_block(self):
        raw=self.image.read_bytes()
        with self.assertRaises(ValueError): fw.parse_uf2(raw[:512]+raw[:512]+raw[1024:])
    def test_rejects_outside_flash(self):
        with self.assertRaises(ValueError): fw.make_uf2({0x20000000:bytes(256)})
    def test_rejects_different_program(self):
        blocks=fw.parse_uf2(self.image.read_bytes()); blocks[fw.FLASH]=bytes(256)
        with self.assertRaises(ValueError): fw.image_settings(fw.make_uf2(blocks),self.base)
    def test_rejects_corrupt_settings(self):
        data=bytearray(SETTINGS); data[8]^=1
        with self.assertRaises(ValueError): fw.build_image(bytes(data),self.base)
    def test_backup_precedes_write(self):
        io=FakeDevice(self.full); job=self.install(io)
        self.assertLess(io.events.index('save'),io.events.index('load'))
        self.assertEqual(fw.FirmwareManager.state(job)['status'],'complete')
        self.assertEqual(self.manager.restore_point()['backup_sha256'],fw.digest(self.full))
    def test_failed_write_restores_backup(self):
        io=FakeDevice(self.full,fail_load=True); job=self.install(io)
        self.assertEqual(io.events.count('load'),2)
        self.assertIn('verify old',io.events)
        self.assertIn('was restored',fw.FirmwareManager.state(job)['message'])
        self.assertIsNone(self.manager.restore_point())
    def test_failed_reconnect_restores_backup(self):
        io=FakeDevice(self.full,fail_restart=True); job=self.install(io)
        self.assertEqual(io.events.count('load'),2)
        self.assertIn('verify old',io.events)
    def test_bad_backup_never_flashes(self):
        io=FakeDevice(self.full[:-512]); job=self.install(io)
        self.assertNotIn('load',io.events)
        self.assertIn('reboot',io.events)
        self.assertEqual(fw.FirmwareManager.state(job)['status'],'failed')
    def test_incompatible_guitar_stays_in_normal_mode(self):
        io=FakeDevice(self.full,config='different')
        with self.assertRaisesRegex(RuntimeError,'different guitar'): self.install(io)
        self.assertNotIn('boot',io.events)
    def test_undo_uses_verified_restore_point(self):
        self.install(FakeDevice(self.full))
        job=self.manager.prepare('undo'); io=FakeDevice(self.full)
        fw.execute_job(job,io)
        self.assertEqual(fw.FirmwareManager.state(job)['status'],'complete')
        self.assertIsNone(self.manager.restore_point())
        self.assertEqual((job.parent/'undo.uf2').read_bytes(),self.full)
    def test_corrupt_undo_backup_blocks_prepare(self):
        self.install(FakeDevice(self.full))
        Path(self.manager.restore_point()['backup']).write_bytes(b'broken')
        with self.assertRaises(ValueError): self.manager.prepare('undo')
    def test_missing_tool_blocks_prepare(self):
        (self.assets/'picotool.exe').unlink()
        with self.assertRaisesRegex(RuntimeError,'missing or damaged'): self.manager.prepare('install',self.image)
    def test_helper_crash_does_not_leave_ui_waiting_forever(self):
        job=self.manager.prepare('install',self.image)
        fw.write_json(job.with_name('process.json'),dict(pid=123))
        with patch.object(fw,'process_running',return_value=False):
            self.assertEqual(self.manager.state(job)['status'],'failed')

if __name__=='__main__': unittest.main()
