# FretGlow

A Windows app for five-fret Santroller Pico guitars with APA102 RGB lights.

- Individual fret colours with a picker or hex input.
- Optional white lighting while a fret is held.
- Brightness control and saved settings.
- Graphite, Slate, Violet and Sand interface themes, each in light or dark mode.
- Editable keyboard mappings for frets, strum, Start and Select.

## Use

Download the Windows ZIP from **Releases**, extract it, and open `FretGlow.exe`.
Keep the `_internal` folder beside the executable. Close any older copy first.

Connect the guitar, choose colours and click **Apply lights**. Changes then apply
live. **Save settings** remembers your colours, mappings and theme. Enable
**Apply saved lights on connect** to restore your lighting when connecting.

Keyboard mode sends keys to the focused application. Default fret keys are
**A, S, K, L, M**. **F8** stops keyboard mode. Disable it before editing mappings.

Keep the app open for custom lighting and keyboard control. **Restore** and
closing the app return lighting to the guitar's firmware, including its original
press effects. Reconnect USB if an interrupted session leaves an override active.

## Compatibility

Built and checked against one Santroller Pico with five APA102 frets in XInput
mode. Other controllers and firmware layouts are not supported. No flashing or
driver changes are performed. The guitar remains a game controller while keyboard
mode runs; some games may process both sources or reject simulated keystrokes.

## Development

Windows with Python 3.13:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python fretglow.py
python build.py
```

The build produces `dist/FretGlow-Windows.zip`. Tests use synthetic configuration
data and do not send lighting commands or keyboard input to hardware.

Protocol references: [Santroller firmware](https://github.com/Santroller/Santroller)
and [Santroller Configurator](https://github.com/Santroller/SantrollerConfigurator).
FretGlow is an independent app and is not affiliated with those projects.

Dependencies retain their own licenses. The Windows package includes their notices
and dynamically loads libusb; [libusb source](https://github.com/libusb/libusb/tree/v1.0.30).
