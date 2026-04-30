# Reason 13: Performance, MIDI Control & Sync
Based on Reason 13.4 documentation.

This skill covers four interlocking systems that determine how Reason performs in real time:
**ReGroove** (timing/feel), **Remote** (controller mapping), **Synchronization** (MIDI Clock /
Ableton Link), and **Performance Optimization** (CPU/RAM/buffer). These systems share concerns:
controllers feed notes that ReGroove reshapes; sync determines tempo for everything; performance
ceilings limit how much you can do live. Use this file when wiring up a hardware setup, taming
CPU, or trying to make a stiff sequence feel human.

---

## ReGroove Mixer

The ReGroove Mixer is Reason's groove quantization engine. It is opened from the **Groove**
button on the Transport Panel. Unlike destructive quantize, ReGroove shapes how notes *play
back* — original positions and velocities are preserved on disk until you Commit to Groove.

### Architecture

- **32 channels** organized into **4 banks** (A1-A8, B1-B8, C1-C8, D1-D8).
- Each channel is independent and holds one groove patch (`.grov`).
- Note lanes in the sequencer are routed to a ReGroove channel via the lane's **Groove Select**
  pop-up.
- Groove channels affect timing, velocity, and (sometimes) note length of routed lanes.

### Global Parameters

| Parameter | Function |
|-----------|----------|
| **Anchor Point** | Where groove patterns begin repeating. Default Bar 1; offset for songs with pickup measures. Time signature changes always force restart, so duplicate a time-sig event to force restart mid-song. |
| **Global Shuffle** | Master swing for all *pattern-based* devices (Redrum, Matrix, Dual Arpeggiator, RPG-8). 50% = straight; 66% = perfect 1/16 triplet shuffle. Quantize-to-Shuffle uses this value. |

### Per-Channel Parameters (Front Panel)

| Parameter | Range / Meaning |
|-----------|-----------------|
| **On** | Toggles the channel. When off, routed lanes play straight. Useful for A/B comparison. |
| **Edit** | Selects the channel for the Groove Settings panel on the right. |
| **Groove Patch Name** | Shows loaded `.grov`. Click to browse; right-click for Initialize / Copy / Paste Channel. |
| **Slide** | +/- 120 ticks (up to a 1/32 note). Positive = laid back; negative = rushed. Affects every note equally — needs an unaffected reference to be audible. |
| **Shuffle** | 50% straight to 66% triplet swing. Below 50% removes inherent swing. |
| **Groove Amount** | Master 0-100% scale on Timing/Velocity/Length/Random impacts. |
| **Pre-Align** | Quantizes incoming notes to a rigid 1/16 grid *before* applying the groove, so the groove template lands on consistent input. |
| **Global Shuffle Toggle** | When lit, channel uses Global Shuffle instead of its own Shuffle knob — keeps the channel locked to pattern devices. |

### Groove Settings Panel (Edit-button view)

| Parameter | Effect |
|-----------|--------|
| **Timing Impact** | 0% no movement, 50% halfway, 100% exact template, 200% overshoot. Scaled by Groove Amount. |
| **Velocity Impact** | Scales velocity reshaping. ReGroove modifies relative differences only — soft/loud passages keep their character. Scaled by Groove Amount. |
| **Note Length Impact** | Affects duration. Most factory patches have no length data — exception: Bass-Comp category. Scaled by Groove Amount. |
| **Random Timing** | 0-120 ticks of jitter. Polyphonic (notes at the same time shift differently) and semi-deterministic (recalculated when the clip is edited). Scaled by Groove Amount. |
| **Groove Patch Length** | Bars in the patch. Mismatched lengths between lanes interact via LCM (a 3-bar + 4-bar groove cycles every 12 bars). |
| **Groove Patch Time Signature** | Should match the song unless a polyrhythm is the goal. |
| **Get Groove from Clip** | Converts the selected clip into a `.grov`. |

### How To: Apply a Groove to a Lane

1. Open the ReGroove Mixer from the Transport's **Groove** button.
2. In the sequencer, select the lane to be grooved (hi-hats and drum lanes work best).
3. From the lane's **Groove Select** pop-up, assign it to a channel (A1, B3, etc.).
4. Verify the channel's **On** button is lit.
5. Press play. Start with the **Shuffle** knob to confirm the routing works audibly.
6. Browse to **Factory Sounds > ReGroove Patches** and load a patch.
7. Set **Groove Amount** to ~80% as a starting point.
8. Click **Edit** and adjust Timing/Velocity/Length/Random impacts.
9. Use the **Next Patch** button to audition variants while playback runs.

### How To: Build a Custom Groove from a Clip

1. Make or import a clip whose timing and velocity feel right (REX or imported MIDI work too).
2. Select the clip.
3. Pick an unused ReGroove channel from the lane's groove selector (so the channel becomes the
   destination).
4. From the clip's context menu, choose **Get from Clip**.
5. In Groove Settings, fine-tune impact parameters (defaults are usually fine).
6. Click **Save Patch** in the Groove Patch browser, name it, save.

**Source-clip rules of thumb:**
- Keep 1/16 density high — gaps in the source create gaps in the resulting groove template.
- Avoid wild velocity ranges unless that dramatic dynamic is the point.
- Use even bar lengths (1, 2, 4 bars). Odd lengths get extended to the next bar.

### How To: Make the Groove Permanent (Commit to Groove)

**Whole track:**
1. Select the track.
2. Choose **Commit to Groove** from the Edit menu or the track's context menu.
3. All notes shift to grooved positions; Groove Select resets to "No Channel."

**One lane only (workaround — Reason commits at the track level):**
1. On every lane that should *stay* grooved, open Groove Select and uncheck **Enabled**
   (this bypasses the channel without losing the assignment).
2. Run **Commit to Groove** — only the still-routed lane is committed.
3. Re-enable Groove on the bypassed lanes.

### How To: Copy / Paste / Initialize Channels

- **Copy:** right-click source channel's name > **Copy Channel**, right-click target >
  **Paste Channel**.
- **Initialize:** right-click any channel's name > **Initialize Channel**.

### Best Practices (ReGroove)

**Do this:**
- Route kick / snare / hat to *separate* ReGroove channels so each can be shaped independently.
- Apply the same patch to multiple lanes with *different* Groove Amount values for layered humanization.
- Use a tiny Random Timing on doubled instruments (clap on snare) to make doubles feel less rigid.
- Set Timing Impact = 0 to apply only the *velocity* feel of a groove to already-grooved material.
- Audition with subtle Slide adjustments before reaching for complex patches.

**Don't do this:**
- Don't expect Slide to be audible by itself — it shifts everything equally; you need a straight reference track.
- Don't chain grooves with mismatched bar lengths unless you've calculated the LCM and want that polymetric result.
- Don't trust Length Impact except on Bass-Comp factory patches — most have no length data.

### Quantize Interaction

When the sequencer's Quantize panel is set to "Shuffle," it uses the **Global Shuffle** value
from the ReGroove Mixer. The two systems share state.

### Pitfalls (ReGroove)

- A clip that wants notes *rushed* (negative Slide) needs an empty bar at the song start;
  otherwise the rushed first note has nowhere to go. Compensate by setting Anchor Point to
  Bar 2 and starting the song one bar in.
- Different time signatures across groove patches create polyrhythmic side effects — usually
  not what you wanted unless explicitly designed.
- Override Edit / Keyboard Control mappings do *not* operate on ReGroove Mixer parameters.

---

## Remote (Control Surfaces & MIDI Controllers)

Remote is Reason's controller-mapping protocol. It binds physical knobs, faders, pads, and keys
to device parameters automatically (Standard mappings) or manually (Override mappings). Remote
affects every device that has parameters — synths, mixers, effects, ReGroove (limited).

### Supported Surface Types

- **MIDI Control Keyboard** — keys + knobs/faders.
- **MIDI Control Surface** — knobs/faders only, no keys.
- **MIDI Keyboard** — keys only, no programmable controls.
- **MIDI Multichannel Control Keyboard / Surface** — multiple MIDI channels.

### Master Keyboard

Exactly one keyboard is the **master keyboard**:
- It must have keys.
- It cannot be locked to a specific device.
- It always follows the sequencer's MIDI input routing (i.e. plays whatever track is selected
  / MIDI-armed).
- The first keyboard added becomes master automatically; you can reassign.

### Standard Mapping vs Override

**Standard mappings** — automatic, consistent across songs that share the same hardware,
require zero setup. Many devices expose multiple **mapping variations** reachable with
**Ctrl+Alt+1-10** (Win) / **Cmd+Option+1-10** (Mac).

**Override mappings** — manual, per-device, saved with the song. Use for any control
the standard mapping does not cover.

### How To: Add a Control Surface

1. Open **Preferences > MIDI** tab.
2. Click **Auto-detect Surfaces** (works for USB and two-way MIDI).
3. If your unit is not detected, click **Add manually**.
4. Pick **Manufacturer**, then **Model**. (If unsupported, choose **Other** and a generic class.)
5. Read the on-screen info — some surfaces require specific factory presets.
6. Use the **Find** button: tweak any control on the surface, Reason identifies the port.
7. Assign **MIDI Input** (and MIDI Output if the surface needs feedback for motor faders / displays).
8. Optionally rename the surface.
9. OK out.

### How To: Lock a Surface to a Device

Locking dedicates a surface to one device, ignoring master-keyboard track selection.

**Method A — Surface Locking dialog:**
1. **Options > Surface Locking**.
2. Pick the surface.
3. Choose target device under **Lock to device**.
4. Optionally pick a specific mapping variation.

**Method B — Context menu:**
1. Right-click / Ctrl-click the device.
2. Pick the surface from the list (ticked = locked).

**Unlock:** untick in context menu, or set **Follow Master Keyboard** in the Surface Locking dialog.

**Locking constraints:**
- Master keyboards cannot be locked.
- Each surface locks to one device (multiple surfaces *can* lock to the same device).
- Lock state saves with the song.
- Surfaces created via **Easy MIDI Inputs** cannot be locked.

### How To: Use Remote Override Edit Mode

This is how you manually map a control to a parameter.

1. **Options > Remote Override Edit Mode**.
2. Mappable parameters show a **blue arrow**. Standard-mapped ones show **yellow knob**
   symbols.
3. Click a parameter — the arrow turns **orange**.
4. Right-click and choose **Edit Remote Override Mapping** (or use the Edit menu).
5. Either pick the surface and control manually, or tick **Learn From Control Surface Input**
   and tweak the physical control — the assignment captures.
6. OK. The parameter now shows a **lightning bolt** icon.

**Faster: direct Learn**
1. In Edit Mode, double-click the parameter — a rotating lightning bolt appears.
2. Move the desired control. Mapping captured.

**Without Edit Mode (one-off):** right-click any parameter > **Edit Remote Override Mapping**.

### How To: Clear, Copy, Paste Override Mappings

- **Clear single:** select parameter in Edit Mode > Edit menu > **Clear Remote Override Mapping**.
- **Clear device:** right-click device panel > **Clear All Remote Override Mappings for Device**.
- **Copy/paste between devices** (must be same device type):
  1. Edit Mode on.
  2. Source device > **Copy Remote Override Mappings**.
  3. Target device > **Paste Remote Override Mappings**.
  4. Confirm whether to replace existing mappings if pasting in the same song.

### Additional Remote Overrides (Non-device Functions)

**Options > Additional Remote Overrides** maps surface controls to:
- Target Previous/Next Track, Target Track Delta (jump tracks from your surface).
- Select Previous/Next Patch, Select Patch for Target Device.
- Select Previous/Next Keyboard Shortcut Variation (cycle the Ctrl+Alt+1-10 variations).
- Undo / Redo.
- Document Name (display the song name on the surface).

### Keyboard Control (computer keys, not MIDI)

Maps QWERTY keys to parameters.

- Enable: **Options > Enable Keyboard Control**.
- Edit Mode: **Options > Keyboard Control Edit Mode**. Yellow arrows appear on mappable parameters.
- **Edit Keyboard Control Mapping** from a parameter, then press a key (Spacebar, Tab, Enter,
  numeric keypad, and most function keys are excluded). Shift modifier is allowed.
- Or double-click the parameter for learn mode (rotating yellow rectangle).

**Limitations:**
- Keys *toggle* on/off or jump between min/max. Multi-selectors cycle options.
- ReGroove Mixer parameters cannot be assigned.
- With Edit Mode on you see all mappings but cannot operate Reason normally — use right-click
  while Edit Mode is *off* for normal workflow.

### MIDI Input / Output Setup

- Each surface gets its own MIDI input port — separate ports for separate devices.
- Output ports needed for motor-fader / display feedback (sometimes labeled "Optional",
  sometimes required).
- **Reason only grabs MIDI inputs assigned to Remote or Sync.** Other apps may grab everything,
  so launch order matters.
- **Easy MIDI Inputs** auto-detects available ports but its surfaces cannot be locked.

### Best Practices (Remote)

**Do this:**
- Give every controller its own MIDI port. No shared cabling.
- Lock one surface to **Main Mixer** for ever-present level/pan control.
- Save a **Remote Template song** containing devices with their Override mappings, then open it
  as a starting point for new projects.
- Toggle Override Edit Mode briefly to *preview* what is and isn't mapped on a device.
- Use Ctrl+Alt+1-10 / Cmd+Option+1-10 to flip between mapping variations live.

**Don't do this:**
- Don't put control keyboards / surfaces on the External Control Bus tab — that's for incoming
  MIDI from external sequencers, not from your hardware controllers.
- Don't expect Override mappings to follow you across new documents — they save *with* the song.
- Don't auto-detect surfaces and then expect them in Easy MIDI Inputs — auto-detect removes
  them from Easy MIDI's pool.

### Pitfalls (Remote)

- Switching away from a device resets its variation to default — non-sticky.
- Multiple surfaces all following the master keyboard end up assigning the same parameters
  redundantly. Lock surfaces to distinct devices instead.
- "Target Track" (master keyboard input routing) is not the same as a locked surface — they're
  independent layers; an unlocked surface follows Target Track.

---

## Synchronization & Advanced MIDI

Reason supports two sync schemes:

1. **MIDI Clock** — classic master/slave sync over MIDI.
2. **Ableton Link** — wireless network sync.

(MTC and ReWire sync are not part of Reason 13.4.)

### Sync Mode Quick Reference

| Mode | What it sends/receives | When to use it |
|------|------------------------|----------------|
| **Internal** (no sync) | Reason runs on its own clock | Solo work; full audio stretching available |
| **MIDI Clock — Reason as master** | Reason sends Start/Stop/Continue/SPP + clock ticks out a chosen MIDI port | You're driving external drum machine, groovebox, hardware sequencer |
| **MIDI Clock — Reason as slave** | Reason listens to clock on a MIDI input port; auto-disables HQ stretching, hides Tempo readout | You're slaving to a DAW or hardware host |
| **Ableton Link** | All Link-aware apps on the LAN share tempo and bar phase | Multi-app, multi-device live setups; networked sessions |

### MIDI Clock — Reason as Master

1. **Preferences > Sync** tab.
2. In the **MIDI clock sync** section, pick the output MIDI port.
3. Either tick **Options > Sync > Send MIDI Clock**, or click **Send Clock** on the Transport.
4. Adjust **Output Offset** if external gear is drifting (negative if it's late, positive if it's
   early).

**Optional outgoing settings:**
- Send MIDI clock while sequencer is stopped.
- Send Song Position Pointer (SPP).
- Send Stop / Continue when repositioning.

### MIDI Clock — Reason as Slave

1. Connect external host via USB or MIDI.
2. Configure host to transmit MIDI Clock.
3. **Preferences > Sync** > pick the MIDI input port.
4. **Options > Sync** > activate MIDI Clock Sync.
5. Press play on the *host*.

**Latency-tuning procedure** (essential for tight slave timing):
1. Set up both apps to play synchronized click tracks.
2. Start both.
3. **Preferences > Sync** > adjust **Input Offset** until clicks line up.
4. Setting persists across sessions.

**Critical slave-mode caveats:**
- Reason needs ramp-up time when first receiving Start. Insert **2-4 empty bars** at the start
  of the song.
- Sudden tempo changes need up to a full bar to settle — automate gradually.
- High-quality audio stretching is auto-disabled while externally clocked.
- The Tempo readout disappears (the host owns it).

### Song Position Pointer (SPP)

SPP lets a slave locate to arbitrary positions. Older devices that don't support SPP must
start from bar 1. If a synced device ignores SPP or plays looped patterns, **disable SPP
transmission** so its loop position isn't reset.

### Ableton Link

1. Make sure all devices/apps are on the same network.
2. **Sync Mode** selector (Transport panel or Options > Sync) > **Ableton Link**.
3. Press Play. Reason starts when the **green progress bar** reaches the current bar phase.

**Operational notes:**
- Anyone connected can change tempo; everyone follows.
- Individual users can stop/start without breaking others.
- Pre-count is auto-disabled in Link mode.
- Tempo automation lanes are *muted* while Link is active. Click **Automation Override** or
  stop playback to take manual control back.
- HQ audio stretching auto-disables.
- For audio recording in Link, use **External Monitoring** with latency comp.
- Different time signatures across Link peers are fine — phase aligns within the bar.
- To sync external hardware to Link, configure Reason's MIDI Clock output normally — Link
  feeds the Reason tempo, MIDI Clock feeds the hardware.

### Advanced MIDI: External Control Bus

The External Control Bus routes incoming MIDI **directly to specific devices**, bypassing the
master keyboard / sequencer routing. This is for *external sequencers / hosts*, **not** for
your control keyboards.

**Buses & channels:** four independent buses **A, B, C, D**, each carrying 16 MIDI channels
(64 channels total).

**Setup:**
1. **Preferences > Other Controls** (or Control Surfaces depending on layout).
2. Assign a unique MIDI port to each bus you need.
3. Make sure no port collides with a Control Surfaces assignment.

**Routing a channel to a device:**
1. Click **ADVANCED MIDI** on the Reason Hardware Interface.
2. In the Advanced MIDI panel, click **Bus Select** (A/B/C/D).
3. Click the arrow for the desired MIDI channel (1-16).
4. Pick a target device from the menu.

Incoming MIDI on that bus+channel goes straight into the device.

**External CC and pattern automation:**
- External sequencers can send CC to manipulate Reason device parameters — see the *MIDI
  Implementation Charts.pdf* for the controller numbers.
- **CC #3** switches device patterns *immediately* (not at bar end).

### Input Focus vs Play Focus (multi-song)

When several songs are open with sync on:
- **Both Play Focus + Input Focus:** MIDI, sync, audio all route here regardless of which
  window is on top.
- **Input Focus only:** MIDI and audio come here, sync goes to whatever song has Play Focus.

### Best Practices (Sync)

**Do this:**
- Insert empty bars at the song start when slaving.
- Tune Input Offset with the click-against-click method — eyeballing is unreliable.
- Verify the host's MIDI and audio playback are themselves locked before you compensate.
- Use Ableton Link for jamming with phones/tablets/other DAWs on the same network.
- Keep Control Surface ports and External Control Bus ports strictly disjoint.

**Don't do this:**
- Don't put control keyboards on the External Control Bus.
- Don't use the External Control Bus when the only sequencer involved is Reason's own — there's
  nothing to route from.
- Don't ramp tempo aggressively while slaved; give Reason a bar to follow.
- Don't expect HQ stretching while clocked externally — it auto-disables.
- Don't try to fix a misaligned external app *inside* Reason; fix it at the source.

### Pitfalls (Sync)

- Latency drift in MIDI Clock is normal; that's why Input Offset exists.
- Older devices without SPP must always start from bar 1.
- Tempo automation silently stops working under Link mode — symptom: "my tempo curve isn't
  doing anything."

---

## Optimizing Performance

Performance tuning is about three resources: **CPU time** (DSP), **RAM** (samples), and
**audio buffer** (latency vs stability). All three are visible from Preferences and the
Transport.

### Monitoring CPU Load

- **DSP Meter** on the Transport — real-time DSP usage. Slow graphics + audio clicks =
  approaching ceiling.
- **Options > Show CPU Load for Devices** — adds per-device CPU readouts on every device.
  Each Mix Channel shows the cumulative load of its instrument plus inserts.

Use these together: the DSP meter tells you *how close* you are; the per-device readouts tell
you *where* the load is.

### Audio Buffer & Latency

**Where:** Preferences > Audio > Buffer Size slider.

**Trade-off:** smaller buffer = less latency = more CPU work / higher dropout risk. Larger
buffer = more latency = fewer dropouts.

**Tuning procedure:**
1. Open a CPU-heavy song and start playback.
2. With playback running, open Preferences.
3. Lower the buffer until clicks/pops appear.
4. Bump it back up one notch.
5. The 64-256 sample range is where buffer changes have the most audible effect.

> Raising buffer size to clear audio artifacts is mostly effective when you started small.
> If you're already at 1024+, raising further yields diminishing returns — find the load
> elsewhere.

### Multi-core Processing

**Preferences > Audio > Max audio threads.** Defaults to physical core count.

- Lower this to reserve cores for VSTs, other apps, or to dodge a flaky core.
- **Hyper-threading** is experimental — try it on, try it off, keep whichever performs better
  on your hardware.

### Audio Rendering Mode

**Preferences > Audio > Render audio using audio card buffer size.**

- **Checked:** processing happens in batches matching the audio buffer. More efficient for
  DSP-heavy VSTs but can affect playback of *old* songs that rely on tight feedback or CV
  routings.
- **Unchecked:** internal rendering is fixed at 64-sample batches. Predictable feedback
  latency, more CPU on heavy plugins.

Default to checked unless you're loading a vintage feedback-routing song.

### Latency Compensation

Reason auto-compensates for round-trip latency when you record with **External Monitoring**
or via an outboard mixer (i.e. monitoring not through Reason).

If recordings land *too early*, apply a *negative* offset; if *too late*, *positive*.

### RAM Optimization

RAM scales with sample data. Reduce footprint:

- Delete unused audio recordings from tracks.
- Close other songs.
- Quit non-essential apps.
- Convert stereo samples to mono — halves memory.
- Resample down (e.g. 44.1 kHz instead of 96 kHz) where source quality permits.

### Song-level Optimization

**Bouncing (commit DSP to audio):**
- Bounce a Mix Channel that hosts a heavy instrument + insert chain to an audio track.
- Delete the original instrument track. The DSP is now baked into a wav.

**Device Hygiene:**
- Delete unused/inactive devices.
- Replace per-channel reverbs with a single send reverb.
- Use one sampler with multiple zones rather than many single-sample samplers.
- **Save and Optimize** — strips empty/freed disk space from the song file.

### Synth-specific Tips

| Device | Power-saving tactics |
|--------|----------------------|
| **Subtractor** | Disable Filter 2 / Osc 2 if unused. Avoid phase-mod and FM routings unless required. Turn off the noise generator when silent. |
| **Malström** | Use only Osc A if you don't need B. Connect only the filter outputs you actually use. Avoid running both filters + shaper simultaneously. |
| **Thor** | Unload unused filters and oscillators (the modular routing means unused slots can still cost). |
| **NN19, NNXT, Dr. Octo Rex, Grain, Redrum** | Turn off **High Quality Interpolation** unless audibly needed. Pre-resample sources for pitched playback. |
| **All polyphonic devices** | Set polyphony to the maximum you actually use — but **note that lowering polyphony alone doesn't help; only *active* voices cost CPU**. Shorten release times. Enable Low Bandwidth filtering when high-frequency detail isn't critical. |

### Effects Tips

| Effect class | Lighter alternative |
|--------------|--------------------|
| **Reverb** | RV-7 < RV7000. RV-7's Low Density algorithm is the cheapest tail. |
| **Distortion** | D-11 Foldback < Scream 4. |
| **Mono sources** | Disconnect right-channel returns (D-11, Scream 4, ECF-42, COMP-01, PEQ-2, DDL-1, MClass devices) — Reason halves the work. |
| **Mixer channels** | Disable EQ sections when unused. Connect mono sources to left input only. |

### System-level Best Practices

- One song document at a time.
- Latest ASIO drivers (Windows).
- Lower the *project* sample rate if you're CPU-bound and don't strictly need 96 kHz.
- Keep at least 20 GB free on a fast SSD/HDD.
- Disable unused channel-strip parameters (Input Gain, INV, EQ, Filters, Dynamics, Insert FX).
- Close background apps; disable non-essential system tasks.

### Do / Don't (Performance)

**Do this:**
- Bounce heavy instrument chains to audio once they're stable.
- Watch the per-device CPU readout *before* upgrading hardware — usually one or two devices
  are the culprits.
- Mono-ize sends and effects you didn't intend to use in stereo.
- Use **Save and Optimize** before archiving a finished song.
- Resample samples down when high frequencies aren't audible after the device's filter chain.

**Don't do this:**
- Don't lower polyphony as your only optimization — voices not currently sounding aren't
  costing you anything anyway.
- Don't run RV7000 on every channel; one send reverb covers most needs.
- Don't drop the audio buffer "just because" — only drop it when you need lower latency for
  recording or live monitoring.
- Don't enable HQ Interpolation everywhere; it's costly on every sample player.
- Don't leave background songs open when one is the focus.

### Pitfalls (Performance)

- **Polyphony myth:** lowering polyphony doesn't free CPU when those voices weren't being
  used. The setting only caps a maximum; idle slots are free.
- **VST/Rack Extension spikes:** third-party plugins are unpredictable. Profile with
  per-device CPU loads on; bounce or replace the worst offenders.
- **Swap-file thrashing:** if RAM fills, the OS pages to disk and audio breaks up
  catastrophically. Watch RAM, not just DSP.
- **Sample-rate mismatch:** running a session at 96 kHz when 44.1 kHz would do roughly
  doubles DSP cost.

---

## Cross-System Notes

These four systems share state and constrain each other:

- **Sync vs ReGroove:** under MIDI Clock slave, audio stretching disables but ReGroove still
  works (it's note-level, not audio-level).
- **Sync vs Performance:** Ableton Link mutes tempo automation; if a song depends on a tempo
  ramp for feel, Link will silently break it.
- **Remote vs ReGroove:** ReGroove parameters are *not* available to Keyboard Control. Use
  Remote Override if you need a hardware knob on a ReGroove parameter.
- **Remote vs Sync:** Control Surfaces and External Control Bus must live on **disjoint MIDI
  ports**. A port can't do both.
- **Performance vs Sync:** the Input Offset / Output Offset values for sync depend on your
  current audio buffer. Re-tune the offset when you change buffer size.
- **Performance vs Remote:** controller dropouts under heavy load are usually CPU saturation
  starving the MIDI thread. Treat dropped notes as a CPU symptom, not a controller fault,
  until proven otherwise.

## Quick-Reference: Where Things Live

| Task | Location |
|------|----------|
| Open ReGroove Mixer | Transport > **Groove** button |
| Route a lane to a groove channel | Lane's Groove Select pop-up |
| Get groove from a clip | Clip context menu > **Get from Clip** |
| Commit groove permanently | Edit menu / track context > **Commit to Groove** |
| Add a controller | Preferences > **MIDI** > Auto-detect or Add manually |
| Lock a surface | Options > **Surface Locking** *or* device context menu |
| Map a control to a parameter | Options > **Remote Override Edit Mode** |
| Map a key to a parameter | Options > **Keyboard Control Edit Mode** |
| Surface-level extras (track, patch, undo) | Options > **Additional Remote Overrides** |
| Pick sync mode | Transport Sync Mode selector / Options > **Sync** |
| MIDI Clock in/out ports | Preferences > **Sync** |
| External Control Bus | Preferences > **Other Controls** |
| Per-bus device routing | Hardware Interface > **ADVANCED MIDI** |
| Audio buffer | Preferences > **Audio** > Buffer Size |
| Threads | Preferences > **Audio** > Max audio threads |
| DSP meter | Transport panel |
| Per-device CPU readouts | Options > **Show CPU Load for Devices** |
| Strip a song down | File > **Save and Optimize** |
