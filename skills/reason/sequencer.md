# Reason 13: The Sequencer
Based on Reason 13.4 documentation.

The sequencer is where you record, arrange, and edit everything in Reason. It hosts tracks (which contain lanes, which contain clips) and works alongside the rack (devices) and mixer. The sequencer has two main views: the **Arrange Area** (overall song timeline) and the **Edit Area** (detailed clip editing). Press [F8] to toggle the Edit Area for any selected clip.

## Core Concepts

### Hierarchy
- **Track**: A horizontal row in the Track List. Belongs to one device or has a special role (Transport, Blocks).
- **Lane**: A horizontal sub-row inside a track. Tracks can have multiple lanes (note lanes, automation lanes, pattern lanes).
- **Clip**: A discrete container on a lane. Holds notes, audio, automation, or pattern data.
- **Event**: An individual note, automation point, or audio slice inside a clip.

### Track Types
| Type | Lanes | Notes |
|------|-------|-------|
| Transport Track | Tempo + Time Signature (max 2 lanes) | Always present at top |
| Audio Track | One audio lane + automation lanes | Mono or stereo recordings, takes |
| Instrument Track | Multiple note lanes + automation lanes | MIDI-capable devices, drum layering |
| Parameter Automation Track | Automation lanes only | For effects, mixers (no MIDI) |
| Blocks Track | Block automation only | Appears only when Enable Blocks active |

### Clip Types
- **Note clips**: Note events with velocity; can include performance controllers (Pitch Bend, Mod Wheel, etc.).
- **Audio clips**: Mono/stereo waveforms; may contain multiple takes on Comp Rows.
- **Parameter automation clips**: Recognizable by a cut-off top-right corner.
- **Pattern automation clips**: Bank/pattern numbers for Redrum, Matrix, Dr. Octo Rex.
- **Block automation clips**: Reference one of 32 blocks; live on the Blocks Track.

### Relationships to Rack and Mixer
- Each instrument or audio track is bound to a device in the rack. Renaming the track renames the device.
- Mixer channel strip parameters can be automated by creating a parameter automation track for the mix channel.
- Master Keyboard Input routes your MIDI controller to one track at a time (gray arrow icon). [Shift]-click the SEQ button on a mixer channel to create a track for that channel.

## Transport, Locators, and Time

### Transport Controls
| Action | Shortcut |
|--------|----------|
| Play | [Enter] (numeric) |
| Stop | [0] (numeric) or [Shift]+[Return] |
| Toggle Play/Stop | [Spacebar] |
| Record | [*] (numeric) or [Ctrl/Cmd]+[Return] |
| Rewind / Fast Forward | [4] / [5] (numeric, hold for acceleration) |
| Move forward/back one bar | [8] / [7] (numeric) |
| Go to bar start | [.] (numeric) |
| Loop on/off | [L] or [/] (numeric) |
| Click on/off | [C] or [9] (numeric) |
| Pre-count on/off | [Ctrl/Cmd]+[P] |
| Tempo up/down | [+] / [-] (numeric) |

### Loop Locators (L and R)
- Drag the L (Left) and R (Right) flags in the Ruler, or enter values in the Transport Panel.
- Jump: [1] = Left Locator, [2] = Right Locator.
- Set locators around the current selection: [Ctrl/Cmd]+[L].
- Loop+Play from Left Locator: [P].

### Tempo and Time Signature
- Tempo range: 1.000–999.999 BPM. Drag the display, type a value, or **Tap Tempo** (click repeatedly).
- Time signatures: 1/2 to 16/16, edited via the Transport Panel display.
- **Automate tempo**: [Alt]/[Option]+click the Tempo display to create a Tempo automation lane on the Transport Track. Then either record live changes or draw with the Pencil Tool.
- Audio clips auto-stretch to follow tempo changes (when stretch is enabled). Notes/automation always follow.

### Position Format
The ruler is divided into Bars.Beats.1/16th Notes.Ticks (240 ticks per 1/16 note). The Inspector position field accepts the format `x.x.x.x`, with `+` or `-` prefixes for relative moves.

### Snap
- Toggle snap: [S] or click the Snap button.
- Pick grid from dropdown: Bar, Beat, 1/16, 1/32, "Grid" (auto-scales with zoom), etc.
- **Absolute mode**: Snaps to nearest grid position.
- **Relative mode**: Steps by snap value from original position.
- Edit Area and Arrange Area can have separate snap values — useful for rough arranging at Bar resolution while editing notes at 1/16 resolution.

## Tools (Toolbar)

| Tool | Key | Use |
|------|-----|-----|
| Selection (Arrow) | [Q] | Move/resize clips and events |
| Pencil | [W] | Draw clips, notes, automation |
| Eraser | [E] | Delete clips and events (click or drag rectangle) |
| Razor | [R] | Split clips and notes |
| Mute | [T] | Toggle mute state on clips/lanes |
| Magnifying Glass | [Y] | Zoom in (click), out ([Ctrl/Cmd]+click), or marquee zoom |
| Hand | [U] | Scroll the arrange area |
| Speaker | — | Audition slices/notes |

**Modifier tricks:**
- Hold [Alt]/[Cmd] to temporarily switch to a related tool (e.g., from Selection to Pencil).
- [Alt]/[Cmd]+click with Selection Tool = Speaker Tool to audition.
- [Ctrl]/[Option]+drag a clip with Selection Tool = duplicate.
- [Ctrl]/[Option] on the Resize handle = "scale tempo" (stretches content).
- [Ctrl/Cmd]+drag with Razor = duplicate cut sections.
- Click Pencil twice to enter "Draw multiple notes" mode.

## Recording

### General Recording Procedure
1. Enable Click [C] and Pre-count [Ctrl/Cmd]+[P] as needed (set 1–4 pre-count bars in Options menu).
2. Move the Song Position Pointer to your start point.
3. Click Record (or [*] on numeric keypad). Record button turns red.
4. During pre-count, nothing is recorded.
5. Recording starts; Play button activates alongside Record.
6. Click Stop ([0], [Spacebar], or [Shift]+[Return]) when done.
7. Empty note clips auto-delete after stop. Empty audio clips do **not** auto-delete.

> **Do this:** Save the song before recording large audio files — saves are faster afterwards.
> **Don't do this:** Forget to reset clipping LEDs (red persistent indicators); they stay until clicked.

### Click and Pre-count
- Click is the metronome (first beat accented).
- Click level slider lives on the Transport Panel. **Click routes through the audio interface, not the mixer** — adjust level via the slider, not the mixer.
- Pre-count does NOT work with Ableton Link sync.
- Choose 1–2 pre-count bars for slow songs, 3–4 for fast songs.

### Audio Recording

**Setup:**
1. Select mono or stereo from the Audio Input dropdown.
2. Aim for **-12 dB** on the Input Meter (24-bit interface). Slightly higher OK on 16-bit.
3. **Adjust input level at the source** (preamp/interface gain), NOT the channel strip. The channel strip affects monitoring/playback only — recording is pre-fader.
4. Red clipping LEDs persist until clicked. Reset by clicking the Input Meter.

**Monitoring modes** (Preferences > User Interface):
- **Automatic**: Monitoring follows track selection/record-enable.
- **Manual**: You toggle monitoring with the Monitor button.
- **External**: Reason monitoring stays off (when monitoring through external hardware).

**Tuner**: Click "Enable Tuner" to switch the Input Meter to a tuner display. Sustain a note briefly for detection.

**Recording Meter Window**: Toggle via Windows menu. Shows current record-enabled audio track's levels and tuner. Arrow keys navigate between tracks. Click pitchfork for an enlarged tuner.

### MIDI / Note Recording

- An instrument track is auto-created when you add a MIDI-capable device. It already has Master Keyboard Input and a record-enabled note lane.
- Only one note lane per instrument can record at a time (unless using multiple controllers via Remote locking).
- Q Record button on the Transport quantizes notes to the grid as they're recorded.
- After Stop, clip boundaries auto-snap to nearest bar for easier arranging.
- For external MIDI gear, create a MIDI Out Device and pick port/channel.

### Loop Mode Recording

**Audio in Loop:**
1. Set Left/Right Locators around target section.
2. Enable Loop [L].
3. Click L button to jump to Left Locator.
4. Record. Each pass is saved to a separate **Comp Row** in the background.
5. Double-click the clip and press "Comp Edit" to access the Comp Editor.

**Notes in Loop:**
- New notes are **additive** — they layer on top of previous loops, all heard during recording.
- Use Alt function (see below) to make each loop a separate take.

### Multi-Take and Layered Recording

- **Dub** (audio): Creates a new audio track with duplicate channel strip + effects. Original stays unmuted; both play together.
- **Alt** (audio): Creates a new audio track and **mutes the original**. Only the newest plays.
- **Dub** (notes): Adds a new record-enabled note lane on the same track. Layers play together — great for drum overdubs.
- **Alt** (notes): Adds a new note lane and mutes the previous one. Only the newest plays.
- In Loop mode, Alt on notes splits and mutes only between the locators (not the entire lane).

> **Do this:** Use Alt for trying alternate takes (auto-A/B comparison).
> **Do this:** Use Dub for layered drum hits or doubled vocals.

### Recording Over Existing Clips

- **Audio**: New recording replaces the previous take in the same clip boundaries. The Comp Editor opens with separate takes on Comp Rows. Original audio is preserved — just switch comp rows.
- **Notes**: New notes are added to existing events (additive). If recording starts before the original clip, a larger clip is created encompassing the original. Original notes are not deleted when split by new recording.

> **Don't do this:** Recording over **masked** clip regions — masked events are permanently deleted in note clips.

### Punch Recording / Mid-Take Undo

- Press [Delete]/[Backspace] **during** note recording to delete the current clip and start a fresh one at the current position. Recording continues.
- Edit menu > "Undo Record Track" or select clip + [Delete] after stopping.

### Recording Mixdowns / Stems

1. Create a new audio track called "Mixdown" (or similar).
2. Click "Rec Source" on the Master Section device.
3. Solo the source tracks you want.
4. Set Audio Input dropdown to "Stereo" + "Master Section."
5. Aim for 0.0 dB device volume + 0.0 dB Mix Channel level (avoid clipping).
6. Record. After done, un-solo source tracks and **mute the originals** to avoid duplicate playback.

### Parameter Automation Recording

**Performance Controllers** (Pitch Bend, Mod Wheel, Sustain, Aftertouch, Breath, Expression):
- Recorded automatically alongside notes, **inside note clips**.
- Move with the clip when repositioned.
- Best for "performance" gestures.

**Track Parameter Automation:**
- Lives on dedicated Parameter Automation Lanes outside note clips.
- Moves independently from notes.
- Best for mixing and sound design.

**To record track automation:**
1. Set parameter to its desired static (default) value.
2. Activate "Automation Record Enable" on the track.
3. (Optional) Disable note lane Record Enable.
4. Record. Each parameter you tweak gets its own automation lane/clip.
5. Click Stop **twice** (or click Automation Override) for green borders to display on automated parameters.

**To record automation INSIDE note clips:**
- Options menu > "Record Automation into Note Clip" enables this mode.
- Then tweak parameters while recording notes.

**Loop mode automation**: Each new pass replaces previous values for parameters you change. Untouched parameters keep their values.

**Live Mode (Playback Override)**: Adjust an automated parameter during playback to override. Automation Override indicator lights up. Click it to revert to recorded automation.

> **Don't do this:** Record overlapping track automation and note clip automation for the same parameter — track automation overrides the note clip version, which can be confusing.

### Pattern Automation Recording (Redrum, Matrix, Dr. Octo Rex)

1. Activate "Record Enable Parameter Automation."
2. Ensure "Enable Pattern" / "Enable Loop Playback" is on.
3. Set the desired starting pattern.
4. Start recording. **No clip is created until the first pattern change.**
5. Change patterns via Bank/Pattern buttons during recording.
6. Pattern changes are quantized to the next downbeat.

> **Note:** Patterns play only where automation clips exist (no static value).
> **Tip:** Use "Convert Pattern Track to Notes" or "Copy Pattern/Loop to Track" to switch from pattern to notes for further editing.

### Tempo Automation Recording

1. Set the static tempo first.
2. [Alt]/[Option]+click Tempo display to create a Tempo automation lane.
3. Tempo display shows a green border indicating automation.
4. Record; drag tempo display up/down or use scroll wheel to change BPM (or 1/1000 BPM steps).

### Recording Tips

- **Difficult takes**: Lower tempo to record, restore tempo afterwards. Audio stretch preserves pitch; MIDI just plays back at the new speed.
- **Manual Rec mode**: Disables automatic record-enabling of selected tracks — useful when switching between recording types.

## Arranging Clips

### Creating Clips

- **Auto-created** during recording.
- **Double-click** with Selection Tool on a track lane = empty clip of current Snap length, extendable by dragging right.
- **Pencil Tool**: Click and drag on a lane to draw a clip.

### Selecting

- Click a clip to select.
- [Ctrl] (Win) / [Shift] (Mac) + click for multi-select.
- Drag a selection rectangle.
- [Ctrl/Cmd]+[A] to select all.

### Moving and Nudging

- Drag with Selection Tool. [Shift] restricts to vertical-only movement.
- Inspector Position field: numeric placement (`x.x.x.x` format).
- **Nudge by Snap**: [Ctrl/Cmd]+[Left/Right Arrow]
- **Nudge by Beat**: [Ctrl/Cmd]+[Shift]+[Left/Right Arrow]
- **Nudge by Tick**: [Ctrl/Cmd]+[Alt/Option]+[Left/Right Arrow]

### Resizing and Masking

- Drag the Resize handles on a selected clip's edges.
- **Resizing does NOT delete content — it MASKS it.** Re-enlarging the clip restores hidden events.
- Note clips show **white corners** indicating masked events. Audio masking is invisible unless you open the Comp Editor.
- Inspector's Length field for numeric resize.
- Multi-clip resize maintains relative proportions.

### Tempo Scaling (Stretch Content)

Hold [Ctrl] (Win) / [Option] (Mac) over a Resize handle until the cursor changes to the "scale tempo" arrow, then drag horizontally. The clip's content stretches to match the new length.

### Splitting (Razor Tool)

- Click on a single clip at the desired split point.
- Click the **Ruler** to split all tracks/lanes at that position simultaneously.
- Click-drag on the Ruler to split a range across all tracks.
- [Alt/Option]+[X] = split at song position.

### Joining

- Same lane only: [Ctrl/Cmd]+[J] or "Join Clips."
- Audio: overlapping clips auto-comp to separate Comp Rows.
- Notes: permanently overlapped events are deleted.

### Chopping

"Chop Clips/Notes to >" divides selection into equal preset lengths relative to the absolute grid.

### Copy/Paste Workflow

1. Activate Snap (set to "Bar").
2. Select clips.
3. Copy [Ctrl/Cmd]+[C]. Song position auto-advances to selection end.
4. Paste [Ctrl/Cmd]+[V] repeatedly to chain copies.

Pasting between Reason documents auto-creates tracks (and empty Combinators if needed).

### Other Clip Operations

- **Mute**: [M] toggles, or use Mute Tool. Muted clips show gray stripes.
- **Delete**: [Delete]/[Backspace].
- **Duplicate**: [Ctrl/Cmd]+[D] (duplicates after original) or [Ctrl/Option]+drag.
- **Labels**: "Add Labels to Clips," then double-click to rename. "Remove Labels" deletes them.
- **Color**: "Clip Color" overrides default track color.

### Inspector for Clips

The Edit Area Inspector (above the Arrange Area) shows context-aware properties:
- Position, Length (with subtick `*` indicator)
- Velocity, transpose, level, fade in/out (audio)
- **Match Values** function aligns selected clips' properties to the topmost selected clip.
- The Inspector **disappears** when the Pencil Tool is active.

### Bounce in Place

Converts note/audio clips to new audio tracks. Includes insert effects and channel strip settings, but **excludes Send FX and Master Section**. Sustaining audio tails extend up to 5 seconds beyond the clip. Multiple clips on one source track bounce to one destination; different sources create separate destinations.

### Timeline Functions

- **Insert Bars Between Locators**: Adds empty bars; existing clips split and shift right.
- **Remove Bars Between Locators**: Deletes content between locators. **Notes/automation are permanently deleted.** Audio is masked on Comp Rows (recoverable).

### Alien Clips

Moving a clip to an incompatible lane creates an "alien clip" (red-striped, inactive). Use "Adjust Alien Clips to Lane" to recalibrate parameter ranges automatically.

## Editing Notes

Open a note clip in the Edit Area: double-click, [Return], or [F8].

### Edit View Modes
- **Key Edit View**: Standard piano roll. Default for instrument devices.
- **Drum Edit View**: Shows Redrum drum sound names instead of keys.
- **REX Edit View**: Shows slice numbers (Dr. Octo Rex).

View mode is automatic per device and remembered per note lane.

### Selecting Notes
- Click; [Ctrl] (Win)/[Shift] (Mac) for multi-select.
- Drag selection rectangle.
- Arrow keys navigate to next/previous note.
- Double-click a piano keyboard key to select all notes of that pitch.
- [Ctrl/Cmd]+[A] selects all in clip.

### Drawing Notes
- **Pencil Tool**: Click to insert (snap-aligned, default velocity 100). Click and drag to set length.
- **Multiple Notes mode**: Click Pencil Tool **twice** to enter. Then click-drag creates sequential notes at the same pitch (length = current Snap value).
- **Selection Tool double-click** also inserts a note of current Snap length.

### Moving and Transposing
- Drag with Selection Tool. [Shift] restricts to one axis.
- **Nudge by Snap/Beat/Tick** uses the same modifiers as clip nudging.
- **Transpose semitones**: [Ctrl/Cmd]+[Up/Down Arrow]
- **Transpose octaves**: [Shift]+[Ctrl/Cmd]+[Up/Down Arrow]
- Inspector "Transpose (Semitones)," "Octave," "Alter Notes," and "Randomize Notes" buttons batch-transform selections.

### Resizing Notes
- Drag handles on the note's edges.
- Inspector Length field (`x.x.x.x` or `+/-x.x.x.x`).
- **Overlap / Make Legato**: Extends each note to reach the next selected note's start. Positive values overlap, zero abuts, negative values create gaps. Range: ±960 ticks.
- **Drum notes (Redrum)**: In Decay mode, length doesn't matter — sound plays to completion. In Gate mode, length matters (capped by Length knob).

### Velocity Editing
- **Velocity Edit Lane**: Pick "Velocity" from the Controller selector. Tall bars = high velocity.
- Drag with Pencil Tool to adjust.
- [Ctrl/Cmd]+click Pencil = Line Tool for smooth ramps.
- Hold [Shift] while editing to affect only selected notes.
- Inspector functions: **Velocity** (offset), **Scale** (% multiply), **Randomize**, **Make Ramp** (gradient between first and last selected).

### Note Operations
- **Mute**: [M] or Mute Tool. Muted notes appear blue.
- **Split**: Razor Tool — click for single, drag rectangle for multiple. Split notes inherit parent velocity.
- **Join**: [Ctrl/Cmd]+[J] (same pitch).
- **Chop**: "Chop Notes to >" with desired length (absolute grid).
- **Duplicate**: [Ctrl/Cmd]+[D] or [Ctrl/Option]+drag. "Duplicate Selected Notes to New Lane" creates a parallel copy.
- **Extract**: "Extract Notes to Lanes" splits notes by pitch criteria onto new lanes — great for splitting drum pitches into separate lanes.
- Cut/Copy moves Song Position Pointer to selection end (handy for sequential pasting).

### Quantize

1. Select notes/clips/tracks.
2. Pick Quantize Value from dropdown (1/16, 1/8, etc.). "T" suffix = triplets.
3. Pick Quantize Amount (100% = full snap, 50% = halfway).
4. Click Quantize.

- **Q Record** quantizes during recording.
- **Quantize to Shuffle** delays even-numbered 16ths for swing. Shuffle amount lives in the ReGroove Mixer's Global Shuffle.
- **Randomize**: Offsets note start positions randomly within a tick range.

### Scale Tempo

Multiplier 1–800% on selection start. Affects notes, automation, and audio clips. **Does not affect time signature automation.** Quick buttons: x2 (200%), x/2 (50%).

### Reverse

Two modes (toggle in Options menu):
- **Reverse Notes Graphically**: Considers note length. End positions become start positions.
- **Musical Reverse**: Only considers note start positions; ignores lengths.

### Multi Lanes Editing

Toggle the Multi Lanes button to overlay multiple lanes in the Edit Area:
- Active lane in red; others ghosted gray.
- Click a gray note or use the lane selector to switch active lane.
- Only notes on the active lane can be edited together.

## Editing Automation

### Two Storage Locations
- **Parameter Automation**: Separate clips on Parameter Automation Lanes.
- **Performance Controller Automation**: Inside note clips (Pitch Bend, Mod Wheel, Velocity, etc.).

### Static Value
The handle to the LEFT of the Controller Edit Lane sets the parameter's value where there are no automation clips. Drag up/down or double-click to type. Hold [Shift] for fine adjustment.

### Drawing Automation
- **Selection Tool double-click**: Insert a single point. Drag for a series.
- **Pencil Tool**: Click or drag to draw a curve.
- [Shift]+Pencil: Add a single point to the existing line.
- [Ctrl/Cmd]+Pencil: Draw a step (range) function.
- **Curves**: With Selection Tool, click and drag a line segment to bend it into a curve. Repeat to refine. [Shift]+click to straighten.

### Editing in the Arrange Area
Double-click an automation clip in the Arrange Area to expand the lane for editing. Edit the Static Value with arrows or by typing. [Esc] closes.

### Editing in the Edit Area
Open a note clip, then pick a parameter from the Controller selector. Selected event's position/value shows in the Inspector.

### Automation Cleanup
Removes superfluous events to simplify curves. Set density in Preferences > User Interface (Normal, Heavy, Maximum). Apply retroactively via "Cleanup Automation" in context menus.

### Performance Controller Lanes
1. Open a note clip in Edit Area.
2. Click Controller selector → choose controller.
3. New lane appears. Draw with Pencil Tool.
4. **Hide** option at top of Controller selector hides the lane while preserving data.
5. **Clear** button deletes the controller lane (with confirmation).

> **Note:** When multiple performance controller lanes overlap, the **topmost lane's controllers override** lower lanes.

### Pattern Automation Editing

A pattern automation clip contains exactly **one** pattern event. To set up:
1. Activate Snap (typically Bar).
2. Select Pencil Tool.
3. Pick pattern from the Pattern/Loop dropdown in Inspector.
4. Draw a clip for desired duration.
5. Repeat for each pattern change.

> **Don't do this:** Drawing pattern clips with Snap off — leads to chaotic mid-bar pattern changes.

Use "Convert Pattern Automation to Notes" to convert to editable note clips.

## Audio Editing

### Three Edit Modes
- **Slice Edit Mode**: Time-stretching, transient slicing, audio quantize.
- **Vocal Edit Mode**: Monophonic pitch correction with formant preservation.
- **Comp Edit Mode**: Take comping with cuts and crossfades.

### Slice Edit and Transients
On opening a single-take clip in Slice Edit mode, Reason auto-detects transients and marks them with vertical white **Slice Markers**.

- Move slice markers with Selection Tool to adjust timing without affecting pitch.
- Add markers manually with Pencil Tool.
- Delete unwanted markers with Eraser/Delete.
- **You cannot add markers before the first slice marker or after the end slice marker.**

### Stretching and Tempo Matching

Stretching is performed by repositioning slices. Reason runs two parallel processes:
- A real-time preview stretch (immediate playback)
- A high-quality background render (CALC progress meter)

**Stretch Types** (choose per clip):
| Type | Best For |
|------|----------|
| Allround | Polyphonic material — formants follow pitch |
| Melody | Monophonic material — preserves formant character |
| Vocal | Vocals specifically — character preserved while pitching |

### Audio Quantize

> **Important:** Audio can only be quantized **after** recording, never during.

1. Open clip in Slice Edit mode.
2. Select slice markers.
3. Apply quantize from Inspector or Transport Panel.

Unlike note quantize, **multiple slice markers cannot be quantized to the same position** — only the marker closest to a grid position moves. Others stay in place.

In **Vocal Edit mode**, quantize works on **pitch transitions** (note starts), not level transients.

### Pitch Editing (Vocal Edit Mode)

- Click "Correct Pitch" to snap selected notes to the nearest semitone.
- **Three transpose modes**:
  - **Snap**: Absolute semitone positions.
  - **Jump**: Semitone steps preserving original fine-tuning.
  - **Fine**: Free cent-level adjustment.
- **Drift handle**: Appears when notes are selected. Drag down to reduce natural pitch drift / vibrato.

### Comping Audio Takes

After a loop-mode recording, multiple takes sit on **Comp Rows** below the master clip.

**Adding cuts:**
1. Open the clip and click "Comp Edit."
2. With Razor Tool, click a Comp Row at the desired switch point.
3. Or **swipe** the Razor Tool across a range to assign that range to a take.

**Crossfades:**
- Select cut handles, drag the crossfade controls.
- Longer crossfades = flatter (smoother) curves.

**Recording offsets**: Nudge an entire take horizontally without changing playback assignment — useful for aligning takes that drifted.

**Levels per row**: Each comp row has its own fader.

> **Tip:** Run "Delete Unused Recordings" after comping to shrink the file size.

### Fades and Clip Level
- Drag the Fade handles at clip edges to set fade in/out — non-destructive, edit anytime.
- Inspector shows fade values in 1/16 + Tick precision.
- Fades persist when clip boundaries are adjusted.
- **Crossfades**: Overlap two adjacent clips, then [X] (or context menu Crossfade). Adjust shape via curve handles.
- **Clip Level**: Vertical handle, or Inspector Level (in dB).
- **Transpose**: Inspector Semitones + Cents (non-destructive).

### Bouncing Audio

| Function | Result |
|----------|--------|
| Bounce to Recording | Combines all comped segments into a single new comp row (re-enables Slice/Vocal Edit) |
| Bounce to REX | Single-take audio → REX loop loadable in Dr. Octo Rex |
| Bounce to MIDI | Audio → note clip. "Vocal" stretch type generates pitched MIDI notes |
| Bounce to Samples | Creates song samples for sampler devices |

> **Tip for REX bouncing**: Trim clip length to the closest full Beat first — ensures REX plays the same as the original.

### Other Audio Operations
- **Normalize**: Boosts overall level so the loudest peak hits 0 dB.
- **Reverse**: Available via context menu.
- **Split at slices/notes**: Razor Tool in respective modes.

## Working with Blocks

Blocks are 32 reusable pattern-like sections. Each is typically 4–8 bars and contains multi-track recordings. Blocks let you mix pattern-based and linear composition.

### Enabling Blocks
Options menu > "Enable Blocks." A new **Blocks Track** appears above the Transport Track.

### Song View vs. Block View
- **Song View**: Linear arrangement (the regular timeline).
- **Block View**: Where you record and edit the contents of a single block.
- Click the Block button to switch to Block View; Song button to return.
- **They share the Track List, but clips on lanes are unique to each view.**

### Creating and Editing Blocks
1. In Block View, pick a block (1–32) from the Blocks dropdown in the Track List.
2. Double-click the block name to rename.
3. **Set block length** by dragging the End Marker (E) in the Ruler.
4. Record/edit content as you would in Song View.
5. Assign block colors from the Block Color palette (context menu on Blocks Track).

> **Important:** Events to the right of the End Marker in Block View are **ignored** during Song View playback.

### Arranging Blocks in Song View
1. Switch to Song View.
2. Pencil Tool, pick block from Inspector's Block Selector List, draw on Blocks Track.
3. Or double-click with Selection Tool on Blocks Track for a Snap-length clip.
4. Block content appears as ghosted clips on regular tracks beneath.

### Block Behavior
- **Clip longer than block**: Block repeats; thin vertical lines mark repetitions.
- **Clip shorter than block**: Unused content is masked.
- **Resize left edge**: Creates a Block Offset, starting playback from mid-block.
- **Reassign**: Click the small triangle on a Block Automation Clip → pick a different block (1–32).
- **Mute lanes within a block**: Use Mute Tool on lanes within a Block Automation Clip — silences for that clip's duration only. Great for gradual track introductions.

### Combining Blocks with Song Clips
**Song clips have priority over block data.** A Song clip placed on the same lane as a ghosted block clip plays instead of the block — block content is masked underneath.

This enables: foundational blocks in Song View + targeted variations layered on top via short linear clips.

### Automation in Blocks
- **Performance Controller and Parameter Automation in Song View always overrides automation in Blocks.**
- Parameter automation in blocks affects corresponding lanes throughout the song.
- Song clips can interrupt performance controller automation.

### Converting Blocks to Song Clips
- **Single block**: Select the Block Automation Clip(s) → Edit menu → "Convert Block Automation to Song Clips." Unmuted clips become regular sequencer clips; the block clip remains.
- **All blocks**: Track List context menu → "Convert Block Automation to Song Clips." Blocks Track auto-mutes; references preserved.
- **Manual**: Cut/Copy clips in one view, switch view, Paste.

### Block Workflow Pattern
1. Build 4–8 bar blocks with full instrumentation (verse, chorus, breakdown, etc.).
2. Arrange blocks in Song View via Block Automation Clips.
3. Use lane muting per Block Automation Clip for variations within a block.
4. Layer short linear clips in Song View for unique sections, fills, or hits.
5. Convert to Song clips when you need to fine-tune individual events.

## Best Practices

### Recording
- **Click on, pre-count on** for any tempo-locked recording — saves comping headaches later.
- **-12 dB target** on input meters; never trust the channel strip for recording level.
- **Use Loop + Alt** for take-style recording: each loop becomes a comparable take.
- **Use Dub** for layered drum overdubs or doubled vocals.
- **Save before** large audio recording sessions.
- **Check Monitoring mode** matches your hardware setup (Automatic for built-in, External for hardware monitoring).

### Arranging
- **Set Snap to Bar** before any heavy duplication or section-paste workflow.
- **Use folded tracks** to manage screen space when arranging.
- **Bounce in Place** committed parts to free CPU and lock in mixes.
- **Use Match Values** to align fades, levels, transposes across clips.
- **Insert Bars / Remove Bars Between Locators** is faster than dragging clips manually.

### Editing Notes
- **Quantize at 50–80%** to preserve human feel rather than 100%.
- **Make Legato** for sustained instrument lines (strings, pads).
- **Multi Lanes editing** for cross-lane drum tweaks.
- **Use Extract Notes to Lanes** to break drum hits into per-pitch lanes for separate processing.
- **Velocity Make Ramp** for crescendos and fade-ins.

### Editing Audio
- **Choose stretch type per material**: Allround for polyphonic, Melody for solo lines, Vocal for vocals.
- **Quantize in Slice Edit** but expect that not every marker will move (only closest to grid).
- **Vocal Edit's Drift handle** subtly tames vibrato without removing it entirely.
- **Comp before bouncing**: keep takes available; only "Delete Unused Recordings" once you're certain.
- **Trim audio to the nearest beat** before "Bounce to REX."

### Automation
- **Set Static Value first** so the parameter's "default" between clips matches your intent.
- **Cleanup Automation** after recording detailed control-surface moves.
- **Live Mode override** for fixing one-off values without re-recording.
- **Performance controllers in note clips** for gestures tied to a part. **Track automation** for mixing/sound design that spans multiple clips.

### Blocks
- **4–8 bars per block** is the sweet spot for reusability.
- **Don't put song-wide automation in blocks** — Song View overrides anyway, and it can confuse playback.
- **Reserve 1–2 blocks for variations** (alt verse, drop, breakdown) instead of cramming everything into one.
- **Set block colors immediately** — visual scanning in Song View matters.

## Common Pitfalls

| Pitfall | What Happens | Fix |
|---------|--------------|-----|
| Forgetting to reset clipping LEDs | Old clip warning sticks around | Click Input Meter to clear |
| Adjusting input level on channel strip | Recording level unchanged | Adjust at preamp/interface only |
| Empty audio clips after stop | They DON'T auto-delete (notes do) | Manually delete leftover empty audio clips |
| Recording over masked notes | Masked events permanently deleted | Don't punch over hidden content |
| Click via mixer | Click goes through audio interface, NOT mixer | Adjust click level via Transport slider |
| Pre-count + Ableton Link | Pre-count doesn't work | Use one or the other |
| Pattern automation has no static value | Patterns ONLY play where clips exist | Draw clips spanning the desired range |
| Track + note-clip automation overlap | Track automation overrides | Pick one method per parameter |
| Block content past End Marker | Ignored in Song View | Move End Marker or trim content |
| Drawing pattern clips without Snap | Mid-bar pattern changes, chaos | Always Snap to Bar |
| Multiple performance controller lanes | Topmost overrides others | Consolidate or hide redundant lanes |
| Automation green borders not showing | Need to click Stop twice | Or click Automation Override to confirm |
| Removed Bars Between Locators | Notes/automation **permanently** deleted | Audio is masked (recoverable); double-check before |

## Quick Reference: Modifier Keys

| Modifier + Action | Effect |
|---|---|
| [Shift]+drag clip/note | Restrict to one axis |
| [Ctrl]/[Option]+drag clip | Duplicate while dragging |
| [Ctrl]/[Option] over Resize handle | Tempo scale (stretch content) |
| [Alt]/[Cmd] hold (any tool) | Toggle to alternate tool |
| [Alt]/[Cmd]+click | Speaker (audition) |
| [Ctrl/Cmd]+drag with Razor | Duplicate cut sections |
| Pencil Tool clicked twice | "Draw multiple notes" mode |
| [Shift]+drag Static Value | Fine adjustment |
| [Shift]+click curve | Straighten automation line |
| [Shift]+Pencil on automation | Add single point |
| [Ctrl/Cmd]+Pencil on automation | Step (range) function |
| [Shift] while editing velocity bars | Affects only selected notes |
| [Ctrl/Cmd]+click Pencil (velocity) | Line Tool for ramps |

## Quick Reference: Essential Shortcuts

| Action | Shortcut |
|--------|----------|
| Toggle Edit Area | [F8] |
| Open clip in Edit Area | Double-click or [Return] |
| Close Edit Area | [Esc] |
| Play / Stop | [Spacebar] |
| Record | [*] (numeric) or [Ctrl/Cmd]+[Return] |
| Loop on/off | [L] |
| Click on/off | [C] |
| Pre-count on/off | [Ctrl/Cmd]+[P] |
| Set locators to selection | [Ctrl/Cmd]+[L] |
| Locators + Loop Play | [P] |
| Snap on/off | [S] |
| Select all | [Ctrl/Cmd]+[A] |
| Cut / Copy / Paste | [Ctrl/Cmd]+[X / C / V] |
| Duplicate | [Ctrl/Cmd]+[D] |
| Join | [Ctrl/Cmd]+[J] |
| Mute | [M] |
| Crossfade adjacent audio | [X] |
| Split at song position | [Alt/Option]+[X] |
| Delete | [Delete] / [Backspace] |
| Nudge by Snap | [Ctrl/Cmd]+[Left/Right] |
| Nudge by Beat | [Ctrl/Cmd]+[Shift]+[Left/Right] |
| Nudge by Tick | [Ctrl/Cmd]+[Alt/Option]+[Left/Right] |
| Transpose semitones | [Ctrl/Cmd]+[Up/Down] |
| Transpose octaves | [Ctrl/Cmd]+[Shift]+[Up/Down] |
| Tools: Selection / Pencil / Eraser | [Q] / [W] / [E] |
| Tools: Razor / Mute / Zoom / Hand | [R] / [T] / [Y] / [U] |
