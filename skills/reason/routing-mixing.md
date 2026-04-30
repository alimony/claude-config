# Reason 13: Routing, Cables & The Main Mixer
Based on Reason 13.4 documentation.

This skill teaches you how to route audio and CV signals, mix on the SSL-style Main Mixer, manage delay compensation, and configure the Hardware Interface for physical I/O. Use it whenever you're patching cables, building a mix, troubleshooting latency, or sending audio out to your interface.

## Mental Model: The Three Layers

Reason has three coexisting layers that all interact:

```
+---------------------------------------------------------+
|  MAIN MIXER (SSL-style remote control)                  |
|  -- Channel strips (EQ, dyn, inserts, sends, fader) --  |
+-----------------------+---------------------------------+
            ^           |
            | P-LAN     v
+-----------------------+---------------------------------+
|  RACK (devices: instruments, effects, Mix Channels,     |
|  Audio Tracks, Combinators, CV utilities)               |
|  Cables (audio + CV) connect on the REAR panel          |
+-----------------------+---------------------------------+
            ^           |
            | physical  v
+-----------------------+---------------------------------+
|  HARDWARE INTERFACE (top of rack, undeletable)          |
|  -- physical inputs/outputs to your audio interface --  |
+---------------------------------------------------------+
```

Mix Channels and Audio Tracks in the rack are the *back side* of channel strips in the Main Mixer. They are linked by an internal routing called **P-LAN** (not visible as cables). Everything else — synths, effects, CV — is patched with visible cables on the rear of the rack.

## Cables, Routing & CV

### Signal Types and Cable Colors

| Color | Meaning | Connector |
|---|---|---|
| Red | Audio between instruments and mixers | Large 1/4" jack |
| Green | Audio in/out of effect devices | Large 1/4" jack |
| Yellow | CV / Gate (modulation, triggers) | Mini jack |
| Blue | Combinator-internal connections | (varies) |

P-LAN connections (Mix Channel/Audio Track to Master Section) are invisible. Patching a Direct Out **breaks P-LAN** for that channel — you'll see `---` in the Audio Output display.

### Flipping the Rack

```
Front  <---[ Tab ]--->  Rear
```

- **Tab** flips the rack to see cables.
- Or: Options menu > "Toggle Rack Front/Rear", or click the Flip Rack button.
- **K** toggles cable visibility. Three modes available: show only for selected devices, hide auto-routed, or hide all (jacks then show colored dots).

Hide cables liberally during heavy patching — it makes the rack legible. Don't ship a session with hidden cables if a collaborator needs to read the routing.

### Connecting Cables Manually

Two ways:

1. **Drag method.** Click an output jack, drag, hover over a valid input (it highlights), release.
2. **Pop-up menu method.** Right-click (Win) / Ctrl-click (Mac) on the jack, pick a device from the menu, then choose the specific connector. An asterisk (`*`) marks an already-occupied connector.

To **disconnect**:
- Drag a cable end off the jack and drop it, OR
- Right-click / Ctrl-click the jack > "Disconnect", OR
- Select device(s), Edit menu > "Disconnect Device" to clear *all* cables on those devices.

To **find what's on the other end**: hover for a tooltip, or right-click / Ctrl-click > "Scroll to Connected Device".

To **abort a cable drag**: press **Esc** while dragging.

### Auto-Routing (the default)

When you create or duplicate a device, Reason routes it intelligently based on what's selected:

| You created... | With this selected... | You get... |
|---|---|---|
| Instrument | (nothing relevant) | New Mix Channel + connected to it |
| Instrument | Mixer 14:2 / Line Mixer 6:2 | First free input |
| Effect | Mix Channel / Audio Track | Insert effect on that channel |
| Effect | Master Section | Send effect on first free Aux Send/Return |
| Effect | rack mixer | Send effect on that mixer |
| Matrix Pattern | instrument | Note CV + Gate CV to Sequencer Control |
| RPG-8 | instrument | Note CV, Gate CV, Mod Wheel, Pitch Bend |

**Bypass auto-routing**: hold **Shift** while creating the device.
**Re-route after the fact**: select device, Edit > "Disconnect Device", then Edit > "Auto-route Device". Or hold **Shift** and drag a device to a new rack position.

### CV / Gate — Quick Reference

CV modulates parameters; Gate triggers events (note on/off, envelopes). You can only route CV/Gate from an output to an input.

**Trim knobs.** Every CV input has a Trim knob next to it.

```
Trim fully CCW = no modulation
Trim fully CW  = 100% modulation range (typically 0-127)
```

**Sequencer Control inputs** on synths are *monophonic* — designed for Matrix or RPG-8. Don't use them for polyphonic modulation.

**CV polarity (rules of thumb).**

```
Unipolar:  0  ........... +127     (envelopes, gate amounts)
Bipolar:  -64 ... 0 ... +64        (LFOs, pitch bend, pan modulation)
Gate:      off / on (trigger)      (note triggers, sample triggers)
```

Think before patching: a unipolar source into a bipolar destination only modulates "upward" from the current value. A bipolar LFO into a unipolar destination clips on the negative side. Use **Trim** plus the destination's existing offset (knob position) to dial in the right swing.

**Universal trick.** Route CV into a Combinator rotary; the Combinator can then modulate "virtually any parameter on any device" via its programmer.

### Common Cabling Patterns

**Sidechain compression via the mixer (preferred).**

```
Source channel  ----[ Parallel Out ]---->  [ Sidechain In ]  Destination Mix Channel
                                               |
                                               +-- KEY button auto-engages
                                                   compressor now ducks on source
```

If the source is taken (parallel out already used), tap the Insert FX "To Device" output, or split with a **Spider Audio Merger & Splitter**.

**Sidechain via CV (creative ducking).**

```
Mix Channel A  --[ Gain Reduction CV Out ]--> [ CV input ]  any device
```

Gain reduction CV from a channel's compressor can drive a filter cutoff (auto-wah), an LFO rate, etc.

**Trigger from drums to gate a synth.**

```
Drum loop channel --[ Sidechain In ]--+
Synth Mix Channel: KEY on, Gate threshold set
```

**Avoid feedback loops.** Cabling an output back through an effect chain into its own input creates a feedback loop. Reason will pass signal but **delay compensation ignores feedback paths** — and DC/runaway can blow your speakers. Use the Spider Audio device or a deliberate feedback-loop patch with a limiter if you want this on purpose.

## The Main Mixer (SSL-style)

The Main Mixer is "a remote control for Audio Track and Mix Channel rack devices." Channels are unlimited. Open it with **F5**; detach to its own window with **Ctrl/Cmd+F5**.

### Channel Strip Signal Flow (Default)

```
  IN  -> [Gain ±18 dB / Phase] -> [HPF/LPF Filters] -+
                                                     |
              +--------------------------------------+
              |
              v
        [ Dynamics: Gate/Expander + Compressor ]
              |
              v
        [ 4-band EQ: LF, LMF, HMF, HF ]
              |
              v
        [ Insert FX (rack devices) ]
              |
              v
        [ FX Sends 1-8 (post or pre fader) ]
              |
              v
        [ Pan, Width, Mute/Solo, Fader ]
              |
              v
        [ Output Bus selector ] -> Master Section (default)
                                   or sub-mixer Output Bus
```

### Reordering the Signal Path

Three buttons in the input section let you flip the order:

- **Insert Pre**: inserts go *before* dynamics + EQ
- **Dyn Post EQ**: EQ before dynamics
- **Insert Pre + Dyn Post EQ**: order becomes Insert -> EQ -> Dynamics

### EQ at a Glance

| Band | Range | Notes |
|---|---|---|
| HF  | 1.5k - 22k Hz | ±20 dB, optional bell |
| HMF | 600 - 7k Hz | parametric, Q 0.70-2.50 |
| LMF | 200 - 2k Hz | parametric, Q 0.70-2.50 |
| LF  | 40 - 600 Hz | ±20 dB, optional bell |
| HPF | 20 - 4k Hz | 18 dB/oct |
| LPF | 100 Hz - 20 kHz | 12 dB/oct |

**E mode** changes the curve and keeps bandwidth constant as gain changes. Toggle for a different character.

**Filters to Sidechain** routes the HPF/LPF as a *detector* feeding the dynamics — the dynamics still process the whole channel signal. Classic use: HPF the sidechain to make a compressor ignore kick-drum thumps (de-pumping) or keep the LPF on it for de-essing.

**Spectrum EQ window**: **F2**. Drag points = frequency + gain together. Hold **Shift** to constrain horizontal/vertical. **Alt/Option + drag** changes Q (HMF/LMF only). **Ctrl/Cmd-click** resets gain to 0 dB. Enable "Follow Selection" so it tracks the selected channel.

### Dynamics Quick Reference

Compressor:
- Ratio 1:1 to inf:1, threshold -52 to 0 dB
- Release 100-1000 ms (Auto on master)
- **FAST**: 3 ms attack
- **Peak** mode for snares/transient material
- Auto make-up gain

Gate / Expander:
- Range 0 to -40 dB, threshold -52 to 0 dB
- Hold 0-4000 ms, release 100-1000 ms
- **EXP** flips from gating to expansion
- **FAST**: 100 µs/40dB attack

### Inserts, Sends, and Returns

- **Insert FX** are local to the channel. Add by selecting the channel/device and using the Create menu — Reason routes them automatically.
- **Send FX** are global, attached to the Master Section, max **8 sends**.
- Each channel has FX Send 1-8 on/off + level knobs, plus a **PRE** button (toggles pre/post fader).

To add a send: select the Master Section (or any channel), context menu > "Create Send FX..." > pick a device. It connects to the next free Aux Send/Return.

To edit: click **EDIT** in the channel's FX Send section (or in the Master Section's FX Send/Return area) — the rack scrolls to it.

To copy a channel's settings: select source > "Copy Channel Settings >" choose section (Dynamics / EQ / Insert FX / All) > select destination > "Paste Channel Settings".

### Master Section

Final summing point for everything routed to Master Out.

```
[ All channels ] -> [ Master Inserts (default: post-comp) ]
                 -> [ Master Bus Compressor ] -> [ Master Fader ] -> Hardware Interface
```

Master Bus Compressor (the SSL-style one):
- Threshold -30 to 0 dB
- Ratio 2:1, 4:1, or 10:1
- Attack 0.1, 0.3, 1, 3, 10, 30 ms
- Release 0.1, 0.3, 0.6, 1.2 s, or **Auto**
- Make-up -5 to +15 dB
- **KEY** for external sidechain

**Master Inserts** are for mastering: limiter/maximizer, broad EQ. Default placement is *post* compressor — keep it there to avoid clipping the output. Use "Inserts Pre Compressor" only when you have a specific reason (e.g., shaping into the comp).

**Control Room outputs** are the monitor path. They are **separate from Master Out**. The Control Room selector can audition Master, FX Send 1-8, or FX Return 1-8 individually — invaluable for hearing what's hitting a reverb.

```
Do this:    Adjust monitoring with the Control Room level.
Don't:      Pull the Master Fader down to lower headphone volume.
            (You'll change the actual mix and any prints/bounces.)
```

### Output Busses (Sub-Mixers / Groups)

To group channels:

1. Select the channels (Shift-click range, Ctrl/Cmd-click non-contiguous).
2. **Ctrl/Cmd+G**, or context menu > "Route to > New Output Bus".

Output Bus channels have a colored background and red fader cap. Source channels show the bus name in their Output label. To reroute a channel: click the Audio Output selector at the top of the channel strip (or on the rack device).

If all channels leave a bus, it auto-converts back to a regular Mix Channel. To delete: select bus, delete — sources fall back to the Master Section.

To **record a sub-mix to disk**: enable Rec Source on the bus device, then choose it as the input on a fresh Audio Track.

### Parallel Channels

For New York-style parallel processing while keeping the dry signal:

1. Select the source Mix/Audio channel.
2. Edit menu > "Create Parallel Channel".

You get a "P1: <name>" channel cabled from the source's Parallel Out to the new channel's Direct In. Want more parallels? Chain from the last parallel (only one Parallel Out pair on the source).

For parallel bus compression: select multiple channels, **Ctrl/Cmd+G** for an Output Bus, then create a Parallel Channel on the bus.

### Mute / Solo Behavior in the Mixer

- Mute and Solo in the **Main Mixer are separate** from sequencer-track mute/solo.
- Multiple solos coexist. To mute one of them, you must un-solo it first.
- Solid green/red = manual; dim = automatic (e.g., follows a bus).
- Send FX levels follow Output Bus fader movements automatically — *unless* PRE is on. Knobs do not visually move when this happens.
- Muting an Output Bus mutes the Send FX returns from all routed channels. Muting a Parallel Channel only mutes that parallel's sends.

### Faders, Pan, Width

- Pan law is **-3 dB compensated**: a hard-panned signal is +3 dB louder than centered. Mind this when balancing.
- Width: stereo channels only, 0 (mono) to 127 (full stereo).
- Ganged adjust: select multiple channels, drag one fader — all selected move by the same dB. Works for Level, Mute, and Solo only.

### Navigation Shortcuts

- **F5** show/hide Main Mixer; **Ctrl/Cmd+F5** detach.
- **F2** Spectrum EQ window.
- Arrow keys = move between channels.
- Page Up/Down = scroll vertically.
- Home/End = leftmost/rightmost channel.
- Eight Show/Hide buttons toggle sections (Input, Dynamics, EQ, Inserts, FX Sends, Fader). **Alt/Opt-click** toggles all. **Ctrl/Cmd-click** shows just that section.
- **RACK** button on a channel: jumps to its source device (Shift-click on a Mix Channel jumps to the Mix Channel device itself, not the instrument).
- **SEQ** button: jumps to the sequencer track.

### A Sane Mixing Order (Best Practice)

```
1. Gain stage (input gain ±18 dB) so meters sit healthy
2. Subtractive EQ + filters (HPF rumble, scoop honk)
3. Dynamics (gate noisy mics, compressor for level)
4. Additive EQ (presence, air)
5. Insert FX (saturation, character, stereo treatment)
6. Sends (reverb, delay) -- usually post-fader
7. Group into Output Busses (drums, vox, bass, FX)
8. Bus processing (glue compression, EQ shaping)
9. Master Bus Compressor (gentle, 2:1, ~2-3 dB GR)
10. Master Inserts (limiter last, post-comp)
```

Don't reach for the Master Fader to fix loudness; use the limiter on Master Inserts and Control Room for monitor level.

## Delay Compensation

Plugins/devices with internal latency (lookahead compressors, FFT-based EQ, oversampling, resamplers) delay their channel relative to others. Without compensation you get comb filtering, phasing, and smeared transients — *especially* on parallel channels.

### How It Works

Reason finds the channel with the **longest** latency, then inserts invisible delays on every other channel so they all arrive at the Master Section in sync.

```
Ch 1: 4 samples device latency  -> +8 samples invisible comp = 12
Ch 2: 12 samples device latency -> 0 samples comp           = 12
                                          \_ everything aligned
```

Latency shows in samples on the channel strip and Transport panel. Hover for milliseconds.

### Toggling Delay Compensation

Three places:
- Master Section fader area — **Delay Comp** button
- Transport panel — **Delay Comp** button
- Options menu — Delay Compensation entry

### What Gets Compensated

| Path | Compensated? |
|---|---|
| Effects between instrument and Mix Channel | Yes |
| Insert FX (between To/From Insert FX jacks) | Yes |
| Effects on Parallel Out -> another Mix Channel | Yes |
| Mix channel -> Send FX bus | Yes (per channel) |
| Bouncing / Bounce in Place | Yes |
| Metronome click | Yes (handled at Hardware Interface) |

### What Does NOT Get Compensated

- Rack mixers (Mixer 14:2, Line Mixer 6:2) — outside the main mixer
- Direct Outs (P-LAN bypass) — totally outside the system
- Send Effect device's *own* internal latency
- Effects inside Instrument Combinators
- CV, MIDI, automation, MIDI Clock, Ableton Link
- Master Insert FX latency (applied equally to all signals, so no compensation needed)

### Manual Latency Adjustment

On the rear of any Audio Track or Mix Channel device, there's a manual latency display you can tweak when a plugin lies about its latency.

Constraint: the manual value can never be **less than** the sum of inherent latencies of devices in the Insert FX chain. Manual adjustment only works for Insert FX (between To Device and From Device).

### Recording with Delay Compensation

When monitoring through Reason, audio is repositioned earlier on tracks by:
```
Input Latency + Output Latency + total delay compensation
```

```
Do this:    Record with Delay Comp OFF and high-latency Insert FX bypassed.
            Bypass Master Insert FX during tracking and live playing.
            Switch Delay Comp back ON for mixing.
Don't:      Track vocals through a 3-second-lookahead limiter.
```

### Troubleshooting

- **Red LED on rear-panel Programmer section** = a non-standard routing was detected; compensation may not work for that channel.
- **"Could not calculate latency. The default value of 0 samples was used."** — broken or partial signal path. Check for missing cables or feedback loops.
- **Parallel paths**: only the *shortest* path with minimum latency drives compensation. If you split with the Spider, the longer leg is on its own.
- **Send effect latency mismatch**: Reason ignores Send FX device latency. If your reverb has 30 ms lookahead, all sends are early relative to it. Live with it, or insert the effect on a parallel channel instead of as a send.

## Hardware Interface

Always at the top of the rack. Cannot be deleted. This is where Reason meets your audio interface.

### Layout

- Default panel: 2 Sampling Inputs, 16 Audio Inputs, 16 Audio Outputs.
- Expand via the **More Audio** panel up to 64 in / 64 out.
- 2 dedicated **Sampling Inputs** (L/R) for sampling devices, with Level knob and Monitor.

### Channel LEDs

| Color | Meaning |
|---|---|
| Green | Available + cable connected |
| Yellow | Available, no cable connected |
| Red | Cable connected but channel unavailable (driver mismatch) |
| Unlit | Unavailable and unconnected |

If you see **red**, your cabling expects a channel that's not currently mapped on your audio interface. Check Preferences > Audio for active channels, or repatch.

### Clipping — Read This

> The Hardware Interface is where any possible audio clipping will occur in Reason.

Internal Reason buses are 32-bit float — practically uncippable until they hit the integer-domain converters in the Hardware Interface. Watch:
- Transport panel clip indicator.
- Per-channel meters on the Hardware Interface.
- The **BIG METER** panel for detailed visualization.

If a channel hits red, **reduce gain at the source** (the channel sending to that output), not at the Hardware Interface.

### Big Meter Modes

| Mode | Behavior |
|---|---|
| VU | RMS, 300 ms response — overall loudness |
| PPM | 0 ms rise / 2.8 s per 24 dB fall — transient peaks |
| PEAK | 0 ms both ways — true real-time peak |
| VU+PEAK | combined |
| PPM+PEAK | combined |

Use PEAK when checking against true-peak limiting. VU when balancing perceived levels.

### Routing to Physical Outputs

By default, the Master Section's main outs go to Hardware Interface outputs 1/2. To break out a stem to a separate physical output:

1. Flip rack with **Tab**.
2. On the source (e.g., a Mix Channel), patch its **Direct Out L/R** to free Hardware Interface inputs (channels 3/4, etc.).
3. The channel will display `---` for Audio Output (P-LAN broken — that channel no longer sums into Master).
4. Configure your audio interface's outputs accordingly.

If you only want a parallel feed (channel still goes to Master too), use the **Parallel Out** pair instead — it's a tap, not a break.

### MIDI Routing — Advanced MIDI Device

This routes external MIDI to *specific rack devices*, bypassing Reason's sequencer.

Setup:
1. Select an External Control Bus (up to 4 buses available).
2. Assign devices to MIDI channels via the dropdowns. 16 channels per bus = up to 64 routings total.
3. Send MIDI from your external sequencer / hardware.

```
Don't:  Use the Advanced MIDI Device if you're only using Reason's
        internal sequencer for record/playback. It will conflict.
```

### Sampling Inputs

The 2 Sampling Inputs feed Reason's sampler devices directly. Route the audio you want to sample here, set Level, optionally enable Monitor, and sample from a sampler device.

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Direct Outs in use | Channel shows `---` Output, not summing to master | Repatch via Audio Output selector to "Master Section" |
| Hidden cables | Routing makes no sense, devices seem disconnected | Press **K** to cycle hide modes, **Tab** to see rear |
| Feedback loop | Runaway level, digital noise, no comp on that path | Spider in/out, or insert a limiter; check delay-comp red LED |
| Wrong CV polarity | Modulation only goes "up" or "down", or clips | Switch source (LFO bipolar vs envelope unipolar), use Trim |
| Polyphonic into Sequencer Control | Notes drop | Route Note CV/Gate from Matrix or RPG-8 only |
| Master Fader for monitor volume | Mix changes / bounces are too quiet | Use Control Room level instead |
| Tracking through Delay Comp | Performer hears late playback | Disable Delay Comp + bypass high-latency inserts when tracking |
| Effect inside Combinator | No delay compensation on that effect | Pull effect out to channel insert if you need comp |
| Clipping at Hardware Interface | Red on hardware meter even though channels look fine | Lower at source channel/group, not at master/HW |
| Red LED on Programmer rear | Comp can't calculate this routing | Simplify: avoid feedback / external loops on that channel |

## Keyboard Shortcuts (Quick Reference)

| Shortcut | Action |
|---|---|
| **Tab** | Flip rack front/rear |
| **K** | Toggle cable display modes |
| **F5** | Show/hide Main Mixer |
| **Ctrl/Cmd+F5** | Detach Main Mixer to a window |
| **F2** | Spectrum EQ window |
| **Shift** + create device | Create without auto-routing |
| **Shift** + drag device | Re-route while moving |
| **Esc** while dragging cable | Abort connection |
| **Ctrl/Cmd+G** | Create Output Bus (or Parallel Channel on a bus) |
| **Ctrl/Cmd-click** channel | Add to non-contiguous selection |
| **Shift-click** channel | Range-select |
| **Alt/Opt-click** show/hide button | Toggle all sections |
| **Arrow keys** | Move between channels |
| **Home / End** | Leftmost / rightmost channel |
| **Page Up/Down** | Scroll mixer vertically |
| **Delete / Backspace** | Delete selected channels (with track + device) |

## Worked Examples

### Example 1: Build a drum bus with parallel compression

```
1. Select all drum channels (kick, snare, hats, OH, room).
2. Ctrl/Cmd+G  -> "Drums" Output Bus.
3. With Drums selected, Edit > Create Parallel Channel -> "P1: Drums".
4. On P1: Drums, add a heavy Insert FX compressor (4:1, fast attack, ~6dB GR).
5. Blend P1 fader to taste under the dry Drums bus.
6. Add gentle Master Bus-style glue comp on the Drums bus itself
   (2:1, slow attack, auto release, ~2 dB GR).
```

### Example 2: Sidechain a pad to the kick

```
1. Find the kick's Mix Channel device (rear of rack).
2. Patch kick Parallel Out L/R -> Pad Mix Channel Sidechain L/R.
3. KEY auto-engages on the pad's compressor.
4. On the pad channel, set Ratio 4:1, threshold so each kick gives ~6 dB GR,
   fast attack, release ~150-300 ms.
5. (Optional) Turn off the kick's contribution by patching from Insert FX
   "To Device" tap if you want pre-comp kick to drive it.
```

### Example 3: Stem out to a hardware reverb on outputs 3/4

```
1. Tab to flip rack.
2. Add a new Mix Channel "ToHWVerb"; lower its fader to 0 dB and PRE its sends if needed.
3. From "ToHWVerb" Direct Out L/R -> Hardware Interface inputs 3/4.
4. Route hardware reverb returns to Hardware Interface outputs that come back
   into a fresh Audio Track for record + monitoring.
5. Note: Reason's delay compensation does NOT cover external loops; align by ear
   or use the manual latency offset on the return Audio Track.
```

### Example 4: Diagnose phasing on a parallel snare

```
Symptom: parallel snare bus sounds hollow / comb-filtered when blended.
1. Verify Delay Comp is ON (Master Section / Transport / Options).
2. Check Programmer rear LED on both snare channels -- red = bad routing.
3. Check that the parallel chain does NOT contain a feedback loop.
4. If a Send FX is in the chain, remember send latency is NOT compensated --
   move the effect from a send to an insert on a parallel channel.
5. Last resort: manually adjust latency on the Audio Track / Mix Channel rear.
```
