# Using FretGlow

1. Plug in the guitar and click **Connect**. If it is in keyboard mode, hold the **button above the bottom Start button** for five seconds to return to controller mode.
2. Click a colour square to open the picker, or use a hex field.
3. Click a key beside a fret or button, then press one key on your PC keyboard. Use **Clear binding** to remove it. F8 is reserved for stopping the app's keyboard mode.
4. Choose a **Press effect**: **While held**, **Toggle**, or **Off**. Pick its colour too. While held restores the normal colour on release; Toggle restores it on the next press.
5. Click **Save to guitar** to update the active guitar slot. Those colours, effects and keys stay on the guitar, even with the app closed or on another PC.

If the app says the guitar needs an update, open **Guitar setup → Install update** once. It includes assigned slots, or current settings if none are assigned. You do not need to choose or generate a file first.

## Custom presets and three guitar slots

1. Choose colours, brightness, keys and a press effect in the main window.
2. Open **My presets**, enter a name and click **Save current as preset**.
3. Drag presets into the three slots on the right. You can also select a preset and click **Assign**.
4. Choose a **Startup** slot, then click **Save slots to guitar**. Empty slots are skipped.
5. Hold **both bottom buttons together** for five seconds to cycle presets 1 → 2 → 3 → 1, skipping empty slots. Release both between holds. Reconnecting loads the startup slot.

To edit a preset, click it and choose **Load selected**. Edit the settings in the main window, then choose **Replace selected**. Save slots to guitar again to update the controller. **Clear** removes a slot assignment; the named preset stays in the PC library.

## Press effect

The press colour is the colour a fret changes to when pressed.

- **Off:** the fret keeps its normal colour.
- **While held:** the press colour lasts until you let go.
- **Toggle:** press once for the press colour; press again to go back.

## What each button does

| Button | What it does |
| --- | --- |
| Preview | Tries the lighting while the app is open. |
| End preview | Lets the guitar control its own lighting again. |
| Save to guitar | Updates the active guitar slot with the current colours, press effect and keys. Other slots stay as they are. |
| Save slots to guitar | Sends the whole three-slot arrangement and activates the startup slot. |
| Save on this PC | Remembers your choices in this Windows app. Does not update the guitar's saved settings. |
| Install update | Updates the guitar's software, called firmware. Includes assigned slots, or current settings if no slots are assigned. |
| Undo last update | Restores the previous firmware and the settings from that backup. Newer saved settings are replaced too. |

Installation verifies a complete recovery backup before changing the guitar. Keep USB connected until it finishes. **Open backups** shows the local backups and transfer logs.

## Using the guitar without the app

- Hold **both bottom buttons together** for five seconds to cycle occupied slots.
- Hold only the **bottom Start button** for five seconds to switch between the selected preset and original lighting.
- Hold the **button above Start** for five seconds to switch between controller and native keyboard mode. The current slot stays selected.
- Release before repeating either hold. The saved keys work in native keyboard mode without FretGlow running.

The app's **Keyboard** switch types while the app is running. **F8** stops that app mode. To exit native keyboard mode, hold the **button above Start** for five seconds.

## Manual files

**Guitar setup → Manual file options → Export file** makes a `.uf2` containing assigned slots, or current settings if no slots are assigned. Exporting does not change the guitar. **Install from file** installs a compatible exported file using the same recovery backup process.

For manual recovery, unplug USB, hold **BOOTSEL on the Pico board** while reconnecting, then release when **RPI-RP2** appears. Copy a verified `before.uf2` backup onto that drive. Keep USB connected while it copies; the drive disappears when the guitar restarts. The circular gameplay buttons are not BOOTSEL.
