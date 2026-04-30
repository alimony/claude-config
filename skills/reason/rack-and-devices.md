# Reason 13: The Rack & Devices
Based on Reason 13.4 documentation.

The rack is the central workspace in Reason where every sound-making, sound-shaping, and routing element lives. Master the rack and you master Reason. This skill covers building the rack, the four device categories (Instruments, Effects, Utilities, Players), Rack Extensions, and VST plugins.

## Core Concepts

### The Rack Model

Reason's rack is a vertical stack of modular devices, each occupying a slot. Signal flows top-to-bottom by default, just like physical hardware racks. Every device has a front panel (controls) and a rear panel (cables and connectors). Press **Tab** to flip between them.

The rack is one of three main areas in Reason:
- **Sequencer** — note clips, automation, arrangement (timeline view)
- **Mixer** — channel strips, sends, master bus (mixing console view)
- **Rack** — devices and their connections (modular view)

Each instrument device typically has a corresponding sequencer track *and* a mixer channel strip. Reason keeps these three views synchronized: rename a device and the track and mixer channel update too.

### Device Categories

Reason groups devices into four categories in the Device Palette:

1. **Instruments** — Sound generators (samplers, synths, drum machines). Always the source of audio in a Device Group.
2. **Effects** — Audio processors (reverb, EQ, compression, distortion). Can be inserts or sends.
3. **Utilities** — Routing and CV tools (Mixer 14:2, Spider audio splitter, Combinator, Matrix sequencer).
4. **Players** — MIDI/note effects that sit *between* your keyboard and an instrument (Scales & Chords, Note Echo, Dual Arpeggio, etc.).

Within each category, devices are sorted: Reason native first, then Rack Extensions and VST plugins alphabetically by manufacturer.

### Device Source Types

Three different technologies provide devices:
- **Native devices** — Built into Reason, fully integrated and stable.
- **Rack Extensions (RE)** — Add-on devices from Reason's web shop, designed to behave identically to native devices.
- **VST2/VST3 plugins** — Third-party plugins hosted via the Plugin Rack Device wrapper.

VST3 plugins show a **golden VST3 label**; VST2 plugins show a **blue VST2 label** in the Device Palette.

### Signal Flow (Top-to-Bottom)

Audio flows from the top of a device chain downward. A typical instrument Device Group looks like:

```
[Player(s)]            <- MIDI/note processing (top)
    |
[Instrument]           <- audio source
    |
[Insert Effect 1]      <- effect chain
    |
[Insert Effect 2]
    |
[Mix Channel]          <- routes audio to the mixer
```

**Players** are special: they process MIDI before it hits the instrument. **Effects** process audio after the instrument generates it. **Mix Channels** are the bridge to the mixer.

### Device Groups

A Device Group is a collection of interconnected devices that function as a unit: a source instrument, its effects, its players, and its associated sequencer track and mixer channel strip. Groups are defined by *connections*, not by location in the rack.

When **Auto-group Devices and Tracks** (Options menu, or **Cmd/Ctrl+Cmd+G** / **Cmd+Shift+G** on Mac) is enabled, selecting any device in a group selects the whole group for moving, copying, or deleting.

## Building the Rack

### Creating Devices

There are five ways to create a device:

1. **Drag and drop** from the Device Palette into the rack or sequencer track list.
2. **Double-click** a device in the Device Palette.
3. **Click the + button** at the top or bottom of a selected device — this filters compatible devices contextually.
4. **Use the Create menu** to access Instruments, Effects, Utilities, and Players categories.
5. **Browse patches** in the Browser — Reason auto-creates the matching device.

The **+ button approach** is the most context-aware: it knows what type of device you can sensibly insert at that position and filters the Palette accordingly.

### Creation Side Effects (Read This)

Creating a device often does more than just add it to the rack:

| Device Type | Default Side Effects |
|---|---|
| Instrument | Creates instrument + sequencer track + Mix Channel device |
| Audio Track | Creates audio device + sequencer track + channel strip |
| Effect (with instrument selected) | Inserts between instrument and Mix Channel |
| Effect (with mixer selected) | Connects as a send effect |
| Utility / Mixer | Connection rules vary by device |
| Player | Auto-attaches to selected instrument; if none selected, creates an ID8 |

**Modifier keys to suppress side effects:**
- **Shift** — prevents automatic cable routing (creates the device unconnected)
- **Alt/Option** — prevents sequencer track creation (or, for Utilities/Mixers, *forces* track creation)

Use these when you want full manual control over routing.

### Browsing & Loading Patches

Patches are saved settings for a device.

- Click the **Browse Patch** button on a device to open the Browser.
- Keyboard shortcut: **Ctrl+F** (Windows) / **Cmd+F** (Mac).
- Use **Previous Program / Next Program** buttons on a device to step through patches.
- Browsing a patch from the Browser without a target device will *create* the matching device.

For Rack Extensions, patches live under **Reason Library > Rack Extensions** in the Browser. For VSTs:
- **VST3** — load `.vstpreset` files via the Browse Patch button.
- **VST2** — use the patch name display or Previous/Next Program buttons.

VST preset data is embedded in the saved Reason song, so you don't need to ship preset files separately when sharing songs.

### Reordering Devices

To move a device, click the front panel and drag. An **orange line** indicates the destination.

- With **Auto-group Devices and Tracks** on: the entire Device Group moves together.
- Without it: only the clicked device moves.
- Hold **Shift** while dragging to *re-route* — Reason treats it like a delete-and-recreate, applying automatic routing rules to the new location.

### Duplicating Devices

- **Ctrl/Cmd+drag** a device to copy it.
- **Edit > Duplicate Devices and Tracks** copies the device and its sequencer track.
- Connections between devices in a copied selection are preserved.
- **Shift+drag** while duplicating attempts auto-routing.

### Cut, Copy, Paste

Standard clipboard operations work. Pasted devices insert *below* the current selection. With Auto-group on, operating on any device in a group affects the whole group.

### Replacing Devices

Drag a device from the Device Palette directly onto an existing device. The target dims and shows a "replace" symbol. Release to swap, with automatic routing preserved.

### Deleting Devices

- **Backspace** or **Delete** — prompts for confirmation.
- **Ctrl/Cmd+Backspace** — deletes without confirmation.
- **Edit > Delete Devices and Tracks** — also removes the sequencer track.
- Deleting a device positioned between two others **automatically reconnects** the surrounding devices.

### Renaming Devices

Each device has a "tape strip" showing its name. Click it to rename (max 16 characters). For instruments connected to Mix Channels, the name syncs across the device, channel strip, and sequencer track. To restore the default, delete the custom name.

## Flipping the Rack & Cabling

### Front vs. Rear

- Press **Tab**, click the **Flip Rack button** at the top of the rack, or use **Options > Toggle Rack Front/Rear**.
- The rear panel exposes audio inputs, outputs, and CV connectors.
- Cables follow physical layouts (you can see them snaking between devices).

### Manual Cabling

In rear view, drag from an output connector to an input connector. Right-click any connector for a context menu of compatible destinations.

**Auto-routing** kicks in automatically when devices are created or moved. For precise control, route manually after using Shift to suppress auto-routing on creation.

### Inspecting Cables

- Cables are color-coded by type (red = audio, yellow = CV, etc.).
- Click and drag a cable end to re-route it.
- Right-click a connector to see "Disconnect from..." and "Connect to..." options.
- Press **Tab** again to flip back to the front panel.

## Rack Layout & Organization

### Multiple Rack Columns

Reason supports multiple side-by-side rack columns. Drag a device to the left or right edge of the current rack to create a new column. Use this to:
- Separate drum tracks from synths visually.
- Keep utility/CV processing rigs in their own column.
- Reduce vertical scrolling on large projects.

A column persists as long as a neighboring column has at least one device.

### Folding Devices

Click the **Fold/Unfold button** to collapse a device. Folded devices:
- Retain all connections and play normally.
- Show no parameters and no rear-panel cables.
- Still allow patch selection, renaming, and moving.

**Alt/Option+click** the fold button to fold/unfold *all* devices in a column at once. Fold aggressively — the rack gets unwieldy fast.

### Combinator (When to Use It)

The Combinator wraps a group of devices into a single, navigable unit with:
- A unified front panel with up to 4 rotary knobs and 4 buttons mapped to internal device parameters.
- A single saved patch covering all internal devices.
- Its own sequencer track, mixer channel, and routing.

**Use a Combinator when:**
- You want to create a custom instrument from layered devices (e.g., synth + sampler + effects).
- You want to save and recall complex device chains as a single patch.
- You want simplified macro control over many parameters.

**Don't use a Combinator when:**
- You only need a chain of 1–2 effects on a single instrument.
- You need to access the underlying devices' sequencer tracks independently.

### Sort Selected Device Groups

**Edit > Sort Selected Device Groups** reorders Device Groups, mixer channel strips, and sequencer tracks to match each other. Select sequencer tracks and run this to make the rack mirror the track order. Or select Device Groups in the rack to make the tracks mirror the rack.

### Tags, Favorites, and Hidden Devices

- Hover over a device in the Palette and click the **heart icon** to favorite it.
- Click **Show Favorites Only** to filter the Palette.
- Add custom **Tags** to organize devices into your own groupings.
- Hidden devices are still accessible via the Create menu but suppressed from the Palette unless filtered with the "Hidden" tag.

## Players (Note Effects)

### What Players Are

Players are **MIDI/note processors** that sit between your keyboard input and an instrument. They process, filter, and generate MIDI notes. They can also generate notes independently (as pattern sequencers) without any input.

### Where Players Live

Players are narrower than standard devices and **always sit directly above their associated instrument**, between the instrument and its mix channel.

A Player **cannot exist without an instrument**. Creating one with no instrument selected automatically generates an **ID8** instrument (a basic sound module) to host it.

Multiple Players can chain on a single instrument. **MIDI flows top-to-bottom** through the chain before reaching the instrument.

### Available Players

| Player | Purpose |
|---|---|
| **Beat Map** | Generates drum patterns via crosshair positioning, density controls, pattern locking, mirror notes, and CV modulation |
| **Dual Arpeggio** | Turns single notes or chords into rhythmic patterns; mono arpeggiator or polyphonic 4-note pattern mode; Up/Down/Up+Down/Random directions |
| **Note Echo** | MIDI delay — repeats notes with adjustable spacing, velocity curves, and pitch transposition |
| **Note Tool** | Filters and adjusts MIDI: pitch range, velocity, note length, polyphony limits |
| **Random Tool** | Randomizes pitch, velocity, length; supports conditional sequencing and probability gating |
| **Scales & Chords** | Transposes input to fit a scale or generates chords from single notes; 13 presets plus custom scales |

### Creating Players

- Drag a Player from the Players palette onto an instrument.
- Select an instrument, then double-click a Player in the Palette.
- Right-click an instrument and choose **Player devices >** in the context menu.
- Use **Add Player...** to load a Player patch via the Browser.

### Common Player Controls

- **Fold Button** — collapses/expands all Players attached to an instrument.
- **Bypass All** — sends keyboard input straight through, ignoring Players.
- **On Button** — enables/disables an individual Player.
- **Direct Record** — captures Player-generated MIDI into note clips (rendered output, not input).
- **Send to Track** — renders Player output of *existing* sequencer notes as a new clip; auto-mutes the original and enables Bypass All.

### Recording Modes

| Mode | What's Recorded |
|---|---|
| **Standard (default)** | Your raw keyboard input — Players process during playback |
| **Direct Record** | The notes Players *generate* — Players are bypassed during playback |

**Use Standard mode** when you want to keep Player processing live (e.g., sweeping the arpeggiator parameters during playback).

**Use Direct Record** when you want to commit a specific generated phrase and free up the Player for other duties — or to delete it later for CPU savings.

### Signal Flow Caveat

When Players are active, **only live MIDI input** flows through them. Pre-recorded sequencer notes go *directly* to the instrument and bypass Players. Use **Send to Track** to render existing clips through the Players.

### Player Best Practices

**Do:**
- Chain **Scales & Chords → Dual Arpeggio** to create scale-correct arpeggios from single notes.
- Reverse the order (**Dual Arpeggio → Scales & Chords**) to arpeggiate chords with scale snapping.
- Place a **Scales & Chords** in Chromatic mode with Chords off at the bottom of the chain to *visualize* what notes are actually being generated.
- Use **Note Echo** with Step Length 0, max repeats, and selective muting to build chord voicings programmatically.
- After **Send to Track** or **Direct Record**, **delete the Player** if no longer needed to reduce DSP load.

**Don't:**
- Don't expect Players to process recorded MIDI clips by default — they only process live input until you Send to Track.
- Don't pile Players on every instrument indiscriminately — they cost CPU.
- Don't forget that re-ordering Players changes the result, since MIDI flows top-down.

### Player CV & Automation

Players have CV connections on the rear panel for modulating density, mirror velocity, pitch, etc. Gate outputs can trigger external devices. Key, scale selection, and locked positions support automation.

## Rack Extensions (RE)

### What They Are

Rack Extensions are first-party and third-party add-on devices sold through the **Reason Studios web shop**. They behave identically to native devices: full rear-panel cabling, CV routing, Combinator compatibility, automation, and remote control.

### Licensing

- Purchases write a license to your **Reason Studios user account** automatically.
- You can install on multiple computers; playback requires either an authorized machine or internet verification.
- **30-day free trial** per device — full functionality, but you can only trial each device **once**.
- After trial expires, the device disappears from menus but remains installed unless removed.
- A **rent-to-own** option exists in the web shop.

### Installing & Managing

Since Reason 12.7, **Reason Companion** handles installation (replacing the older Authorizer):

- Launch via Reason's Window menu or as a standalone app.
- **Update all** / **Install all** for batch operations.
- Per-device Update / Install / Uninstall.
- Search/filter by device name.
- Detects missing files and selectively re-downloads.

### Using REs in a Project

REs appear in the Create menu and Device Palette under their category, sorted alphabetically by manufacturer (Reason Studios first, then third-party). Standard auto-routing applies.

Patch browsing: **Reason Library > Rack Extensions** in the Browser, or **Cmd/Ctrl+F**.

### Missing REs in a Song

If a song references an RE you don't have:
1. Reason shows an alert.
2. You can proceed without the RE or open the web shop to buy/trial.
3. Missing REs become **generic placeholder devices** — silent for instruments, bypassed for effects.
4. Project structure is preserved, so collaboration works.
5. Install the missing RE through Reason Companion and restart Reason to restore.

### Demo Mode

REs are **not available** in Reason Demo Mode.

### RE Best Practices

- Trial REs before buying — you only get one trial per device, so don't waste it on casual exploration.
- Authorize at least one machine before going offline.
- Keep Reason Companion installed and run **Update all** periodically.
- For collaborative songs, document which REs are required.

## VST Plugins

### Format Support

- **VST3 (64-bit)** — gold label in the Palette.
- **VST2 (2.4)** — blue label in the Palette.
- Both are supported on Windows and Mac.

### Scan Locations

**Windows:**
```
C:\Program Files\VSTplugins\
C:\Program Files\Steinberg\VSTplugins\
C:\Program Files\Common Files\Steinberg\VST2\
C:\Program Files\Common Files\VST3\
```

**Mac:**
```
/Library/Audio/Plug-ins/VST
~/Library/Audio/Plug-ins/VST
/Library/Audio/Plug-Ins/VST3
```

Reason scans these on launch. Add custom paths via **Preferences > Folders**.

### Manage Plugins Window

**Window > Manage Plugins** lists every plugin Reason knows about with columns: Manufacturer, Plugin Name, Plugin Type, Device Type, Status.

Statuses:
- **Enabled** — loads normally.
- **Disabled** — won't load on restart.
- **Could not load** — failed to scan.
- **Crashed** — caused a crash, sandboxed out.

Disable misbehaving plugins from this window. They'll stay disabled across restarts.

### The Plugin Rack Device

When you load a VST, Reason wraps it in a **Plugin Rack Device**. Click **Open** to show the VST's GUI in a floating Plugin Window. Toggle **Keep open** to persist the window across device selections. Multiple Plugin Windows can be open at once.

### Automation & Remote Control

Three ways to automate VST parameters:
1. Record edits during sequencer playback.
2. Click **Automate** and select parameters.
3. Use the **Track Parameter Automation** popup.

Use the **Remote** button in the Plugin Window to map MIDI controllers to VST parameters.

### CV Modulation

The Plugin Rack Device's rear panel has **8 CV inputs**, mappable to VST parameters via Learn or dropdown selection. Bipolar amounts from -100 to +100. Useful with the CV Programmer or LFO sources.

### Audio Routing & Sidechain

- VST instruments auto-route to Mix Channels (stereo L/R or mono).
- Mono-in VSTs in stereo paths route to the **left channel only**.
- Stereo VSTs in mono paths run as mono-in/stereo-out.
- **Audio 3-4 inputs** are sidechain inputs for VST effects that support them.

### Limitations (Important)

VSTs in Reason **do not support**:
- **Multitimbrality** — only MIDI Channel 1 receives data.
- **VSTs that output MIDI** (no MIDI-out plugins like arpeggiators).
- **Reason Rack Plugin format VSTs** (chicken-and-egg loop).

**Critical performance note:** Setting a VST effect to **Off** or **Bypass** does **not** reduce CPU load. The plugin keeps processing. To save CPU, use the **On/Off button on the Plugin Rack Device** itself, or remove the plugin.

### Saving Songs with VSTs

- VST preset data is embedded in the saved song.
- No separate preset files needed.
- Missing VSTs become empty Plugin Rack Devices on load — silent or bypassed, but the slot is preserved so the song can be restored when the VST returns.

### VST Troubleshooting

- **Tiny GUI on hi-res Windows displays:** Enable **Auto-scale (follow Windows display scaling)** in Manage Plugins, then reload the VST instance.
- **Standard Reason shortcuts don't work:** Holding Shift for precision, Cmd/Ctrl-click to reset, and Undo/Redo may not work — VST manufacturers define their own control behavior.
- **Built-in VST keyboards** preview sound but **don't record** into Reason's sequencer.
- A **crashed VST** drops to "Crashed" status. Disable it in Manage Plugins to prevent future crashes.

## Native vs. RE vs. VST: Reference Table

| Aspect | Native | Rack Extension | VST2/VST3 |
|---|---|---|---|
| **Source** | Built into Reason | Reason web shop | Third-party developers |
| **Stability** | Highest | High (designed for Reason) | Variable; can crash Reason |
| **Sandboxing** | N/A | Integrated | Wrapped in Plugin Rack Device; can be disabled if unstable |
| **Authorization** | Comes with Reason | License tied to Reason account; trial once per RE | Per-vendor licensing (varies) |
| **Internet required** | No | One-time auth, then optional | Depends on vendor |
| **CPU usage** | Optimized | Comparable to native | Variable; **Bypass does NOT reduce CPU** |
| **Disable to save CPU** | Toggle On/Off | Toggle On/Off | Use Plugin Rack Device On/Off (NOT Bypass) |
| **Automation** | Full | Full | Full (record, Automate button, popup) |
| **CV in/out** | Full rear-panel CV | Full | 8 CV inputs only |
| **MIDI in** | Yes | Yes | MIDI Channel 1 only |
| **MIDI out** | Yes (Players) | Yes | **Not supported** |
| **Multitimbral** | Per device | Per device | **Not supported** |
| **Combinator-compatible** | Yes | Yes | Yes |
| **Sidechain** | Native CV/audio inputs | Native CV/audio inputs | Audio 3-4 (if VST supports it) |
| **Preset format** | Reason patches | Reason patches | VST3: `.vstpreset`; VST2: programs |
| **Demo Mode** | Available | **Not available** | Available |
| **Missing-on-load** | N/A | Generic placeholder device | Empty Plugin Rack Device |
| **Latency** | Reported, compensated | Reported, compensated | Reported, compensated (vendor-dependent) |
| **GUI scaling** | Native | Native | VST3 supports DPI; VST2 may need Auto-scale (Windows) |

## Key Keyboard Shortcuts

| Shortcut | Action |
|---|---|
| **F3** | Show/Hide Device Palette |
| **F6** | Toggle rack visibility |
| **Ctrl/Cmd+F6** | Detach rack to separate window |
| **Tab** | Flip rack front/rear |
| **Page Up/Down** | Scroll one screen vertically |
| **Home/End** | Jump to top/bottom of column |
| **Backspace/Delete** | Delete selected device(s) (with confirm) |
| **Ctrl/Cmd+Backspace** | Delete without confirmation |
| **Ctrl/Cmd+F** | Browse Patch on selected device |
| **Cmd+Shift+G** (Mac) / **Ctrl+Cmd+G** | Toggle Auto-group Devices and Tracks |
| **Shift+drag** (creating) | Suppress auto-routing |
| **Alt/Option+drag** (creating) | Suppress sequencer track creation |
| **Shift+drag** (moving) | Re-route as if delete-and-recreate |
| **Ctrl/Cmd+drag** | Duplicate device |
| **Alt/Option+click fold button** | Fold/unfold all devices in column |

## Best Practices

### Organizing the Rack

- **Enable Auto-group Devices and Tracks** by default — keeps related devices, tracks, and channel strips locked together.
- **Use multiple columns** for complex projects: drums in one, synths in another, FX/utilities in a third.
- **Fold devices** you're not actively editing. Use Alt/Option+click on a fold button to collapse a whole column at once.
- **Name devices meaningfully** — instrument names sync to the mixer and sequencer, so good names everywhere.
- **Sort Selected Device Groups** periodically to keep rack and track order matching.

### Effect Chain Order Matters

Audio flows top-to-bottom. Order changes the sound:

- **EQ before compression** = compress the EQ'd signal (color the dynamics).
- **Compression before EQ** = EQ the compressed signal (clean the tone).
- **Distortion before delay** = clean repeats of distorted notes.
- **Delay before distortion** = distorted repeats blur into noise.

Always think about which signal gets processed by which effect.

### When to Use a Combinator

- Wrap layered instruments (synth + pad + sampler) into one playable unit.
- Save complex effect chains as a single recallable patch.
- Expose macro controls (4 knobs, 4 buttons) for live performance.
- *Don't* Combinator a single device or a 1-effect chain — overkill.

### CPU Management

1. **Native devices are cheapest.** Prefer them when functionality overlaps with REs/VSTs.
2. **Disable unused VSTs at the Plugin Rack Device's On/Off button** — Bypass on the plugin itself does NOT reduce CPU.
3. **Render Player output and delete the Player** when you've committed the phrase (Send to Track or Direct Record).
4. **Fold devices** to reduce GUI overhead (minor, but real for many devices).
5. **Disable misbehaving VSTs** in Manage Plugins to prevent CPU spikes from problem plugins.
6. **Bounce CPU-heavy effect chains** to audio if they're committed.

### Players: Generation vs. Recording

- During tracking, leave Players in **Standard mode** so the recorded MIDI is your raw input — you can tweak the Player later.
- Once happy with the result, use **Direct Record** or **Send to Track** to commit the generated phrase, then delete the Player.

### Cabling Hygiene

- Use **Shift+drag** when creating a device if you want to manually route everything.
- Check the rear panel (**Tab**) periodically — auto-routing can produce unexpected paths.
- Color-coded cables make CV vs. audio mistakes easy to spot.
- A device deleted between two others auto-reconnects the survivors — useful, but check the result.

## Common Pitfalls

### Auto-routing surprises
Creating a device while another is selected can produce unexpected cables. If you want manual control, hold **Shift** when creating.

### Effect order
The same effects in a different order produce a different sound. Always confirm the chain reads top-to-bottom in the order you intend.

### Players don't process recorded clips
Pre-recorded notes bypass Players. Use **Send to Track** to render existing clips through the Player chain.

### Trialing Rack Extensions
You only get **one 30-day trial per RE, ever**. Don't burn trials casually — only trial REs you're seriously considering.

### VST Bypass doesn't save CPU
Bypassing a VST keeps it processing. Use the Plugin Rack Device On/Off button or remove the plugin to actually save CPU.

### VST multitimbrality
VSTs only see MIDI Channel 1. Multitimbral plugins won't work as multitimbral hosts in Reason — use one instance per part.

### VST MIDI out
VSTs that *output* MIDI (arpeggiators, chord generators with MIDI out) are not supported. Use Reason's native Players for MIDI generation instead.

### Missing devices on load
Songs with missing REs or VSTs load with placeholder devices. The slots are preserved but silent. Install the missing devices and reopen.

### Sandboxed VST crashes
A crashing VST is marked **Crashed** in Manage Plugins. Disable it there before reloading the song or it may crash again.

### Combinator overuse
Combinators add a layer of indirection. Don't wrap single devices or trivial chains — it just hides the rack from yourself.

### Folding hides rear-panel cables
You can't see or edit cables on a folded device. Unfold to inspect routing.

## Quick Workflows

### "Build a synth lead with arpeggiator and reverb"
1. Create an instrument (e.g., Europa). Auto-creates sequencer track and Mix Channel.
2. With instrument selected, create a **Dual Arpeggio** Player. Sits above the instrument.
3. With instrument selected, click **+** below it and add an **RV-7000 reverb**. Inserts between instrument and Mix Channel.
4. Press **Tab**, verify cables. Press **Tab** again.
5. Play notes — arpeggiated lead with reverb.

### "Replace an instrument while keeping its effect chain"
1. Drag the new instrument from the Device Palette onto the existing instrument.
2. Release when the "replace" symbol appears.
3. Connections are preserved.

### "Render a Player phrase and free up CPU"
1. Set the Player's instrument's track to **Direct Record** (or use **Send to Track** on existing clips).
2. Record/render the phrase.
3. Delete the Player device.
4. The rendered clip plays back the same notes via the instrument directly.

### "Diagnose a missing-device alert"
1. Open Reason Companion.
2. Filter by missing device name.
3. Click **Install**.
4. Restart Reason.
5. Reopen the song — placeholder is replaced by the real device.

### "Suppress all auto-routing on creation"
Hold **Shift** while dragging from the Device Palette or pressing the **+** button. Device appears with no cables. Press **Tab** and route manually.

### "Visualize what notes a Player chain is generating"
Add a **Scales & Chords** at the bottom of the Player chain. Set scale to Chromatic and turn Chords off. The keyboard display shows the actual MIDI being delivered to the instrument.

## Relationships Between Areas

| Area | Role | Sync |
|---|---|---|
| **Rack** | Devices and cables | Source of truth for routing |
| **Sequencer** | Note clips, automation, arrangement | One track per Device Group; renames sync |
| **Mixer** | Channel strips, sends, master | One channel per Mix Channel device; names sync |

A change in one place propagates: rename in the rack, see it in the mixer and sequencer. Reorder Device Groups, optionally re-sort tracks via **Sort Selected Device Groups**. Delete a device with **Delete Devices and Tracks** to clean all three views together.

The rack is the truth — the mixer and sequencer are views into it.
