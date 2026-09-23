from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
import customtkinter as ctk
import fretglow
from colour_ui import ColourPicker
from preset_ui import PresetDialog

class EditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=ctk.CTk();self.root.withdraw()
        self.app=fretglow.App(self.root,profile=Path(self.tmp.name)/'profile.json',autoconnect=False)
    def tearDown(self):
        self.app.pool.shutdown()
        for child in list(self.root.winfo_children()):
            if isinstance(child,ctk.CTkToplevel):child.destroy()
        for timer in self.root.tk.call('after','info'):self.root.after_cancel(timer)
        self.root.destroy();self.tmp.cleanup()
    def test_drag_to_slot_and_load_all_settings(self):
        settings=self.app.current_settings();settings['keys'][0]='Right Ctrl';settings['mode']='Off';settings['effect_colour']='#AABBCC'
        id=self.app.library.add('Example',settings)
        dialog=PresetDialog(self.app,fretglow.THEMES['Graphite']);dialog.window.deiconify();dialog.window.update_idletasks()
        dialog.begin(None,id);frame=dialog.targets[1]
        drop=SimpleNamespace(x_root=frame.winfo_rootx()+10,y_root=frame.winfo_rooty()+10)
        dialog.motion(drop);dialog.drop(drop)
        self.assertEqual(self.app.library.slots,[None,id,None]);self.assertEqual(dialog.start.get(),'1')
        dialog.load();self.assertEqual(self.app.bindings[0].get(),'Right Ctrl');self.assertEqual(self.app.white_mode.get(),'Off');self.assertEqual(self.app.effect_colour,'#AABBCC')
        self.assertEqual(self.app.firmware_settings(),self.app.library.bank())
    def test_picker_accepts_hex_and_only_applies_on_use(self):
        changes=[];picker=ColourPicker(self.app,'#FF0000','Red fret',changes.append,fretglow.THEMES['Violet'])
        picker.choose(SimpleNamespace(x=309*.75,y=0));self.assertEqual(picker.colour,'#8000FF');self.assertEqual(changes,[])
        picker.select_colour('#000000');picker.choose(SimpleNamespace(x=309*.75,y=0));self.assertEqual(picker.colour,'#8000FF')
        picker.hex.set('xyz');self.assertFalse(picker.from_hex());self.assertEqual(changes,[])
        picker.hex.set('abc');self.assertTrue(picker.from_hex());self.assertEqual(picker.colour,'#AABBCC');self.assertEqual(changes,[])
        picker.accept();self.assertEqual(changes,['#AABBCC'])
