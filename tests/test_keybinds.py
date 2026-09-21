import unittest
import keybinds as k

class KeyTests(unittest.TestCase):
    def test_capture_letters_ignores_shifted_character(self):
        self.assertEqual(k.capture('a',65),'A')
        self.assertEqual(k.capture('A',65),'A')
    def test_keypad_and_modifier_keys_stay_distinct(self):
        self.assertEqual(k.capture('KP_Enter',13),'Num Enter')
        self.assertEqual(k.capture('Return',13),'Enter')
        self.assertEqual(k.capture('Control_R',17),'Right Ctrl')
        self.assertEqual(k.capture('KP_End',35),'Num 1')
    def test_capture_uses_physical_scan_code(self):
        self.assertEqual(k.capture('numbersign',0xde,lambda vk:0x2b),'Backslash')
        self.assertEqual(k.HID['Backslash'],49)
    def test_reserved_and_unsupported_keys_are_not_silently_bound(self):
        with self.assertRaises(ValueError): k.capture('F8',0x77)
        with self.assertRaises(ValueError): k.capture('AudioPlay',0xb3)
    def test_scan_codes_and_usb_keys_agree_for_navigation_and_modifiers(self):
        self.assertEqual(k.SCAN[k.VK['Right Ctrl']],0xe01d)
        self.assertEqual(k.HID['Right Ctrl'],228)
        self.assertEqual(k.SCAN[k.VK['Num Enter']],0xe01c)
        self.assertEqual(k.HID['Num Enter'],88)

if __name__=='__main__': unittest.main()
