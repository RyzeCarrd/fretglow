from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch
from concurrent.futures import Future
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
    def test_click_loads_main_page_but_drag_does_not(self):
        settings=self.app.current_settings();settings['colours']=['#8000FF']*5;settings['brightness']=61
        id=self.app.library.add('Purple',settings)
        dialog=PresetDialog(self.app,fretglow.THEMES['Graphite']);dialog.window.update_idletasks()
        row=dialog.rows[0][0];event=SimpleNamespace(x_root=row.winfo_rootx()+10,y_root=row.winfo_rooty()+10)
        dialog.begin(event,id);dialog.drop(event)
        self.assertEqual(self.app.colours,settings['colours'])
        self.assertEqual([v.get() for v in self.app.hexes],settings['colours'])
        self.assertEqual(self.app.brightness.get(),61)
        self.assertIsNotNone(self.app.autosave_data)
        self.app.autosave_data=None
        dialog.begin(event,id);target=dialog.targets[0]
        end=SimpleNamespace(x_root=target.winfo_rootx()+10,y_root=target.winfo_rooty()+10)
        dialog.motion(end);dialog.drop(end)
        self.assertIsNone(self.app.autosave_data)

    def test_autosave_debounces_and_keeps_edit_during_transfer(self):
        app=self.app;app.guitar.dev=object();app.guitar.onboard=True
        first=Future();second=Future()
        with patch.object(app.pool,'submit',side_effect=[first,second]) as submit:
            app.hexes[0].set('#112233');app.commit_hex(0)
            app.hexes[0].set('#445566');app.commit_hex(0)
            app.service_guitar_save();submit.assert_not_called()
            app.service_guitar_save(force=True);sent=app.autosave_sent
            self.assertEqual(submit.call_count,1)
            app.hexes[1].set('#AABBCC');app.commit_hex(1)
            latest=app.autosave_data;self.assertNotEqual(sent,latest)
            first.set_result('Saved');app.service_guitar_save()
            self.assertEqual(app.autosave_data,latest)
            app.service_guitar_save(force=True)
            self.assertEqual(submit.call_args.args[1],latest)
            second.set_result('Saved');app.service_guitar_save()
            self.assertIsNone(app.autosave_data)
            self.assertEqual(app.guitar_save_state.get(),'Saved to guitar · active slot')

    def test_failed_and_offline_saves_do_not_claim_saved_or_loop(self):
        app=self.app;app.queue_guitar_save();app.service_guitar_save(force=True)
        self.assertIsNotNone(app.autosave_data);self.assertIsNone(app.autosave_due)
        app.guitar.dev=object();app.guitar.onboard=True;failed=Future()
        with patch.object(app.pool,'submit',return_value=failed) as submit:
            app.queue_guitar_save();app.service_guitar_save(force=True)
            failed.set_exception(RuntimeError('USB disconnected'));app.service_guitar_save()
            app.service_guitar_save(force=True)
            self.assertEqual(submit.call_count,1);self.assertIsNotNone(app.autosave_data)
            self.assertIn('Not saved',app.guitar_save_state.get())

    def test_initial_values_and_invalid_hex_do_not_queue_save(self):
        self.app.current_settings();self.assertIsNone(self.app.autosave_data)
        self.app.hexes[0].set('invalid');self.assertFalse(self.app.commit_hex(0))
        self.assertIsNone(self.app.autosave_data)

    def test_saving_bank_cancels_pending_single_slot_save(self):
        app=self.app;app.guitar.dev=object();app.queue_guitar_save()
        with patch.object(app,'run'):
            app.send_settings(b'bank')
        self.assertIsNone(app.autosave_data);self.assertIsNone(app.autosave_due)

    def test_close_flushes_debounce_before_releasing_usb(self):
        app=self.app;app.guitar.dev=object();app.guitar.onboard=True;app.queue_guitar_save()
        transfer=Future()
        with patch.object(app.pool,'submit',return_value=transfer) as submit:
            app.close()
            self.assertEqual(submit.call_args.args[0],app.guitar.push)
            self.assertFalse(app.closing)
            self.assertIs(app.autosave_future,transfer)

    def test_picker_accepts_hex_and_only_applies_on_use(self):
        changes=[];picker=ColourPicker(self.app,'#FF0000','Red fret',changes.append,fretglow.THEMES['Violet'])
        picker.choose(SimpleNamespace(x=309*.75,y=0));self.assertEqual(picker.colour,'#8000FF');self.assertEqual(changes,[])
        picker.select_colour('#000000');picker.choose(SimpleNamespace(x=309*.75,y=0));self.assertEqual(picker.colour,'#8000FF')
        picker.hex.set('xyz');self.assertFalse(picker.from_hex());self.assertEqual(changes,[])
        picker.hex.set('abc');self.assertTrue(picker.from_hex());self.assertEqual(picker.colour,'#AABBCC');self.assertEqual(changes,[])
        picker.accept();self.assertEqual(changes,['#AABBCC'])
