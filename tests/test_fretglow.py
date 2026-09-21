import ctypes as ct
from pathlib import Path
import unittest
import tempfile
import customtkinter as ctk
import fretglow as f

class Tests(unittest.TestCase):
    def test_toggle_white_on_press_not_hold_or_release(self):
        effect=f.WhiteEffect();green,red=f.MASKS[:2]
        self.assertEqual(effect.update(green,'Toggle'),green)
        self.assertEqual(effect.update(green,'Toggle'),green)
        self.assertEqual(effect.update(0,'Toggle'),green)
        self.assertEqual(effect.update(red,'Toggle'),green|red)
        effect.update(0,'Toggle')
        self.assertEqual(effect.update(green,'Toggle'),red)
        self.assertEqual(effect.update(0,'Off'),0)
        self.assertEqual(effect.update(green,'While held'),green)
        self.assertEqual(effect.update(0,'While held'),0)
    def test_white_press_toggle_and_release(self):
        original=f.CLASSIC.copy()
        self.assertEqual(f.reactive_colours(original,0x1000,True),['#FFFFFF']+original[1:])
        self.assertEqual(f.reactive_colours(original,0x1000,False),original)
        self.assertEqual(f.reactive_colours(original,0,True),original)
        chord=f.reactive_colours(original,0x9000,True)
        self.assertEqual([chord[i] for i in (0,2)],['#FFFFFF','#FFFFFF'])
        self.assertEqual(original,f.CLASSIC)
    def test_hex_input(self):
        for value in ['ff0099',' #ff0099 ','#f09']:
            self.assertEqual(f.normalise_hex(value),'#FF0099')
        with self.assertRaises(ValueError):f.normalise_hex('nope')
    def test_custom_press_effect_preserves_other_frets(self):
        self.assertEqual(f.reactive_colours(f.CLASSIC,0x1000,True,'#123456'),['#123456']+f.CLASSIC[1:])
    def test_light_updates_only_changed_frets(self):
        g=f.Guitar();g.mapping=[4,3,2,1,0];writes=[];g.write=writes.append
        g.apply(f.CLASSIC,30);self.assertEqual(len(writes),5)
        g.apply(f.CLASSIC,30);self.assertEqual(len(writes),5)
        g.apply(f.reactive_colours(f.CLASSIC,0x1000,True),30)
        self.assertEqual(writes[-1],bytes([4,9,255,255,255]))
        self.assertEqual(len(writes),6)
        g.apply(f.CLASSIC,30);self.assertEqual(len(writes),7)
    def test_controller_mapping(self):
        def varint(value):
            out=bytearray()
            while value>127:out.append((value&127)|128);value>>=7
            return bytes(out)+bytes([value])
        def scalar(tag,value):return varint(tag<<3)+varint(value)
        def message(tag,value):return varint((tag<<3)|2)+varint(len(value))+value
        data=scalar(1,6)+scalar(10,5)+scalar(48,9)
        for fret,index in enumerate([5,4,3,2,1]):
            data+=message(7,message(115,scalar(5,fret)+message(6,bytes([index]))))
        self.assertEqual(f.light_config(data),[4,3,2,1,0])
    def test_themes_and_saved_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            root=ctk.CTk();root.withdraw()
            app=f.App(root,profile=Path(directory)/'profile.json',autoconnect=False)
            try:
                self.assertEqual(app.theme.get(),'Graphite')
                for name,palette in f.THEMES.items():
                    app.theme.set(name);app.select_theme(name)
                    self.assertEqual(tuple(root.cget('fg_color')),palette['bg'])
                    self.assertEqual(tuple(app.slider.cget('progress_color')),palette['accent'])
                    app.dark_mode.set(False);app.change_theme();self.assertEqual(ctk.get_appearance_mode(),'Light')
                    app.dark_mode.set(True);app.change_theme();self.assertEqual(ctk.get_appearance_mode(),'Dark')
                app.theme.set('Violet');app.select_theme('Violet')
                app.hexes[0].set('A1B2C3');app.white_pressed.set(False);app.white_mode.set('Toggle')
                app.effect_hex.set('12abef');app.bindings[0].set('Right Ctrl')
                self.assertTrue(app.save_profile())
                app.theme.set('Graphite');app.load_profile()
                self.assertEqual(app.theme.get(),'Violet');self.assertEqual(app.colours[0],'#A1B2C3');self.assertFalse(app.white_pressed.get())
                self.assertEqual(app.white_mode.get(),'Toggle')
                self.assertEqual(app.effect_colour,'#12ABEF');self.assertEqual(app.bindings[0].get(),'Right Ctrl')
                self.assertIsNotNone(app.combos[0]._text_label)
                self.assertEqual(app.combos[0]._text_label.cget('text'),'Right Ctrl')
            finally:
                app.pool.shutdown()
                for timer in root.tk.call('after','info'):root.after_cancel(timer)
                root.destroy()
    def test_light_protocol_rgb_and_black(self):
        self.assertEqual(f.packet(4, '#123456', 100), bytes([4,31,18,52,86]))
        self.assertEqual(f.packet(2, '#000000', 30), bytes([2,0,1,0,0]))
        self.assertEqual(f.packet(0, '#ffffff', 0), bytes([0,0,1,0,0]))
        with self.assertRaises(ValueError): f.packet(0, '#xxx', 100)
    def test_keys_chords_shared_bindings_and_release(self):
        events=[]; keyboard=f.Keyboard(lambda k,d: events.append((k,d)))
        keyboard.transition(0x1000 | 0x8000, f.DEFAULT_KEYS)
        self.assertEqual(set(events), {(65,True),(75,True)})
        keyboard.transition(0x8000, f.DEFAULT_KEYS)
        self.assertEqual(events[-1], (65,False))
        keyboard.release(); self.assertEqual(events[-1], (75,False)); self.assertFalse(keyboard.held)
        events.clear(); bindings=f.DEFAULT_KEYS.copy(); bindings[1]='A'
        keyboard.transition(0x3000, bindings); keyboard.transition(0x2000, bindings)
        self.assertEqual(events, [(65,True)])
        keyboard.transition(0, bindings); self.assertEqual(events[-1], (65,False))
    def test_disconnect_releases_keys(self):
        events=[]; keyboard=f.Keyboard(lambda k,d: events.append((k,d)))
        keyboard.transition(0x1000, f.DEFAULT_KEYS)
        with self.assertRaises(RuntimeError): keyboard.poll(f.DEFAULT_KEYS)
        self.assertEqual(events, [(65,True),(65,False)])
    def test_windows_input_structure(self):
        self.assertEqual(ct.sizeof(f.Input), 40 if ct.sizeof(ct.c_void_p)==8 else 28)
    def test_bad_configuration_is_rejected(self):
        for value in (b'', b'\x3a\xff', b'\xff'*12):
            with self.assertRaises(ValueError): f.light_config(value)

if __name__=='__main__': unittest.main()
