# Reason 13: Sounds, Browser & File Handling
Based on Reason 13.4 documentation.

This skill covers everything about managing sounds, patches, samples, and files in Reason 13: the Browser, patch loading/saving, song file handling (`.reason`), audio import/export, and direct sampling into devices. Use this when you need to organize content, share songs reliably, or set up a sampling workflow.

## Core Concepts at a Glance

- **Patch** = saved settings for a single device (e.g., Subtractor, Thor, NN-XT, Kong). Stored as small files on disk or inside ReFills. Samplers/loop players store *references* to samples, not the samples themselves.
- **ReFill** (`.rfl`) = packaged sound bank containing patches, samples, REX files, SoundFonts, MIDI. Treat them as read-only — you cannot save into a ReFill.
- **Browser** = the unified file finder for patches, samples, REX loops, ReFills, and Sound Packs. Continuously indexes content with filtering, tagging, and favorites.
- **Song file** (`.reason`) = stores all device parameters automatically. Samples are referenced by default; "self-contain" embeds them inside the song.
- **Sampling** = direct recording into NN-XT, NN19, Redrum, Kong, Grain, or RV7000 MkII via dedicated Sample buttons. 30-second buffer, fixed 16-bit, user-set sample rate.
- **Scratch Disk** = where unsaved audio recordings go until you save the song.

---

## The Browser

### Open / Close

- `F9` toggles Browser
- `Ctrl+F` (Win) / `Cmd+F` (Mac) also opens it
- Click the Browser button at top of song window, or `Windows menu > Show/Hide Browser`
- Browser can float as a separate window or dock as a side panel — toggle via the "Show Browser in Side Panel" symbol; resize side panel horizontally
- Set side-panel-by-default in `Preferences > Browser`

### The Six Main Locations

| Location | What's there |
|---|---|
| **All Locations** | Flat list of every indexed patch/sample/loop |
| **User Library** | Default save folder (`Music/Reason Studios`) — your custom patches |
| **Reason Library** | Built-in factory sound banks, Rack Extensions, ReFills subfolder |
| **Sound Packs** | Reason+ subscription content |
| **Song Samples** | Samples used in the current song (not in Rack Plugin) |
| **Computer** | Links to User and Desktop folders (NOT in All Locations) |

### Indexing & Blacklisted Folders

The Browser auto-indexes content. First-run indexing takes a while; a progress symbol shows status. **Don't store Reason content in blacklisted folders** — they will not be scanned:

- **macOS:** `/System`, `/Applications`, `/Library` (except `/Library/Audio` which IS scanned), `~/Music/Propellerhead Content`
- **Windows:** `C:\Windows`, `C:\Users\<you>\Music\Propellerhead Content`

> Do this: keep custom content in `Music/Reason Studios` (User Library).
> Don't do this: drop ReFills into the legacy `Propellerhead Content` folder — they won't index.

### Browse Focus

When you click a "Browse Patch" button on a specific device, that device gets **Browse Focus** (orange side bars in rack and sequencer). The Browser shows only patches valid for that device. Opening the Browser via `F9` opens it without focus — you see everything.

### Filtering and Search

Type in the Filter text field. As you type, suggestions appear for: Name, Category, Tag, Author, Sound Pack, Rack Extension, ReFill, Folder, Kind. Press `Return` to apply, or arrow-key through suggestions.

**Filter logic — memorize this:**
- Multiple **Names / Categories / Kinds** → results **widen** (OR)
- Multiple **Tags** → results **narrow** (AND)

Active filters show as chips with `X` to remove individually.

**Category buttons:** click to filter; multiple categories can be active. Subcategories appear depending on file type. "Uncategorized" shows untagged items.

**Staff Pick** tag = curated highlights. **Untagged** = items without any tags.

### Sorting & View

- Toggle **Flat list** vs **Tree** (folder structure) in view mode selector
- Click column headers to sort; drag edges to resize
- Right-click an item > **Show in Folder** to open its OS folder

### Auditioning

Audition controls sit below the Item List:

- **Auto** toggle: selecting a sample/loop plays it automatically
- **Volume slider**: preview level (does not affect sample data)
- For samplers: arrow keys cycle through items with auto-preview

### Multi-select

`Shift+click` (range) or `Ctrl/Cmd+click` (additive) lets you:

- Load multiple drum patches into Kong
- Load multiple samples into NN-XT, NN19, Kong NN-Nano
- Load multiple REX files into Dr. Octo Rex
- Import multiple audio files to sequencer tracks
- Add multiple files to a Favorite List at once

If a multi-selection contains incompatible files, the Create/Load button grays out.

---

## Patches

### File Extensions Cheat Sheet

| Device | Extension |
|---|---|
| Combinator | `.cmb` |
| Subtractor | `.zyp` |
| Thor | `.thor` |
| Malstrom | `.xwv` |
| NN19 | `.smp` |
| NN-XT | `.sxt` |
| Redrum | `.drp` |
| Dr. Octo Rex | `.drex` |
| Kong Kit | `.kong` |
| Kong Drum (single pad) | `.drum` |
| RV7000 | `.rv7` |
| Scream 4 | `.sm4` |
| The Echo | `.echo` |
| Pulveriser | `.pulver` |
| Alligator | `.gator` |
| Rack Extension | `.repatch` |
| VST2 | `.fxp`, `.fxb` |
| VST3 | `.vstpreset` |
| REX loops | `.rx2`, `.rcy`, `.rex` |
| Audio | `.wav`, `.aif`, `.mp3`, `.aac`, `.m4a`, `.wma` |
| SoundFont | `.sf2` |

### Loading a Patch

Five ways:

1. Click the **Browse Patch** button on the device
2. `Edit menu > Browse Patches...` (or device context menu)
3. `Ctrl+B` (Win) / `Cmd+B` (Mac) with device selected
4. Click the **Patch Name display** for a quick pop-up list (browse list)
5. Use the up/down **Select Patch** buttons to step sequentially

While auditioning, click any patch in the Browser to load it temporarily; press `Return` or click `OK` to confirm, or `Cancel` to revert.

### Cross-Browsing Between Device Types

When the Browser opens with focus on a specific device, **Patch Type buttons** at the top let you switch between:
- "This device only"
- "All Instrument Patches" (cross-browsing)

> If you select a patch belonging to a different device while cross-browsing, **the original device is replaced by the new device.** Be aware of this when experimenting.

**Sampler edge case:** NN19 (`.smp`) and REX patches load into their original device when possible; otherwise they load into NN-XT. The "Create Instrument" function picks NN19 for `.smp` and Dr. Octo Rex for REX files.

### Saving a Patch

1. Click **Save Patch** on the device panel
2. Pick name + location (defaults to User Library)
3. Extension is added automatically

**Quick overwrite:** hold `Alt` (Win) / `Option` (Mac) while clicking Save Patch — skips the dialog and overwrites the current patch silently. Use with care.

> Don't do this: try to save into a ReFill — it's read-only. Always save modified ReFill patches outside the ReFill with a new name.
> Do this: keep your saves under User Library so they're easy to find later.

**Modifying a patch in the rack does NOT modify the file on disk** until you save. Cancelling a Browser session reverts unsaved changes.

### Copy / Paste / Reset

- **Copy Patch** + **Paste Patch** between same-type devices via Edit menu or context menu — transfers parameter settings only (no cable routing for non-Combi patches).
- **Reset Device** initializes parameters to defaults. For samplers/drum machines, this also clears all sample/REX references.

### Tags, Categories, Author Info

Right-click a file in Item List:
- `Categories >` and `Tags >` submenus toggle assignments
- Multi-select then change to batch-edit; a dash (`-`) means conflicting values across selection
- `Edit Info...` opens a panel where you set Categories, Tags, and Author; can move between selected items, click `Save` when done

### User Tags (your own taxonomy)

1. Unfold the Filter text field; expand User Tags
2. Click `+ Add...`, type a name, press Enter
3. Right-click any sound > `User Tags >` to assign
4. Or `User Tags > + Assign New Tag...` creates and assigns in one step
5. Right-click the User Tag itself to rename or delete

### Shortcuts vs Favorite Lists

**Shortcuts** = pinned folders (drag a folder from Item List under "Shortcuts" heading). Right-click > Delete Location to remove.

**Favorite Lists** = curated lists of individual files (patches/samples/loops):
- Drag files in, or right-click > pick a Favorite List
- Check mark ⇒ already in list; click again removes
- Right-click list icon to Rename / Delete

> Don't do this: put entire ReFills in Favorite Lists (the docs explicitly recommend against this). Use Shortcuts or User Library instead.

### Browser Preferences That Matter

- **Load Default Sound in New Devices** (default ON): new instruments come up with a default patch. Off → bare "init sound" (same as Reset Device).
- **Browsing starts in default sound folder (for new devices)**: ON shows the device's home folder; OFF shows All Locations (good if you have lots of custom patches).
- **Show Browser in Side Panel**: dock by default for new songs.

---

## Song Files

### Supported Song Extensions

`.reason` (current), `.rsndemo`, `.rns` (legacy), `.rps` (Published), `.rsb` (Adapted), `.record` / `.recdemo`, plus the various edition variants (`.ree`, `.rei`, `.rltd`, `.relt`, etc. and their demo counterparts).

### New Song

- `Ctrl+N` / `Cmd+N` or `File > New` — creates a blank song with Hardware Interface, Main Mixer Master Section (connected to Master Out L/R), and Transport Track.
- `File > New from Template` — choose from templates in `Music > Reason Studios > Template Songs > Reason 13`.
- To add your own template: drop a `.reason` file in that folder. Quick way: `File > New from Template > Show Template Folder` opens it in Finder/Explorer.
- Set a **default template** in `Preferences > Browsing` so every new song starts from your preferred state.

### Open

- `Ctrl+O` / `Cmd+O` or `File > Open`, or double-click a song file in Finder/Explorer
- Multiple songs can be open simultaneously — supports drag/drop and copy/paste between them, but uses more RAM/CPU
- **Demo Mode** (unauthorized) replaces "Open" with "Open Demo Song" (factory demos only)
- **Open last song on startup** option in `Preferences > Browsing`
- **Legacy songs (Reason 5 or earlier)** open with reorganized routing: Main Mixer Master goes to Hardware Interface Outputs 1+2; legacy device connections reroute through Mix Channel devices

### Save

- `Ctrl+S` / `Cmd+S` — first save prompts for name+location; subsequent saves overwrite silently
- `Ctrl+Shift+S` / `Cmd+Shift+S` — **Save As** (also auto-optimizes during save)
- `File > Save and Optimize` — defragments the song file, removing empty regions left by deleted audio recordings (only works on already-saved songs). Run periodically on long-edited songs to shrink file size.

### Self-Contained Songs (CRITICAL for sharing)

By default Reason **does not** embed external sample/REX files in songs — only references them. If you move or share the song without the samples, they go missing.

**To embed everything:**
1. `File > Song Self-Contain Settings...`
2. Tick the boxes next to files you want embedded (or click `Check All`)
3. Save the song

Embedded samples are losslessly compressed to ~50% of original size. Sound quality is preserved.

**To extract embedded samples (un-self-contain):**
1. Open `Song Self-Contain Settings...`
2. Untick the box
3. If the original file is found at its original path, the embedded copy is dropped and the reference restored
4. If the original is missing, you're prompted to save the extracted file somewhere

> **Hard limitation: samples that originate from ReFills cannot be un-self-contained.** Once embedded from a ReFill, they stay embedded.

> Do this: self-contain before sending a song to a collaborator or moving it to a different machine.
> Do this: also self-contain before archiving a finished project.
> Don't do this: rely on referenced samples for production work — moving the User Library or renaming a folder will silently break songs.

### Missing Sounds Window

When opening a song with broken references, the **Missing Sounds** window lists each missing item by Device, Sound name, and ReFill/RE source. Options:

- **Search All Locations** — auto-searches all indexed Browser locations
- **Browse to Folder** — manually navigate to the file
- **Replace** — pick a different sound via Browser
- **Download ReFill / RE** — opens Reason Companion to fetch the missing pack
- **Proceed Without** — load anyway; missing items show asterisks `*` on device panels and produce silence

Missing **Rack Extensions** appear as generic "Missing Device" placeholders that preserve all configuration so the song re-links cleanly once the RE is installed.

### Song Information & Metadata

`File > Song Information` lets you set:

- Custom title bar text
- Notes / comments
- **Splash screen image**: JPEG, max 256x256 px
- "Show splash on open" checkbox
- Author website + email URL

### Scratch Disk & Orphan Audio

- Audio you record before saving the song lives in the **Scratch Disk folder**
- On save, audio migrates from Scratch Disk into the song file; further recordings go straight into the song file
- Change location: `Preferences > Folders > Scratch Disk Folder > Change`. **Restart required** for it to take effect
- If Reason crashes mid-recording into a saved song, reopening triggers an "orphan audio streams" alert. You can delete them or have them placed onto a fresh audio track for recovery

### MIDI Import / Export

**Import:** `File > Import MIDI File`, pick a `.mid`. Reason creates sequencer tracks, assigns ID8 devices with approximated sounds, preserves tempo/time-signature automation, and imports controller data.

**Export:** Set the End Marker to your stop point, then `File > Export MIDI File`. Produces a Type 1 MIDI file with all instrument tracks + automation. All tracks export to MIDI channel 1. Tempo and automation preserved; sound info is not.

---

## Audio Import & Export

### Import

**Supported import formats:** mono and stereo audio in WAV/AIFF/MP3/AAC/M4A/WMA (OS-dependent), plus REX files (`.rcy`, `.rex`, `.rx2`).

> When you import a REX file, it's **rendered to audio** — slice positions and per-slice info are lost. To keep slicing, load the REX into Dr. Octo Rex instead of importing it as audio.

**Import targets:**
- Separate audio tracks in the sequencer (one per file when multi-importing)
- A single existing audio track (when one has focus)
- Separate Comp Rows within an open Audio Clip

**Sample rate handling:** if the imported file's rate differs from the hardware setting, Reason auto-converts. Real-time conversion plays first; high-quality background conversion follows. The transport's **CALC** indicator shows when background conversion is running.

**Tempo matching:** if the imported file embeds tempo data Reason supports, the file is automatically time-stretched (not pitch-shifted) to match the song tempo.

### Export Formats Quick-Reference

| Format | Extension | Best For | Bit Depth | Notes |
|---|---|---|---|---|
| **WAV** | `.wav` | Mastering, stems, archive, delivery to other DAWs | 16/24/32-bit | Lossless, widest compatibility, includes tempo metadata |
| **AIFF** | `.aif` | Mac-native delivery, sample export | 16/24/32-bit | Lossless, Apple ecosystem |
| **MP3** | `.mp3` | Demo / streaming previews | N/A (lossy bitrate) | Lossy — never use for further production work |
| **FLAC** | — | Not natively supported as an export format in Reason 13 | — | If you need FLAC, export WAV and convert externally |

> Reason 13's documented export formats are **AIFF, WAV, and MP3**. FLAC is not a native export option. Don't promise FLAC delivery without an external conversion step.

**Sample rates and bit depths:** selectable on export. 16-bit and higher supported. **Dithering** with noise shaping is optional at 16-bit — turn it on when reducing from higher resolutions to improve low-level sound quality.

### Exporting Mixed Audio

Two main commands (both in `File menu`):

- **Export Song as Audio File** — renders from song start to the **End Position Marker**
- **Export Loop as Audio File** — renders between the **Left and Right Locators**

Both use signals from **Outputs 1 and 2 of the Hardware Interface** (i.e., your master bus).

### Bouncing Mixer Channels (Stems)

`Bounce Mixer Channels` gives you per-channel renders. Three settings options:

1. **All settings** (Insert FX, Level, Pan applied)
2. **All except fader section** (insert FX yes, fader/pan no)
3. **None** — pre-fader, pre-FX

**Destinations:**
- New tracks within the song (printing stems back into the song)
- Separate disk files (delivering stems to another DAW or mastering engineer)

**Normalize** checkbox adjusts each bounced file so its peak hits 0 dB. Useful for stem delivery; turn it OFF if you want all stems to retain relative levels for direct sum-back.

> Do this for stems-to-DAW: bounce with "All except fader section" off (use "None" to deliver dry pre-FX stems) so the receiving engineer has full control. Or use "All settings" to deliver finished bus prints.
> Don't do this: normalize stems if the receiver will sum them — relative balance breaks.

### Bouncing Audio Clips

Right-click a clip > **Bounce Clip to Disk**. The clip renders **after** Clip Level and Fades but **before** the Mixer Channel settings. Useful for committing comping/fade decisions without baking in mixer FX.

### Bounce vs Export — the difference

- **Export Song / Loop** = the master bus output, your final mix
- **Bounce Mixer Channels** = per-channel stems (with chosen settings depth)
- **Bounce Clip to Disk** = a single audio clip rendered with its clip-level edits

### Tempo Track Export

When exporting/bouncing, optionally tick **Export Tempo Track (.MID)** — produces a side-car MIDI file with tempo and time-signature automation. Useful for delivering audio to a DAW that needs to follow tempo changes.

### Real-Time vs Offline Render

Audio export is offline (faster than real-time) by default. Some scenarios (Rack Extensions or external sources that misbehave offline) may require real-time rendering — check the export dialog options for this toggle.

### Sample Rate / Bit Depth Pitfalls

> Don't do this: export 16-bit without dither when the project ran at 24-bit or higher — you'll get audible quantization noise on quiet tails.
> Don't do this: deliver 48 kHz files when the target needs 44.1 kHz (or vice versa) — match the destination's spec at export time, don't convert later.
> Do this: for music release, 24-bit / 44.1 or 48 kHz WAV. For video post, match video team's spec (often 48 kHz).
> Do this: keep an internal archive at 24-bit, song's session sample rate, no dither.

---

## Sampling

### Devices With a Sample Button

- **NN-XT**
- **NN19**
- **Redrum** (per drum channel)
- **Kong** (per drum pad)
- **Grain**
- **RV7000 MkII** (sample your own impulse responses for the convolution reverb)

### Quick Recording Procedure

1. **Setup audio inputs:** `Preferences > Audio` and connect your hardware inputs to **Sampling Input** connectors on the Hardware Interface rear panel (`Tab` flips the rack)
2. **Click the Sample button** on the target device — or click-and-hold to sample continuously
3. **Play, sing, or route** internal device audio into the Sampling Inputs
4. **Click Stop Sampling** to finish

### Sample Format

- **Bit depth: 16-bit, fixed** (cannot be changed)
- **Sample rate:** set in Preferences; can be changed any time without affecting pitch or speed of existing samples
- **Auto-trim:** silence preceding the first audio is automatically removed
- **Buffer: 30 seconds.** After 30 seconds the play head wraps and overwrites from the start. Plan recording length accordingly.

### Mono vs Stereo

- Connect both L and R Sampling Inputs → stereo sample
- Connect only L or only R → mono sample
- Internal source: route a device's audio output directly to the Sampling Inputs in the Hardware Interface

### Monitoring

Hardware Interface controls:

- **Monitor button** — continuous monitoring
- **Auto button** — monitoring only while sampling
- **Monitor Level knob** — affects monitor signal only, not what gets recorded

### Edit Sample Window

Open it: right-click a sample > **Edit Sample**, or hold `Alt` (Win) / `Option` (Mac) while clicking the **Start Sampling** button.

**Locators:**
- `S` — Sample Start
- `E` — Sample End
- `L` — Left Loop
- `R` — Right Loop

**Operations:**

| Operation | What it does |
|---|---|
| **Crop** | Discards everything outside `S`/`E` locators |
| **Normalize** | Scales whole sample so loudest peak = 0 dB. Amplifies any noise too — use after careful recording, not as a fix |
| **Reverse** | Reverses the entire sample (ignores locators) |
| **Fade In** | Volume ramps from silence to current level (clean intros, click removal) |
| **Fade Out** | Volume ramps from current level to silence (clean tails) |
| **Loop modes** | None / Forward / Forward+Backward |
| **Crossfade Loop** | Smooths loop boundaries to remove clicks at loop points |

**Set Sample Start/End:** click-drag in the waveform to highlight, then click `Set Sample Start/End` — locators snap to the highlight.

**Set Loop:** same gesture for `L`/`R` loop locators.

**Snap Sample Start/End To Transients:** auto-aligns locators to the nearest transient — invaluable for drum/percussion samples.

**Other controls:**
- **Root Key** — set the sample's original pitch so the sampler transposes correctly across the keyboard
- **Name field** — rename; the new name replaces the original on save
- **Volume slider** — preview level only
- **Play / Spacebar** — audition; toggles to Stop while playing
- **Solo** — isolate sample playback against the rest of the song

**Undo:** Edit Sample window has its own undo stack of **10 steps**, separate from the main app. After clicking Save, the only way to revert that whole editing session is the main window's Undo.

### Slicing

Reason's slicing path is via **Dr. Octo Rex** for REX files: load a `.rx2`/`.rcy`/`.rex` and Dr. Octo Rex preserves the slices. **Do not import REX as audio** — slicing is destroyed in that path. For making your own slices, use ReCycle (external) to author REX files, then load them in Dr. Octo Rex.

### Where Recorded Samples Go

In the Browser under **Song Samples**:

- **Assigned Samples** — currently in use by a device
- **Unassigned Samples** — recorded but no longer attached to a device (reuse them later)
- **All Self-contained Samples** — every sample stored inside the song, including duplicates of Factory/ReFill samples you've duplicated for editing

### Self-Contained by Default

> "All samples you record in a song automatically become self-contained." — they're saved inside the song, no external file dependency.

Use `File > Song Self-Contain Settings...` to un-self-contain (extract them) — except for samples originating from ReFills, which cannot be un-self-contained.

### Sample Management Operations

**Load:** `Browse Sample` button > navigate > double-click.

**Duplicate (so you can edit a Factory/ReFill sample without touching the original):** right-click sample > **Duplicate Sample(s)**. Copy lands in **All Self-contained Samples** with " Copy" appended to the name.

**Export to disk:** right-click > **Export Sample(s)** — saves WAV or AIFF. **Cannot export Factory Soundbank or ReFill samples.** Export options:

- Crop at Start/End markers and render loop crossfades (committed file)
- Crop only at markers
- Save raw sample data without marker positions (preserves locators as metadata if format supports)

**Delete:** only custom-recorded samples can be deleted. Right-click in **All Self-contained Samples** > **Delete Sample(s)** — removes from every folder simultaneously.

### Browsing Samples Specifically

- Click **Browse Sample** on the device (NN-XT, NN19, Kong NN-Nano, Redrum, etc.) — Browser filters to audio + REX
- Use up/down arrow keys with **Auto** preview to compare candidates quickly
- For Kong drum patches: use `Browse Drum Patch` — shows `.drum` + supported audio formats
- For REX in Dr. Octo Rex: `Edit > Browse ReCycle/REX Files` — shows `.rx2`, `.rcy`, `.rex`

### Sampling Best Practices

> Do this: monitor input levels at the source (preamp/mic) to record around -12 to -6 dBFS peaks. You can normalize later, but you can't undo clipping.
> Do this: name samples meaningfully right after recording — Edit Sample window's Name field saves with the sample.
> Do this: set the **Root Key** for any pitched sample before saving the patch — otherwise transposition is wrong across the keyboard.
> Do this: use **Snap to Transients** for percussion to get tight starts.
> Do this: use **Crossfade Loop** when looping sustained material to hide the seam.
> Don't do this: hit **Normalize** as a "make it louder" button before checking for noise — normalize amplifies the noise floor too.
> Don't do this: rely on the 30-second buffer for long takes — record into an audio track and slice/load from there for anything longer.
> Don't do this: edit Factory/ReFill samples in place — Duplicate first, then edit the copy.

---

## Common Workflows

### Sharing a Song With a Collaborator

1. Save the song
2. `File > Song Self-Contain Settings...` > **Check All** > OK
3. Save again — file size will grow but the song is now portable
4. (Optional) `File > Save and Optimize` to defragment
5. Send the `.reason` file. The recipient also needs any Rack Extensions and matching Reason version/edition

### Archiving a Finished Project

1. Self-contain everything
2. Save and Optimize
3. Bounce stems (`Bounce Mixer Channels` > separate disk files, "None" settings option) for portability into other DAWs
4. Export Song as Audio File at 24-bit WAV at the project's sample rate
5. (Optional) Export Tempo Track `.MID` alongside stems
6. Store the `.reason`, stems, master, and tempo track together

### Building a Reusable Patch Library

1. Save patches into User Library with descriptive names
2. Use `Edit Info...` to set Categories, Tags, Author
3. Add User Tags for personal taxonomy (genre, project, mood)
4. Pin frequently-used folders as **Shortcuts**
5. Curate a **Favorite List** per project or per genre — but don't add ReFills

### Sampling a Live Vocal into NN-XT

1. Connect mic to audio interface input; route to Hardware Interface Sampling Input L (mono) in Preferences > Audio
2. Add NN-XT
3. Click **Sample** button on NN-XT — speak/sing — click **Stop Sampling**
4. `Alt`/`Option` + **Start Sampling**, or right-click sample > **Edit Sample**
5. Trim with `S`/`E` locators > **Crop**; apply **Fade In/Out**
6. Set **Root Key** to the pitch you sang
7. Save the sample (it's auto self-contained); save patch with **Save Patch** if you want it reusable

### Recovering Missing Samples After Moving a Folder

1. Open the song — Missing Sounds window appears
2. Click **Search All Locations** — Reason scans every indexed location
3. For anything still missing, **Browse to Folder** manually
4. Or **Replace** with a substitute
5. Once all resolved, **Save** the song to lock in the new paths
6. Then **Self-Contain** to prevent future breakage

---

## Pitfalls Quick List

- Songs default to **referenced** samples — moving folders silently breaks them. Self-contain before archiving or sharing.
- **ReFill samples can't be un-self-contained.** Plan accordingly.
- **You cannot save into a ReFill.** Save modified ReFill patches to User Library with a new name.
- **REX imported as audio loses slices.** Use Dr. Octo Rex for slicing.
- **Sample buffer is 30 seconds** and wraps. Use audio recording for long takes.
- **Sample bit depth is fixed at 16-bit** — record clean to maximize headroom.
- **Cross-browsing replaces a device** if you load a different device's patch.
- **Quick-overwrite (Alt/Option + Save Patch)** has no confirmation — easy to clobber.
- **Normalize amplifies noise.** Record clean, then normalize.
- **Edit Sample undo is only 10 steps and is local** — past Save, only main-app undo works.
- **MP3 export is lossy** — don't use for stems or master delivery.
- **Dithering only matters at 16-bit export** — turn it on when reducing from higher bit depths.
- **Reason 13 doesn't export FLAC natively** — convert externally if you need it.
- **Blacklisted folders aren't indexed** — keep content under User Library / Reason Library.
- **Scratch Disk change requires restart.**
