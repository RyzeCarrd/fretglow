# Using FretGlow

1. Plug in the guitar and click **Connect**. If it is in keyboard mode, hold **Select / Back** for five seconds to return to controller mode.
2. Pick your fret colours using the swatches or hex fields.
3. Click a key beside a fret or button, then press one key on your PC keyboard. Use **Clear binding** to remove it. F8 is reserved for stopping the app's keyboard mode.
4. Choose a **Press effect**: **While held**, **Toggle**, or **Off**. Pick its colour too. While held restores the normal colour on release; Toggle restores it on the next press.
5. Click **Save to guitar**. After it confirms the save, those colours, effects and keys stay on the guitar, even when the app is closed or you move to another PC.

If the app says the guitar needs an update, open **Guitar setup → Install update** once. It includes your current settings automatically. You do not need to choose or generate a file first.

## What each button does

| Button | What it does |
| --- | --- |
| Preview | Tries the lighting while the app is open. |
| End preview | Lets the guitar control its own lighting again. |
| Save to guitar | Stores colours, press effect and keys inside the controller. Use this for everyday changes. |
| Save on this PC | Remembers your choices in this Windows app. Does not update the guitar's saved settings. |
| Install update | Updates the software inside the guitar, called firmware. Adds features and includes your current settings. |
| Undo last update | Restores the previous firmware and the settings from that backup. Newer saved settings are replaced too. |

Installation verifies a complete recovery backup before changing the guitar. Keep USB connected until it finishes. **Open backups** shows the local backups and transfer logs.

## Using the guitar without the app

- Hold **Start** for five seconds to switch between saved colours and original lighting.
- Hold **Select / Back** for five seconds to switch between controller and native keyboard mode.
- Release before repeating either hold. The saved keys work in native keyboard mode without FretGlow running.

The app's **Keyboard** switch is a separate way to type while the app is running. **F8** stops that app mode. To exit native keyboard mode, use the five-second Select / Back hold instead.

## Manual files

**Guitar setup → Manual file options → Export file** makes a `.uf2` containing the current settings. Exporting does not change the guitar. **Install from file** installs a compatible exported file using the same verified backup process.

For manual recovery, unplug USB, hold **BOOTSEL on the Pico board** while reconnecting, then release when **RPI-RP2** appears. Copy a verified `before.uf2` backup onto that drive. Keep USB connected while it copies; the drive disappears when the guitar restarts. The circular gameplay buttons are not BOOTSEL.
