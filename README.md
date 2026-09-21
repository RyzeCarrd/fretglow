# FretGlow

A Windows app for five-fret Santroller Pico guitars with APA102 RGB lights.

- Individual fret colours with a picker or hex input.
- Press effect in any colour: Off, While held, or Toggle (press once for the effect colour, again to restore the fret colour).
- Brightness control and saved settings.
- Graphite, Slate, Violet and Sand interface themes, each in light or dark mode.
- Click a binding and press your PC keyboard to record it, including navigation, modifier and numpad keys.
- Save colours, press effects and keys directly on supported FretGlow firmware.
- Generate a customised firmware file, install it, and undo an installation.

## Use

Download the Windows ZIP from **Releases**, extract it, and open `FretGlow.exe`.
Keep the `_internal` folder beside the executable. Close any older copy first.

Click **Tutorial** in the app for a guided walkthrough, or read [the tutorial](TUTORIAL.md).

Connect the guitar, choose colours and click **Preview**. Changes then apply
live. **Save on this PC** remembers your colours, mappings and theme in Windows. Enable
**Apply saved lights on connect** to restore your lighting when connecting.

Keyboard mode sends keys to the focused application. Default fret keys are
**A, S, K, L, M**. **F8** stops keyboard mode. Disable it before editing mappings.

**Save to guitar** stores colours, the press-effect colour and your key mappings on
FretGlow firmware, with readback verification. This is the button for everyday changes.
Closing the app or clicking **End preview** ends the preview and resumes the guitar's lighting.
Custom effect colours and extended keys need the latest guitar update. Existing saved
profiles keep their keys and default to a white effect colour until you change it.

## Firmware

Firmware is the software inside your guitar. Open **Guitar setup** to update it.

1. **Install update** automatically includes your current settings, verifies the connected
   guitar's configuration, makes and verifies a complete backup, installs the update and
   checks the saved settings after restart. There is no separate file-generation step.
2. **Undo last update** restores the full firmware and settings from before the most recent
   installation. It checks that the backup belongs to this guitar and backs up the current
   state before restoring. Undo does not undo a subsequent **Save to guitar** by itself.
3. **Manual file options** has **Export file** and **Install from file** for manual use.

The transfer runs in a separate process. Keep USB connected until it finishes.
If installation or the restart check fails, the helper attempts to restore its verified backup.
Backups and transfer logs stay in `%LOCALAPPDATA%\FretGlow\firmware`; **Open backups** opens it.
Do not delete that folder if you need Undo. Use the same Windows user account to access its backups.

With the updated firmware, saved colours load when powered on. Hold **Start** for
five seconds to toggle between saved colours and the original lighting. Hold
**Select / Back** for five seconds to switch between controller and USB keyboard mode.
Release before repeating either shortcut. The frets use your saved key mappings;
short Start/Select presses in keyboard mode type on release, so holding a shortcut
does not repeatedly send Enter or Backspace. No app is needed on the other computer.

Return to controller mode before connecting the app or installing another update.
The app's keyboard switch is its existing Windows keyboard bridge; **F8** stops that
bridge. The guitar's native keyboard mode is switched with **Select / Back** instead.

For manual recovery, unplug USB, hold **BOOTSEL on the Pico board** while reconnecting,
then release when **RPI-RP2** appears. Copy a verified `before.uf2` backup onto that drive.
The drive disappears when the guitar restarts. An interrupted copy can be retried through
BOOTSEL. The two circular gameplay buttons are not BOOTSEL.

## Compatibility

Built and checked against one Santroller Pico with five APA102 frets in XInput
mode. The bundled firmware is for the Nuclear Pico layout with APA102 frets,
Start GP16, Back GP17 and the verified input mapping/calibration. The updater rejects
other configuration fingerprints; it is not a universal Pico firmware installer.
Normal lighting control remains available on compatible legacy Santroller firmware.
The app does not replace Windows drivers. Automatic recovery transfers need WinUSB on
**RP2 Boot (Interface 1)**; manual BOOTSEL copying uses the standard USB drive.
The Windows keyboard bridge also leaves game-controller input active; native firmware
keyboard mode enumerates as a USB keyboard.

## Development

Windows with Python 3.13:

```powershell
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python fretglow.py
python build.py
```

For a source build, prepare the ignored `firmware_assets` directory as described in
[`controller/README.md`](controller/README.md), or copy it from the release's
`FretGlow/_internal/firmware_assets` directory. The build produces
`dist/FretGlow-Windows.zip`. Tests use synthetic configurations and simulated
transfers; they do not flash hardware.

Release validation includes an actual verified installation, settings readback,
restoration of the original firmware using Undo, and reinstallation on the supported guitar.

Protocol references: [Santroller firmware](https://github.com/Santroller/Santroller)
and [Santroller Configurator](https://github.com/Santroller/SantrollerConfigurator).
FretGlow is an independent app and is not affiliated with those projects.

Dependencies retain their own licenses. The Windows package includes their notices
and dynamically loads libusb; [libusb source](https://github.com/libusb/libusb/tree/v1.0.30).
Controller firmware derives from Santroller and is GPL-3.0; the modified firmware
source and build instructions are supplied as `FretGlow-Firmware-Source.zip` alongside
the Windows release. The app communicates with the firmware over USB.
The bundled [picotool 2.3.1](https://github.com/raspberrypi/picotool/tree/2.3.1)
retains Raspberry Pi's license; its [Windows build tooling](https://github.com/raspberrypi/pico-sdk-tools/tree/v2.3.1-0)
is also available upstream.

## Credits

Made by Harley · discord: harleydabrit

<img src="assets/harley.png" alt="Harley's profile picture" width="100">
