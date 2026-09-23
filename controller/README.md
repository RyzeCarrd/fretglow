# Controller extension

`fretglow.cpp` and `fretglow.h` extend the released legacy Santroller firmware.
Modified September 2026. Licensed under GPL-3.0-or-later, with Santroller and other
components retaining their notices. See `../notices/Santroller-GPL-3.0.txt`.

The exact firmware sources used for the Windows package, including the generated
hardware configuration required to rebuild it, are in the release's
`FretGlow-Firmware-Source.zip`. No runtime user profile or full device backup is included.

Hardware: original RP2040 Pico, 2 MB flash, five APA102 LEDs in reverse fret order,
MOSI GP3 / SCK GP6. Frets: GP11, GP12, GP10, GP14, GP15. Strum: GP9 / GP8.
Start/Back: GP16 / GP17. Whammy GP28 and tilt GP19 retain the generated Santroller
configuration and calibration. This is a specific supported configuration, not a
generic firmware template for arbitrary wiring.

The firmware loads a CRC32-protected 64-byte profile from EEPROM offset 64.
Existing EEPROM byte 0 is preserved. Flash commits are deferred to the main loop,
after the USB request finishes. Repeating an identical save does not write flash.
The single-core RP2040 Arduino EEPROM implementation protects flash writes.

USB interface 2: 0x70 reads a 16-byte FGLW/version/status response; 0x71 reads the
saved profile; 0x72 queues a validated profile save; 0x74 enables/disables app preview.
See `../onboard.py` for the exact profile encoding and readback verification.

Protocol v3 stores a 256-byte FGB3 bank at EEPROM offset 128, beside the legacy
active profile at offset 64. The bank has a 64-byte header and three 64-byte
profiles. Header byte 4 is format version 1, byte 5 is the occupied-slot mask,
byte 6 is the startup slot, and bytes 7–59 are reserved zeros. Bytes 60–63 contain
CRC32 over the entire bank excluding that CRC field. All three profiles must be
valid, even when their slots are unoccupied.

USB OUT requests 0x75–0x78 stage four 64-byte chunks in RAM. Request 0x79 with one
zero byte commits only a complete, valid bank. Staging expires after five seconds;
partial transfers leave saved slots alone. IN requests 0x7A–0x7D read the four
chunks. Status bit 4 marks a valid bank, byte 7 reports the active slot and bytes
12–15 contain the saved bank CRC. A legacy 0x72 save updates only the active slot.
Identical banks activate their startup slot without another flash write.

Holding both bottom buttons for five seconds cycles occupied slots and wraps
back to the first. Both must be released before another cycle. The chord suppresses
single-button actions and short keyboard pulses, including staggered releases.
The bottom Start button alone toggles the selected preset and original lighting.
The button above Start alone switches keyboard mode. A CRC-bound
RAM marker preserves the active slot through USB-mode watchdog reboots without
writing flash. Power-on loads the configured startup slot. The USB dispatcher
reserves 0x70–0x7D, and `reset_usb()` calls `fretglow_reboot()` before rebooting.

Protocol/profile v2 adds the press-effect RGB colour at bytes 34–36 and modifier
keys (HID 224–231). Bytes 37–59 stay reserved. Existing v1 profiles remain valid
and render their press effect as white. Keyboard modifiers use the report's
modifier byte; ordinary keys use the NKRO bitmap. The app records single physical
keys, not shortcut combinations, and keeps numpad/navigation keys distinct.

The generated firmware combines the compiled application with an EEPROM profile.
The app embeds settings without recompiling C++ for each colour change. During an
app installation, unrelated EEPROM bytes are copied from the verified backup.
The template/program blocks must match exactly before installation is allowed.

## Rebuild

1. Extract `FretGlow-Firmware-Source.zip` into a short path (Windows compiler paths
   can exceed its path limit). Its firmware directory contains `platformio.ini`.
2. Use the compiler, Python/PlatformIO and Arduino Pico packages from the official
   SantrollerConfigurator v10.8.49 Windows portable package. The included
   `BUILD.txt` gives the environment variables and exact command.
3. The resulting `.pio/build/pico/firmware.uf2` is the application template. It
   must preserve this hardware configuration. The Pico's ROM BOOTSEL mechanism
   accepts unsigned UF2 files, including modified builds.
4. Run `prepare_assets.py` with the compiled UF2, official picotool executable,
   original `.pb` configuration, and generated `config_data.h` to prepare the app
   assets. Keep configurations, profiles, binaries and backups out of Git.

The source build uses the pinned packages in `platformio.ini`; package metadata
and upstream download URLs are recorded in the source archive.
