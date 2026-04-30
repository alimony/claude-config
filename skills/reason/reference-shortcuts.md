# Reason 13: Menus, Dialogs & Key Commands
Based on Reason 13.4 documentation.

This is a quick-reference cheat sheet for menu structure, key dialogs, and all keyboard shortcuts in Reason 13. Most useful for finding "what's the shortcut for X?" or "where is feature Y in the menus?"

---

## Most Useful Shortcuts (Learn These First)

| Shortcut (mac / win) | Action |
|---|---|
| **Spacebar** | Play / Stop toggle |
| **Cmd+Z / Ctrl+Z** | Undo |
| **Cmd+S / Ctrl+S** | Save |
| **Cmd+T / Ctrl+T** | Create Audio Track |
| **Cmd+I / Ctrl+I** | Create Instrument |
| **Cmd+E / Ctrl+E** | Create Effect |
| **F5 / F6 / F7** | Maximize Mixer / Rack / Sequencer |
| **Tab** | Flip Rack front/rear |
| **Q / W / E / R** | Arrow / Pencil / Eraser / Razor tool |
| **Cmd+K / Ctrl+K** | Quantize |
| **Cmd+J / Ctrl+J** | Join clips / notes |
| **L** | Toggle Loop |
| **S** | Toggle Snap |
| **M** | Mute / Unmute clips or notes |
| **F9** | Show / hide Browser |
| **Cmd+Return / Ctrl+Return** | Record |
| **Numeric 4 / 5** | Rewind / Fast Forward |
| **Cmd+D / Ctrl+D** | Duplicate |
| **Return** | Open selected clip |
| **Esc** | Close open clip |

---

# Part 1: Menu Reference

Reason's menus are organized roughly: Reason (mac) / File / Edit / Create / Options / Window / Help. The Edit menu is contextual — it changes content based on what's selected.

## Reason Menu (macOS only)

- **About Reason** — version and credits
- **Preferences** — opens the comprehensive Preferences dialog (see Part 2)
- **Open Reason Companion** — launches the Companion app for Rack Extensions and Sound Packs
- **My Account** — opens web portal for products and downloads
- **Check for Updates** — server-side update verification
- **Quit and Log out** — exit and remove credentials
- **Quit Reason** (Cmd+Q) — exit with unsaved changes warning

On Windows, Preferences and Quit live under the Edit and File menus respectively.

## File Menu

Important items:

- **New** — creates song based on Default Song preference
- **New from Template** — template-based song creation
- **Open** (Authorized) / **Open Demo Song** (Demo Mode)
- **Close** — window closure with save prompts
- **Save** / **Save As** — Save As prompts for filename
- **Save and Optimize** — removes fragmented/unused audio data, reduces file size
- **Song Information** — metadata, contact info, comments (see Part 2)
- **Song Self-Contain Settings** — configure which samples/REX files are embedded in the .reason file
- **Import Audio File** — browser-based audio import
- **Import MIDI File** — Standard MIDI File (SMF) import
- **Export MIDI File** — SMF export with track selection
- **Save Device Patch As** — format-specific patch saving (.cmb Combinator, .zyp Subtractor, .thor, .repatch, etc.)
- **Export Song / Loop as Audio** — WAV/AIFF mixdown
- **Bounce Mixer Channels** — render individual mixer channels to audio
- **Export REX as MIDI File** — convert Dr. Octo Rex slices to MIDI notes
- **Export Device Remote Info** — documents remotable parameters
- **Recent Songs** — quick access to last 8 files
- **Exit** (Windows) — exit application

## Edit Menu

The Edit menu is highly contextual — its items change based on what is currently selected (clip, device, note, mixer channel, sample, etc.).

### Undo / Redo
- **Undo** (Cmd/Ctrl+Z) — reverses actions; transport commands are NOT undoable
- **Redo** (Cmd/Ctrl+Y) — reapplies undone actions

### Clipboard
- **Cut / Copy / Paste** (Cmd/Ctrl+X/C/V)
- **Cut / Copy / Paste Tracks and Devices**
- **Cut / Copy / Paste Channels and Tracks**
- **Copy / Paste Patch**
- **Paste with Shift held** = paste with auto-routing

### Selection / Duplication
- **Select All** (Cmd/Ctrl+A)
- **Select All Devices / Tracks / Channels / Clips**
- **Select All in Device Group**
- **Duplicate Tracks and Devices** — full replication including settings
- **Sort Selected Device Groups** — rearranges by selection order

### Device operations
- **Auto-route Device** — forces automatic connection
- **Disconnect Device** — removes all audio/CV connections
- **Combine** / **Uncombine** — group devices into Combinator or extract them
- **Reset Device** — restore default parameters

### Pattern operations (Redrum / Matrix / Dr. Octo Rex)
- **Cut / Copy / Paste / Clear Pattern**
- **Shift Pattern Left / Right**
- **Shift Drum Left / Right** (Redrum)
- **Shift Pattern Up / Down** (Matrix — semitone transposition)
- **Randomize Pattern / Drum**
- **Alter Pattern / Drum**
- **Random Sequencer Pattern** (Thor)
- **Invert Pattern** (RPG-8)

### Sampler functions (NN-19 / NN-XT / Redrum)
- **Browse Samples** — load .wav, .aif, .mp3, .aac, .m4a, .wma, SoundFonts, REX
- **Automap Samples** (NN-19)
- **Delete Sample** / **Remove Sample** / **Delete Unused Samples**
- **Split / Delete Key Zone** (NN-19)
- **Reload Samples** (NN-XT)
- **Add / Copy / Paste / Duplicate Zones** (NN-XT)
- **Select All Zones** (NN-XT)
- **Copy Parameters to Selected Zones** (NN-XT)
- **Sort Zones by Note / Velocity** (NN-XT)
- **Group Selected Zones** (NN-XT)
- **Set Root Notes from Pitch Detection** (NN-XT)
- **Automap Zones / Automap Zones Chromatically** (NN-XT)
- **Create Velocity Crossfades** (NN-XT)

### Patch / Loop management
- **Browse Patches** — device-specific patch loading
- **Browse Loops** (Dr. Octo Rex)

### Sequencer / timeline
- **Copy Loop to Track** (Dr. Octo Rex) — convert REX slices to notes
- **Copy Pattern to Track** (Redrum / Matrix)
- **Insert Bars Between Locators** — insert empty bars, push events forward
- **Remove Bars Between Locators** — delete material, consolidate events
- **Set Loop to Selection** (Cmd/Ctrl+L) / **Set Loop to Selection and Start Playback** (P)
- **Open in Edit Area** — launch clip editor (Multi Lanes for multi-clip)

### Clip operations
- **Bounce in Place** — render notes/audio with insert FX to a new audio track
- **Bounce Clips to New Samples** (audio) — convert clips to editable samples
- **Bounce Clip to Disk** (audio) — export as WAV/AIFF
- **Bounce Clips to New Recordings** (audio)
- **Bounce Clip to REX Loop** (single take audio)
- **Bounce Audio Clips to MIDI** — monophonic audio-to-notes
- **Stretch and Transpose Type** (audio) — algorithm choice
- **Correct Pitch / Reset Pitch** (Pitch Edit Mode) — vocal correction
- **Split At Slices / Split At Notes** (single-take audio)
- **Revert Slices / Revert Notes**
- **Enable / Disable Stretch** (audio) — tempo follow toggle
- **Delete Unused Recordings** (audio)
- **Normalize Clips** (audio)
- **Reverse**
- **Stretch Type for New Recordings** (audio)

### Arrangement
- **Mute / Unmute Clips** (M)
- **Crop Events to Clips** — trim out-of-bounds notes/automation
- **Add / Remove Labels from Clips**
- **Clip Color** / **Channel Color** / **Track Color**
- **Adjust Alien Clips to Lane**
- **Join Clips** (Cmd/Ctrl+J)

### Mixer (Main Mixer)
- **Copy / Paste Channel Settings** — Dynamics, EQ, FX, Sends
- **Route to** — output bus creation and routing
- **Create Parallel Channel**
- **Clear Insert FX**
- **Reset All Channel Settings**

### Note / automation editing
- **Select Notes of Same Pitch**
- **Move / Duplicate Selected Notes to New Lane**
- **Transpose** (Note Tools) — pitch + randomization
- **Note Velocity** — scaling and ramps
- **Note Length** — duration scaling, legato
- **Alter Notes** — inter-note pitch modification
- **Randomize Positions** — timing variation
- **Quantize** (Cmd/Ctrl+K)
- **Quantize Setup** — strength configuration
- **Crossfade** (X) — audio clip transitions
- **Convert Pattern Automation to Notes**
- **Convert Block Track to Song Clips**
- **Commit to Groove**
- **New Note Lane**
- **Merge Note Lanes on Tracks** (Cmd/Ctrl+R)
- **Get Groove From Clip**

### Sample management (Song Samples browser)
- **Edit Sample** — open Sample editor
- **Duplicate Sample(s)**
- **Export Sample(s)** — disk export
- **Delete Sample(s)**

### Control surface mapping
- **Edit Keyboard Control Mapping** — assign computer keys to parameters
- **Clear Keyboard Control Mapping**
- **Clear All Keyboard Control Mappings for Device**
- **Edit Remote Override Mapping** — MIDI controller assignment
- **Clear Remote Override Mapping**
- **Clear All Remote Override Mappings for Device**
- **Copy / Paste Remote Override Mappings** — across devices

### Navigation
- **Go To Track for** — jump to device's track
- **Go to Product Page** (Rack Extension)

## Create Menu

The Create menu lists all instruments, effects, utility devices, players, and Rack Extensions that can be created. Items appear in the rack at the position of the focused device.

Key items:
- **Instruments** — Subtractor, Thor, NN-19, NN-XT, Redrum, Kong, Malstrom, ID8, Europa, Grain, Algoritm, Monotone, Combinator
- **Effects** — Scream 4, RV7000 / RV-7, BV512, ECF-42, Pulveriser, The Echo, Alligator, Audiomatic, Polar, Neptune, MClass devices, etc.
- **Players** — Scales & Chords, Note Echo, Dual Arpeggio, Drum Sequencer
- **Utilities** — Mix Channel, Audio Track, Mixer 14:2, Line Mixer 6:2, Spider CV, Spider Audio, Reason Drum / Bass / Synth Hardware Interface
- **Track creation** — Audio Track (Cmd/Ctrl+T), Instrument (Cmd/Ctrl+I), Effect (Cmd/Ctrl+E)

## Options Menu

Important toggles and settings:
- **Snap to Grid** (S)
- **Loop On/Off** (L)
- **Click / Metronome** (C)
- **Pre-count Click**
- **Quantize Notes During Recording**
- **Reduce Cable Clutter** (toggle Hide Cables)
- **Big Meters** — show large output meters
- **Sync** — choose internal / MIDI clock / MTC sync
- **MIDI Control Surfaces** — quick access to surface management
- **Surface Locking** — lock/unlock controllers to specific devices

## Window Menu

- **Toggle Stack windows / Tile windows**
- Lists all open Reason song windows for switching
- Window-specific show/hide commands (also bound to F-keys)

## Help Menu

- **Reason Help** — opens online documentation
- **Operation Manual / Quickstart**
- **Visit reasonstudios.com**
- **Show License Agreement**
- **Open Tutorial Songs**

---

# Part 2: Key Dialogs

## Preferences

The Preferences dialog is the central hub for configuring Reason. It has tabs for User Interface, Browsing, Audio, MIDI, Sync, Other Controls, Folders, and Account.

### User Interface tab
| Option | What it does |
|---|---|
| Trigger notes while editing | Plays notes as you move them |
| Ask before changing audio clip mode or stretch type | Confirmation prompt |
| Return to last start position on stop | Sequencer position memory |
| Show parameter value tool tip | Hover tooltips for params |
| Show automation indication | Green frame around automated parameters |
| Mouse Knob Range | Sensitivity: Normal / Precise / Very Precise |
| Automation Cleanup | Reduces redundant points during recording/drawing |
| Hide Cables | None / Selected devices / Auto-routed / All hidden |
| Theme | Visual style (requires restart) |
| Language (Win) | Localization (requires restart) |
| Monitoring | Automatic / Manual / External |

### Browsing tab
- **Load default sound in new devices** — auto-load patch on creation
- **Browsing starts in default sound folder** — browser location for new devices
- **Self-contain samples when loading from disk** — auto-embed samples
- **Cloud folders** — manage warning before adding cloud folders as Shortcuts
- **Default song** — template song
- **Use Side Panel Browser in new songs**
- **Open last song on startup**
- **Open Reason Companion on startup**

### Audio tab
| Option | Purpose |
|---|---|
| Audio Device | ASIO (Win) or Core Audio (mac) device selection |
| Active inputs / outputs | Channel count, with "Channels..." button |
| Clock Source (ASIO) | Sync source |
| Control Panel | Open hardware-specific driver UI |
| Sample Rate | I/O resolution |
| Master Tune | Global tuning ±100 cents from 440 Hz |
| Buffer Size | Latency vs. stability tradeoff |
| Input / Output Latency | Reported delay (read-only display) |
| Latency Adjustment | Manual compensation for monitoring |
| Max audio threads | CPU core allocation |
| Render audio using audio card buffer size | Large batch processing toggle |
| Play in background | Continue audio when app loses focus |

### MIDI tab
- **Remote keyboards and control surfaces** — added surfaces with Use/Edit/Delete
- **Auto-detect surfaces** — scans USB/MIDI
- **Use no master keyboard** — disables MIDI note input
- **Add control surface** — Manufacturer / Model / MIDI Input / Output / Name
  - Generic options for unlisted devices: MIDI Control Keyboard / Surface / Keyboard
  - Multichannel variants for multi-channel MIDI
- **Master Keyboard** — designate primary keyboard for sequencer
- **Easy MIDI Inputs** — automatic unused-MIDI-port detection

### Sync, Other Controls, Folders, Account tabs
- **Sync** — clock source for external sync (MIDI clock, MTC)
- **Other Controls** — additional remote/scripting controls
- **Folders** — sample / patch / Rack Extension search paths
- **Account** — sign-in, authorization, registered products

## Other Important Dialogs

| Dialog | Purpose |
|---|---|
| **Song Information** | Add contact info, comments, metadata to song |
| **Song Self-Contain Settings** | Choose which samples/REX files embed in song file |
| **Authorization** | Sign-in for activation, online/offline auth |
| **Browser** | File/patch/sample/loop navigator with shortcuts and search |
| **Export MIDI File** | MIDI export with track and automation options |
| **Transpose Notes** | Pitch alteration with optional randomization |
| **Note Velocity** | Scale, set, ramp velocity |
| **Note Length** | Duration scaling and legato |
| **Alter Notes** | Inter-note pitch modification |
| **Randomize Positions** | Timing offsets within tick range |
| **Quantize Setup** | Grid resolution and quantize amount |

---

# Part 3: Keyboard Shortcuts (Cheat Sheet)

Notation: `mac / windows`. Where only one form is shown, both platforms use the same key (e.g. `F5`, `Spacebar`, single-letter tools).

## Window / Panel Navigation

| Shortcut | Action | Notes |
|---|---|---|
| F5 | Maximize / restore Main Mixer | |
| F6 | Maximize / restore Rack | |
| F7 | Maximize / restore Sequencer | |
| F2 | Show / hide Spectrum EQ Window | |
| F3 | Show / hide Device Palette | |
| F4 | Show / hide On-screen Piano Keys | |
| F8 | Show / hide Edit Area | Clip editor |
| F9 | Show / hide Browser | |
| Tab | Toggle Rack front / rear view | Cables on the back |

## File Operations

| Shortcut (mac / win) | Action |
|---|---|
| Cmd+N / Ctrl+N | New Song |
| Cmd+O / Ctrl+O | Open Song |
| Cmd+S / Ctrl+S | Save Song |
| Shift+Cmd+S / Shift+Ctrl+S | Save As |
| Cmd+Option+I / Shift+Ctrl+I | Import Audio File |

## Edit / Clipboard

| Shortcut (mac / win) | Action |
|---|---|
| Cmd+Z / Ctrl+Z | Undo |
| Cmd+Y / Ctrl+Y | Redo |
| Cmd+X / Ctrl+X | Cut |
| Cmd+C / Ctrl+C | Copy |
| Cmd+V / Ctrl+V | Paste |
| Cmd+D / Ctrl+D | Duplicate |
| Cmd+A / Ctrl+A | Select All |
| Delete / Backspace | Delete (with warning) |
| Cmd+Delete / Ctrl+Delete | Delete without warning |

## Device / Track Creation

| Shortcut (mac / win) | Action |
|---|---|
| Cmd+T / Ctrl+T | Create Audio Track |
| Cmd+I / Ctrl+I | Create Instrument |
| Cmd+E / Ctrl+E | Create Effect |
| Shift+Cmd+M / Shift+Ctrl+M | Create Mix Channel |
| Cmd+G / Ctrl+G | Route to New Output Bus |

## Transport (numeric keypad-centric)

| Shortcut | Action | Notes |
|---|---|---|
| Spacebar | Play / Stop toggle | Most useful |
| Numeric Enter | Play | |
| Shift+Return / Numeric 0 | Stop | |
| Cmd+Return / Ctrl+Return / Numeric * | Record | |
| Numeric 4 | Rewind | |
| Numeric 5 | Fast Forward | |
| Numeric 7 | Go back one bar | |
| Numeric 8 | Move forward one bar | |
| Numeric + | Tempo up | |
| Numeric – | Tempo down | |

## Tool Selection

The single-letter tool keys work in the sequencer / edit area. Cycle through tools by pressing repeatedly when applicable.

| Key | Tool | Used for |
|---|---|---|
| **Q** | Arrow (Selection) | Select, move, resize clips/notes |
| **W** | Pencil | Draw clips, notes, automation |
| **E** | Eraser | Delete clips, notes, automation |
| **R** | Razor | Split / cut clips |
| **T** | Mute | Mute / unmute clips/notes |
| **Y** | Magnifying Glass | Zoom |
| **U** | Hand | Scroll / pan |
| **I** | Speaker | Audition (Audio Edit Mode) |

## Sequencer Operations

| Shortcut (mac / win) | Action |
|---|---|
| Return | Open selected clip in Edit Area |
| Esc | Close open clip |
| Cmd+K / Ctrl+K | Quantize |
| Cmd+J / Ctrl+J | Join selected clips / notes |
| Cmd+R / Ctrl+R | Merge Note Lanes |
| M | Mute / Unmute clips or notes |
| S | Toggle Snap |
| C / Numeric 9 | Toggle Metronome (Click) |
| L / Numeric / | Toggle Loop |
| Cmd+L / Ctrl+L | Set Loop to selected clips |
| P | Set Loop to selection AND start playback |
| X | Crossfade overlapping audio |
| Option+X / Alt+X | Split clips at song position |
| B | Toggle Block / Song view |
| F | Toggle Follow Song |
| Z | Zoom to selection |
| Shift+Z | Zoom out / restore |
| H or Cmd++ / Ctrl++ | Horizontal zoom in |
| G or Cmd+– / Ctrl+– | Horizontal zoom out |

## On-Screen Piano Keys (Computer Keys mode)

When the on-screen piano (F4) is set to receive computer keyboard input.

| Key | Action |
|---|---|
| Shift | Sustain |
| Z | Octave Down |
| X | Octave Up |
| 1 | Velocity 1 |
| 2 | Velocity 14 |
| 3 | Velocity 28 |
| 4 | Velocity 42 |
| 5 | Velocity 56 |
| 6 | Velocity 70 |
| 7 | Velocity 84 |
| 8 | Velocity 98 |
| 9 | Velocity 112 |
| 0 | Velocity 127 |

## Pattern Devices

### Redrum

| Shortcut (mac / win) | Action |
|---|---|
| Cmd+X / Ctrl+X | Cut Pattern |
| Cmd+C / Ctrl+C | Copy Pattern |
| Cmd+V / Ctrl+V | Paste Pattern |
| Cmd+J / Ctrl+J | Shift Pattern Left |
| Cmd+K / Ctrl+K | Shift Pattern Right |
| Cmd+R / Ctrl+R | Randomize Pattern |
| Shift+Cmd+P / Shift+Ctrl+P | Alter Pattern |

### Matrix

Same as Redrum, plus:

| Shortcut (mac / win) | Action |
|---|---|
| Shift+Cmd+U / Shift+Ctrl+U | Shift Pattern Up (semitone) |
| Shift+Cmd+D / Shift+Ctrl+D | Shift Pattern Down (semitone) |

### Dr. Octo Rex

| Shortcut (mac / win) | Action |
|---|---|
| Cmd+X / Ctrl+X | Cut Loop |
| Cmd+C / Ctrl+C | Copy Loop |
| Cmd+V / Ctrl+V | Paste Loop |

### RPG-8

Shift Pattern and Randomize functions follow the same pattern conventions.

### Thor (Step Sequencer)

| Action | Notes |
|---|---|
| Random Sequencer Pattern | Property-specific randomization |

## Sampler Devices

### NN-XT

| Shortcut (mac / win) | Action |
|---|---|
| Cmd+A / Ctrl+A | Select All Zones |
| Cmd+C / Ctrl+C | Copy Zones |
| Cmd+V / Ctrl+V | Paste Zones |

NN-19 and Redrum sample-loading functions are accessed via the Edit menu (no dedicated keyboard shortcuts).

## Modifier Key Conventions

Reason follows standard cross-platform conventions. The documentation states "Mac key(s) to the left and Windows key(s) to the right of the slash."

| Mac | Windows | Typical role |
|---|---|---|
| Cmd | Ctrl | Primary modifier — menu commands, shortcuts |
| Option | Alt | Secondary — alternate behavior, fine adjustment, copy-on-drag |
| Shift | Shift | Selection extend, constrain, alternate paste (with auto-routing) |
| Ctrl | (right-click) | Context menu on Mac single-button mouse |

### Common modifier patterns

| Behavior | Modifier |
|---|---|
| Fine knob adjustment | Shift+drag (also affected by Mouse Knob Range pref) |
| Copy clip on drag | Option+drag / Alt+drag |
| Constrain to axis (drag) | Shift+drag |
| Paste with auto-routing | Shift+Paste |
| Delete without warning | Cmd+Delete / Ctrl+Delete |
| Reset knob to default | Cmd+click / Ctrl+click on the knob |
| Add to selection | Shift+click |
| Toggle selection | Cmd+click / Ctrl+click |

---

# Part 4: Customizing Key Commands

Reason 13 supports remapping keys to device parameters via **Edit Keyboard Control Mapping**, accessed from the Edit menu or context menu on any controllable parameter.

## Workflow

1. Right-click (or Ctrl-click on Mac) a parameter on a device
2. Choose **Edit Keyboard Control Mapping**
3. Press the desired key combination
4. The parameter is now controllable from that key

## Related menu items

- **Edit Keyboard Control Mapping** — assign a computer key to a parameter
- **Clear Keyboard Control Mapping** — remove a single mapping
- **Clear All Keyboard Control Mappings for Device** — reset all keys for one device

## MIDI Controller Mapping (Remote Override)

For MIDI hardware, use **Remote Override**:

- **Edit Remote Override Mapping** — bind a MIDI message to a parameter
- **Clear Remote Override Mapping** — remove a single MIDI mapping
- **Clear All Remote Override Mappings for Device** — reset all MIDI mappings on one device
- **Copy / Paste Remote Override Mappings** — duplicate mappings between devices

## Note on customization scope

Reason does NOT expose a global key-binding editor for built-in shortcuts (transport, tools, file operations). Those are fixed. Customization is limited to:

1. **Keyboard Control** — computer keys mapped to device parameters
2. **Remote Override** — MIDI hardware mapped to device parameters

For documentation of remote-controllable parameters, use **File > Export Device Remote Info**.

---

# Part 5: Quick Reference by Workflow

## "I just opened Reason, where do I start?"

| Action | Shortcut |
|---|---|
| Create a new song | Cmd/Ctrl+N |
| Open the browser | F9 |
| Create an instrument track | Cmd/Ctrl+I |
| Create an audio track | Cmd/Ctrl+T |
| Maximize the rack | F6 |
| Maximize the mixer | F5 |
| Show on-screen piano | F4 |

## "I'm recording — transport workflow"

| Action | Shortcut |
|---|---|
| Play / Stop | Spacebar |
| Record | Cmd/Ctrl+Return or Numeric * |
| Rewind | Numeric 4 |
| Loop on/off | L |
| Set loop to selection + play | P |
| Click on/off | C |
| Snap on/off | S |

## "I'm editing notes / clips"

| Action | Shortcut |
|---|---|
| Arrow tool | Q |
| Pencil tool | W |
| Eraser tool | E |
| Razor tool | R |
| Mute clips | M |
| Quantize | Cmd/Ctrl+K |
| Join clips | Cmd/Ctrl+J |
| Open clip | Return |
| Close clip | Esc |
| Crossfade | X |
| Split at position | Option/Alt+X |

## "I'm working in the rack"

| Action | Shortcut |
|---|---|
| Flip rack front/rear | Tab |
| Maximize rack | F6 |
| Show device palette | F3 |
| Create instrument | Cmd/Ctrl+I |
| Create effect | Cmd/Ctrl+E |
| Duplicate device | Cmd/Ctrl+D |
| Combine selected | Edit > Combine |
| Reset device | Edit > Reset Device |

## "I'm mixing"

| Action | Shortcut |
|---|---|
| Maximize mixer | F5 |
| Show Spectrum EQ | F2 |
| Create mix channel | Shift+Cmd/Ctrl+M |
| Route to output bus | Cmd/Ctrl+G |
| Copy channel settings | Edit menu (contextual) |

---

# Notes

- **Numeric keypad** is heavily used for transport. Laptop users without a numeric keypad rely on Spacebar, Cmd/Ctrl+Return, and on-screen Transport buttons.
- **Tool letters (Q W E R T Y U I)** form a contiguous row across QWERTY keyboards — they're designed to be hit with the left hand while right hand uses the mouse.
- **F-keys (F2-F9)** govern panel visibility. F5/F6/F7 are the most-used (Mixer/Rack/Sequencer maximize).
- The **Edit menu is contextual** — items appear based on what's selected. If a shortcut "doesn't work," check that the relevant context (clip / device / sample) is selected.
- **Transport commands are NOT undoable** — playing or stopping cannot be undone with Cmd/Ctrl+Z.
- For complete Edit-menu detail on a per-context basis, the documentation organizes items by Sampler functions, Pattern operations, Clip operations, etc., as listed in Part 1 above.
