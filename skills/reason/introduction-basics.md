# Reason 13: Introduction & Basics
Based on Reason 13.4 documentation.

A practical reference for working in Reason — authorization, the rack/sequencer paradigm, UI conventions, modifier keys, and the on-screen piano. Master these basics first; every other skill builds on them.

## Core Concepts

### The Three Areas
Reason has three primary navigable areas. Knowing how to flip between them fast is fundamental.

| Area | Function Key | Purpose |
|------|-------------|---------|
| Main Mixer | F5 | SSL-style channel strips, sends, master |
| Rack | F6 | Devices (instruments, FX, utilities) and signal routing |
| Sequencer | F7 | Tracks, clips, automation, arrangement |

- Press a single key (F5/F6/F7) to maximize that area
- Press two keys together (e.g. F5+F6) for a combined view
- Press all three together for an equal split
- Click inside an area to give it focus — a thin blue rectangle indicates the focused area

### Other Useful Function Keys

| Key | Window |
|-----|--------|
| F2 | Spectrum EQ |
| F3 | Device Palette (toggle show/hide) |
| F4 | On-screen Piano Keys |
| F8 | Edit Area |
| F9 | Browser |

### Authorization Model
- Account-based via Reason Studios login (Welcome dialog at first launch)
- Once authorized online, runs offline up to **1 month** — the window auto-renews any time the app launches with internet
- **Long-term authorization**: licensed Reason 13 owners and annual Reason+ subscribers can authorize up to **3 computers** for **1 year** of offline use
  - Preferences > Account > "Add long-term authorization"
  - Free a slot via "Remove long-term authorization" (or contact support if all machines are inaccessible)

### Demo Mode
You're in Demo Mode if there's no valid license/subscription, or if the auth state has expired. The Demo Mode LED lights on the Transport Panel.

**Demo Mode restrictions** (memorize these — they trip up users):
- No audio export or bouncing mixer channels to disk
- Only built-in devices work — installed Rack Extensions are unavailable
- Only `.rsndemo` (Reason Demo Song) files open — standard `.reason` songs won't open
- Everything else still works (you can still tinker)

### Additional Content (Rack Extensions & ReFills)
Install via the **Reason Companion app** (separate app, requires internet):
- **Devices tab** → install individual REs or "Install All"
- **ReFills tab** → individual or bulk install
- **Restart Reason** afterward to activate new content

Storage paths:
- Rack Extensions (macOS): `~/Library/Application Support/Propellerhead Software/Optional REs`
- Rack Extensions (Windows): `C:\Users\[user]\AppData\Roaming\Propellerhead Software\Optional REs`
- ReFills (both): `Music > Reason Studios > ReFills`

### Updates
- Auto-checks at launch (within current major version only — no auto-jump from 12.x to 13.x)
- Manual check: Help menu (Windows) / Reason menu (macOS)
- Update bar in song doc offers immediate or deferred install
- After download: "Restart and Install Now" or defer until you quit

### Platform
Windows 10/11 (64-bit) or macOS 10.15 Catalina or later (64-bit). Layouts are essentially identical across platforms.

## Common Operations

### Selecting, Focus, and Navigation
- **Click inside an area** to focus it (blue rectangle border)
- **Click-drag a navigator frame** to scroll a section; click outside the frame to jump there
- **Hand Tool**: click the wooden rack side panels, or activate from Sequencer toolbar — then click-drag to pan

### Undo / Redo
- **Cmd/Ctrl+Z** — Undo
- **Cmd/Ctrl+Y** — Redo
- Multiple levels available — sequential history
- The Edit menu shows the named action: "Undo [Action Name]"
- **Pitfall**: Performing a new action after undoing clears the redo list. Don't expect to recover redo state once you've moved on.

### Context Menus (Right-click)
Right-click is your fastest path to most operations. Menus are tailored per context:

| Right-click on... | You get |
|-------------------|---------|
| Parameter | Automation, MIDI/keyboard assignment |
| Device | Cut/Copy/Paste/Delete/Duplicate, Device Groups, routing, pattern/patch ops, Track creation, color |
| Channel Strip | Device-style ops + Send FX creation, settings copy/paste, Insert FX management |
| Sequencer (track/clip/event) | Track, clip, and event editing |

**Do this**: Right-click before hunting through menus.
**Don't**: Assume operations live only in the menu bar.

### Tool Tips
Hover over any control → name and current value appear. Can be disabled in Preferences if they get in the way.

### Renaming, Deleting, Duplicating
Use the right-click menu on the target object (device, track, clip). Cut/Copy/Paste/Delete/Duplicate are exposed there rather than buried in menu bars.

## Parameter Editing

This is one of the most leverage-heavy parts of the program. Same conventions across nearly every control.

### Knobs
- **Drag vertically** to turn (up = clockwise/increase)
- **Shift+drag** for fine/precision adjustment
- **Cmd/Ctrl+click** to reset to default

### Faders / Sliders
- Click handle and drag, OR click anywhere on the track to jump
- **Shift+drag** for precision
- **Cmd/Ctrl+click** to reset

### Numerical displays
- Use spin buttons, OR click and drag the value vertically (coarse adjustment)

### Alpha-numeric (text-list) controls
- Use spin buttons, OR click-hold the display to pop a list selector

### Multi-mode buttons / selectors
- Click to cycle through modes
- Or click directly on the desired mode label
- Switch-style controls support click-drag

## Modifier Key Reference

| Modifier | Effect |
|----------|--------|
| Shift | Precision on knobs/faders; symmetrical zoom; refined scroll |
| Cmd/Ctrl + click | Reset parameter to default |
| Cmd/Ctrl + click on Mixer/Rack buttons | Detach window |
| Cmd/Ctrl + Shift + F | Focus the Device Palette filter field |
| Cmd/Ctrl + Z / Y | Undo / Redo |

## Scrolling & Zooming

### Wheel Mouse
| Gesture | Action |
|---------|--------|
| Spin | Vertical scroll |
| Shift + spin | Horizontal scroll |
| Cmd/Ctrl + spin | Horizontal zoom (sequencer) |
| Cmd/Ctrl + Shift + spin | Vertical zoom |

### Trackpad
| Gesture | Action |
|---------|--------|
| Two-finger swipe | Scroll |
| Pinch | Horizontal zoom |
| Cmd/Ctrl + Shift + pinch | Vertical zoom |

### Other Zoom Tricks
- **+ / -** buttons adjust track heights
- **Song Navigator** resize handles → horizontal zoom
- **Z** key — toggle zoom-to-selection
- **Double-click a horizontal divider** — maximizes the adjacent area; double-click a divider to open Rack/Sequencer

## On-Screen Piano Keys (F4)

Useful when you don't have a MIDI controller plugged in, or want to test a patch quickly.

### Opening
- **F4**, OR Windows menu → "Show On-screen Piano Keys", OR Keys button on sequencer Transport
- Window floats on top of others

### Two Modes

**Mouse Mode**
- Click keys with the mouse
- Window is resizable horizontally and vertically (changes range and key size)
- Click position on a key sets velocity — higher clicks = lower velocity

**Computer Keys Mode**
- Play with the QWERTY keyboard
- Window is fixed size — shows 18 notes (C to F)
- Layout mirrors a real piano: `A` = C, `W` = C#, etc., continuing through F
- Customize the mapping in Preferences > Advanced

### Computer Keys Cheat Sheet

| Key | Function |
|-----|----------|
| A, S, D, F... | White keys (C, D, E, F...) |
| W, E, T, Y, U... | Black keys (C#, D#, F#, G#, A#) |
| Z | Octave down |
| X | Octave up |
| Shift (held while playing) | Sustain (like a pedal) |
| 1-0 | Velocity (1=1, 8=98 default, 0=127) |

Velocity range in Computer Keys Mode: 40–127 (or type a value into the Velocity box).

### Useful Window Buttons
- **Sustain** button — alternative to holding Shift
- **Hold** — keeps clicked keys pressed
- **Repeat** — repeats the last clicked note as quarter notes at current tempo (great for tweaking patch parameters in real time)
- **Velocity Variation** — None, Light (±5%), Medium (±10%), Heavy (±25%) — adds humanization

### Range Navigation
- **Mouse Mode**: arrow buttons next to the Keyboard Navigator, or drag the green range area
- **Computer Keys Mode**: Z / X keys (or Z / X buttons)
- Total range: 10 octaves (C-2 to E8) — green strip in the navigator shows where you are; gray strips show which keys actually produce sound

## Common Pitfalls

### macOS Function Keys (F1, F2, ..., F9)
By default macOS uses F-keys for hardware controls (volume, brightness). Reason's whole navigation scheme depends on F5/F6/F7.

**Fix once**: System Preferences (or System Settings) > Keyboard → enable **"Use F1, F2, etc. keys as standard function keys"**. Visit Accessibility → Keyboard to remove conflicting OS shortcuts.

**Don't**: Try to use Fn+F5 every time — you'll wear it out fast.

### Demo Mode Surprises
- "Why won't my .reason song open?" → You're probably in Demo Mode (only `.rsndemo` opens)
- "Where are my Rack Extensions?" → Demo Mode hides them; check the Transport Panel LED
- "Why can't I export?" → Same root cause

### Redo Is Fragile
After undoing several steps, a single new action (even a click that nudges a fader) clears the redo stack. Decide before you proceed.

### Reset Is Cmd/Ctrl-click, Not Right-click
Many DAWs use right-click to reset a parameter. In Reason, right-click opens the context menu — use **Cmd/Ctrl+click** to reset.

### Precision Editing
Default knob/fader drag is coarse. **Always Shift+drag** when fine-tuning sends, EQ frequencies, or anything where small changes matter.

### Computer Keys Mode Window
The piano keys window cannot be resized while in Computer Keys Mode. Switch to Mouse Mode if you want to drag the window edges.

## Quick Reference: The Conventions That Apply Everywhere

These hold across the rack, sequencer, mixer, and most plugins/devices:

1. **Right-click → context menu** is the fastest path
2. **Shift = precision** on any draggable parameter
3. **Cmd/Ctrl+click = reset to default**
4. **F5 / F6 / F7 = navigate the three areas** (combine for split views)
5. **Hover for tool tip** showing name + current value
6. **Click to focus an area** before issuing focus-sensitive shortcuts
7. **Cmd/Ctrl+Z / Cmd/Ctrl+Y** for undo/redo, but commit before redo-stack-clearing actions
8. **Cmd/Ctrl+click Mixer/Rack buttons** to detach windows (useful with multiple monitors)

## Relationships to Other Reason Topics

- **Rack work**: parameter conventions (Shift, Cmd/Ctrl+click, right-click) apply to every device knob and fader
- **Sequencer work**: F7 to focus, Z for zoom-to-selection, Cmd/Ctrl+spin for horizontal zoom; right-click clips/events for editing
- **Mixer work**: Channel-strip context menus contain Send FX, Insert FX, settings copy/paste — most mixer ops live there
- **Browser (F9)**: Cmd/Ctrl+Shift+F focuses filter fields; drag-and-drop into the rack/sequencer
- **Piano Keys (F4)**: feeds whichever track has MIDI input focus — focus the target track first
