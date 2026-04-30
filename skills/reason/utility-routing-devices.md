# Reason 13: Utility, Routing & MIDI Devices
Based on Reason 13.4 documentation.

This skill covers the six "glue" devices that hold a Reason rack together: the Combinator container, two analog-style sub-mixers (Line Mixer 6:2 and Mixer 14:2), the Matrix step sequencer, the Pulsar dual LFO, and the RPG-8 arpeggiator. These are not sound sources by themselves (Combinator excepted) but they shape how sound flows, gets sequenced, and gets modulated.

## Comparison table

| Device          | Role                                               | CV out                                                                    | Sequencer-driven        | Typical placement                                                  |
|-----------------|----------------------------------------------------|---------------------------------------------------------------------------|-------------------------|--------------------------------------------------------------------|
| Combinator      | Container / macro / patch wrapper                  | 4 panel-control CVs (rotaries) routed via Modulation Routing              | Yes (sequencer track)   | Wrapping any group of instruments and/or effects                   |
| Line Mixer 6:2  | 6-stereo-channel sub-mixer                         | 1 pan CV per channel                                                      | No                      | Inside Combinators; small group sub-mixes                          |
| Mixer 14:2      | 14-stereo-channel mixer with EQ + 4 aux sends      | Level + Pan CV per channel; Master Level CV                               | No                      | Standalone group mixing; chained for >14 sources                   |
| Matrix          | 32-step pattern sequencer (note + gate + curve)    | Note CV, Gate CV, Curve CV (uni/bipolar)                                  | Yes (pattern lane)      | Driving Sequencer Control inputs of a synth, or modulating CV ins  |
| Pulsar          | Dual LFO with AR envelope                          | 2× LFO CV + inverted + audio outs, summed CV/audio out, Envelope CV out   | Tempo-syncable          | Modulating filter, pitch, pan, FX params                           |
| RPG-8           | Monophonic arpeggiator                             | Note CV, Gate CV, Mod Wheel, Pitch Bend, Aftertouch, Expression, Breath, Start-of-Arp Trig, Sustain Gate | Yes (Arp track) | Above an instrument; inside Combinator wrapping a single synth    |

Quick legend:
- "CV out" means rear-panel CV cables — voltage signals, not MIDI.
- "Sequencer-driven" means the device responds to transport play/stop and pattern-lane automation.

---

## Combinator

### Type and role
Container device. Wraps any number of instruments, effects, mixers, and (stand-alone only) VST devices into one self-contained patch (`.cmb`). Two flavours:

- **Instrument Combi** — contains at least one instrument; produces sound from MIDI/key input.
- **Effect Combi** — only effects; processes audio from external input.

The Combinator Mixer always sits at the top of the container and cannot be removed. It provides 8 stereo "From Devices" inputs and "To Devices" sends — the internal bus that keeps a Combi self-contained.

### Best uses
- Layered patches (split bass + pad + lead by key range or velocity).
- Macro controls — one knob morphing many parameters across many devices.
- Reusable effect chains saved as a single patch.
- Wrapping a synth + its modulators (Matrix, Pulsar, RPG-8) so the whole rig moves together.
- Performance setups where four rotaries + four buttons are the only thing the player touches.

### Front panel anatomy
- **4 assignable rotaries** + **4 assignable buttons** by default. You can extend the panel up to **32 knobs/faders + 32 buttons** plus the two wheels, Run, and Bypass FX.
- **Pitch Bend wheel + Mod Wheel** — mirror master keyboard.
- **Run button** — starts/stops pattern devices (Matrix, Redrum, RPG-8) inside the Combi.
- **Bypass FX** — bypasses all effects in the Combi (does not toggle devices already individually disabled).
- **Panel size**: 1U–6U. Background can be solid colour, default texture, or a custom JPEG/PNG.

Backdrop image dimensions (optimal width 3770 px):
- 1U: 345 px
- 2U: 690 px
- 3U: 1035 px
- 4U: 1380 px
- 5U: 1725 px
- 6U: 2070 px

### Programmer pane (Editor)
The Editor exposes three columns of programming data for every device inside the Combi:

**1. Key Mapping section**
- **Lo Key / Hi Key** — define the keyboard range that triggers a given device. C-2 to G8 MIDI range.
- **Lo Vel / Hi Vel** — define velocity zone (0–127) for velocity layers/crossfades.
- **Transpose** — independent ±36 semitones per device, doesn't move the key range.
- **Receive Notes** toggle — turn off to make a device CV-only inside the Combi.
- **Performance Controllers** — per-device toggles for Pitch Bend, Mod Wheel, Breath, Expression, Sustain, Aftertouch.

**2. Modulation Routing section**
The heart of the Combinator. Up to **4 mappings per rotary/button** by default, more on extended panels. Each row has:
- **Source** — Rotary 1–4, Button 1–4, or any of the 8 panel-control / wheel CV / source CV inputs.
- **Target** — any parameter on any device inside the Combi.
- **Min** / **Max** — value range of the target parameter. **Reverse the mapping** by swapping Min and Max so turning the knob right decreases the target.
- **Source Range** (where exposed) — restricts which portion of the controller is active.

Right-click any device parameter and choose **Map to Combi Control** to assign in one step.

**3. CV Source list (rear-panel inputs)**
Eight modulation inputs each with a sensitivity knob and a **Unipolar/Bipolar** polarity switch. Use Unipolar for envelope-style sources (LFO that should always go positive), Bipolar for LFO-style sources you want to swing around centre.

### Init patch behaviour
**File > New Combinator Patch** loads an empty Combi. Right-click the Combinator and choose **Initialize Patch** to clear all devices/mappings to a blank state.

When you wrap existing devices using **Edit > Combine** (Ctrl/Shift-click multiple devices first), Reason auto-routes them through the Combi Mixer's From/To Devices pairs. Effects placed after instruments auto-route as inserts; new instruments take the next available stereo input.

Modifier keys when dragging devices into a Combi:
- **Plain drag** — move + auto-route.
- **Shift-drag** — move without auto-routing (manual cabling).
- **Alt/Option-drag** — copy instead of move.

### Combinator + Players
Players (Note Echo, Scales & Chords, Dual Arpeggio, etc.) sit **above** an instrument or Combinator in the rack and process incoming MIDI before the instrument receives it. With a Combinator:

- A Player at Combi level processes notes once, then those processed notes are distributed to every instrument inside the Combi according to each device's key/velocity range.
- Players placed on individual sequencer tracks for devices inside the Combi only affect their own track — useful for arpeggiating only one layer of a stack.
- Player order matters: top-down. Scales & Chords above Dual Arpeggio means scale-correct chords get arpeggiated; flip the order and you arpeggiate raw notes then quantise to scale (different result).
- The Combinator Run button starts pattern-device-style Players that have a Run state.

### Rear-panel CV
- **Sequencer Control** — Note CV in (pitch), Gate CV in (gate + velocity). Lets external Matrix/RPG-8/Pulsar play the whole Combi as one voice.
- **Control CV In 1–4** — each with attenuator + dropdown to target any front-panel control directly.
- **Wheel CV / Source CV inputs** — eight extra modulation entries assignable in the Editor.

### Audio in/out
- **External In L/R** — for effect Combis only.
- **External Out L/R** — feed the host mixer / next device.
- All internal device cabling should pass via the Combi Mixer's **To Devices / From Devices** pairs. If you bypass these (cable directly to External Out), the **External Routing LED** lights and the Combi is no longer self-contained — those connections won't survive a save/reload.

### Pitfalls and gotchas

> **Don't this**: Cable a synth's output directly to the Combinator's External Out. The cable will not save with the patch. The External Routing LED is your warning sign.
> **Do this**: Route the synth into a "From Devices" input on the Combi Mixer; the Combi Mixer's master goes to External Out automatically.

- **CPU stack**: every Combi adds a thin overhead, and Combis-of-Combis multiply that. You **cannot put a Combi directly inside another Combi** — combining two Combis uncombines the lower one. To "nest", you have to leave both as siblings or accept the uncombine.
- **Mix Channel / Audio Track devices** cannot be in the selection when you press Combine; Reason will refuse.
- **Maximum panel objects**: 32 knobs/faders + 32 buttons + 2 wheels + Run + Bypass FX. Sounds like a lot until you build a 4-layer hybrid pad.
- **Performance recording**: rotary movements record into the Combinator's track (not the contained device tracks). Automation lives at the Combi level.

> **Quick recipe — Macro morph pad**
>
> 1. Combine: Subtractor + Thor + RV7000.
> 2. Map **Rotary 1** → Subtractor Filter Freq (Min 30, Max 127) AND Thor Filter 1 Freq (Min 30, Max 127) on the same rotary.
> 3. Map **Rotary 2** → RV7000 Dry/Wet (Min 0, Max 90).
> 4. Map **Rotary 3** to Subtractor Mix (osc 1↔2) Min 0 Max 127 AND Thor Osc 1 Index Min 1 Max 64 — one knob morphs spectral content of both synths in opposite directions if you reverse one (Min 64 Max 1).
> 5. Map **Button 1** → Thor Voice 2 / Voice 1 Polyphony toggle, or use it to enable a chorus effect.

---

## Line Mixer 6:2

### Type and role
A small, no-frills 6-channel stereo sub-mixer. No EQ, single aux send/return per channel.

### Best uses
- The default sub-mixer **inside Combinators** when you have more than the 4 stereo From-Devices pairs would conveniently allow.
- Quick group bus when full Mixer 14:2 is overkill.
- Drum bus for Redrum's individual outs.

### Channel strip (per channel × 6)
- **Level** — channel fader.
- **Pan** — Ctrl/Cmd-click resets to centre.
- **Mute (M)** / **Solo (S)** — multiple Solos can stack.
- **Aux Send** — single send to one effect bus.
- **Channel meter** — red zone warns of clipping.

### Aux section
- One **Aux Send** bus → external effect device input.
- One stereo **Aux Return** → mixed back into master.
- A **Pre/Post** switch on the Send Out determines whether the send taps before or after the channel level fader.

### Master section
- Single **Master L/R fader** controls summed output, auto-routed to the first available Mix Channel device.

### Rear-panel I/O
- 6 stereo inputs (use just the L input for mono sources — auto-mono).
- **Pan CV input per channel** (one CV per channel — that's it).
- Master L/R out, Aux Send out, Aux Return in.

### Pitfalls
- **No EQ**. If you need tone-shaping, either insert EQ on the source or use Mixer 14:2.
- **Only one aux**. Multiple parallel effect paths require an external Spider Audio Splitter or Mixer 14:2.
- **Mute/Solo do not chain** when you slave another mixer; behaviour is per-mixer.

---

## Matrix Pattern Sequencer

### Type and role
A 32-step monophonic pattern sequencer that emits **Note CV**, **Gate CV**, and **Curve CV**. It produces no sound; it controls other devices via their Sequencer Control or modulation inputs.

### Best uses
- Vintage step-sequenced bass lines (TB-303 style).
- Triggering Redrum gate channels for hands-on drum patterns.
- LFO replacement when you need a tempo-locked, irregular modulation curve (route Curve CV to a synth's filter freq input).
- Quick melodic ideas that you later **Copy Pattern to Track** and edit as MIDI.

### Pattern memory
- **4 banks (A–D)** × **8 patterns each = 32 pattern slots** per Matrix.
- Pattern length: **1–32 steps** (Steps spin control). Shortening hides steps but preserves data if you re-extend.
- **Resolution** knob sets playback rate relative to transport (1/2 down to fine 1/128 etc.).
- **Shuffle** toggle per pattern; intensity is **global** via the ReGroove Mixer's Global Shuffle.
- **Pattern Enable** switch — disables playback at next downbeat without clearing.

### Output types
**Note (Key) CV** — emits semitone pitch. Wire to a synth's **Sequencer Control: CV** input. In Subtractor/Malström/NN-19/NN-XT this auto-plays one voice.

**Gate CV** — note-on/off plus a velocity-like level (the height of the gate bar in the lower lane). Wire to **Sequencer Control: Gate** to trigger notes, or to a Redrum channel's gate input to trigger a single drum step pattern.

**Curve CV** — independent step lane for non-pitch parameters. Two modes:
- **Unipolar** — 0 to +max. Empty steps = 0. Good for filter cutoff, level.
- **Bipolar** — centre = 0, swings positive and negative. Good for pan, pitch bend amount, anything zero-centred.

The Matrix also generates a **Gate trigger automatically whenever a Curve step rises out of zero**, which is an easy way to get rhythm out of a curve lane without programming gates.

### Editing patterns
- **Keys mode** (switch position) — upper grid edits pitch (one note per step), lower grid edits gate height/velocity.
- **Curve mode** — single grid edits the curve lane.
- **Tie** switch (or **Shift-click** while drawing in the gate lane) — turns a gate into a tied/legato note that's twice the visible width and twice the duration. Stack consecutive ties for long slides.

Pattern manipulation buttons:
- **Shift Left/Right** — moves the whole pattern one step preserving rhythm.
- **Shift Up/Down** — transposes notes ±1 semitone (Curve unaffected because it isn't semitone-based).
- **Randomize Pattern** — generates fresh random Note + Gate + Curve.
- **Alter Pattern** — mutates an existing pattern (requires non-empty pattern).
- **Copy / Cut / Paste / Clear** — across patterns, banks, or whole songs. Clear preserves length, resolution, and shuffle.

### Sequencer track integration
- The Matrix lives on a sequencer track with a **pattern automation lane** for switching banks/patterns at clip boundaries. Changes happen on the **next downbeat**.
- **Mute the Matrix track** to instantly mute every instrument it's driving.
- **Run** button enables free-running playback when the main transport is stopped; auto-syncs when transport starts.
- **Copy Pattern to Track** — converts the current pattern into a note clip on the track between the locators. **Curve CV is not converted** (you'd need to render audio if you want to preserve it). One note per step where Gate > 0.
- **Convert Pattern Automation to Notes** — processes recorded pattern lane changes across multiple clips, gives you regular MIDI clips. After conversion, Pattern Enable is auto-disabled. Move the resulting clips to the target instrument's track manually.

> **Quick recipe — TB-303 acid line**
>
> 1. Create Subtractor with Matrix selected; outputs auto-route Note + Gate.
> 2. Subtractor settings: **Polyphony = 1**, **Trigger Mode = Legato**, **Portamento ≈ 50**, square or sawtooth osc, low filter cutoff with high resonance, short envelope decay.
> 3. In Matrix Keys mode, draw notes on root/5th/octave; on selected steps **Shift-click in the gate lane to tie** — those become the slides.
> 4. Add **DDL-1 delay** and **Scream / D-11 distortion** after the synth.
> 5. Pattern length 16; resolution 1/16; Shuffle ON to taste.

> **Quick recipe — Curve CV as filter LFO**
>
> 1. Disconnect Note + Gate CV from the synth (you only want modulation).
> 2. Wire **Curve CV → Subtractor Filter 1 Freq modulation input**.
> 3. Bipolar mode if you want the cutoff to swing both ways from current setting; Unipolar to only push it up.
> 4. Set Resolution to 1/8 or 1/4 for slow rhythmic sweep, 1/32 for nervous tremolo.

### Pitfalls
- **Per-pattern memory**: each of the 32 slots stores Note, Gate, *and* Curve in one block. There's no way to "play pattern A1 for notes and B2 for curve" simultaneously — if you need that, use a second Matrix.
- **Randomize / Alter affect Note, Gate, AND Curve at once.** No way to randomize only one lane.
- **Monophonic only** — one note per step. Chords need a separate Matrix (and a Spider CV merger) per voice.
- **Curve CV cannot be exported to track**, only Note/Gate.

---

## Mixer 14:2

### Type and role
The classic full-fat Reason mixer: 14 stereo channels, 2-band EQ, 4 stereo aux sends, master section. The big-brother to Line Mixer 6:2.

### Best uses
- Standalone song mixer for small-to-medium projects (chain two for 28 channels).
- Group bus mixer when you want EQ on the bus.
- Inside large Combinators where 6:2 would run out of channels.

### Channel strip (per channel × 14)
- **Level fader** (0–127).
- **Pan** (-64 to +63, 0 = centre; Ctrl/Cmd-click resets).
- **Mute / Solo** — multiple Solos additive; Solos can't be muted.
- **EQ** — 2-band shelving:
  - **Treble**: 12 kHz, ±24 dB.
  - **Bass**: 80 Hz, ±24 dB.
  - **EQ on/off** toggle button per channel.
  - **Improved EQ** (current) vs **Compatible EQ** (legacy) global mode.
- **Aux Sends 1–4** (0–127, post-fader by default).
  - **Aux 4 has a Pre/Post (P) button** — useful for headphone cue mixes that ignore the main fader.
- **Channel meter** with red clip indicator.

### Master section
- **Master L/R fader** controls summed output.
- 4 stereo **Aux Returns** with their own level knobs.
- Master output auto-routes to the first available Mix Channel.

### Rear panel I/O
- 14 stereo inputs (L only = mono).
- **Level CV in** + **Pan CV in** per channel — voltage automation of every channel.
- **Master Level CV in** with trim pot.
- 4 stereo **Aux Send outs** + 4 stereo **Aux Return ins**.
- **Chaining Master In** + **Chaining Aux Ins** for daisy-chaining.

### Chaining mixers
Create a second Mixer 14:2 with the existing one selected. Reason wires:
- New Mixer's Master Out → original Mixer's **Chaining Master** input. The original's master fader controls both.
- New Mixer's 4 Aux outs → original's **Chaining Aux** ins. Both share the same effect returns.

> **Don't this**: chain four mixers and expect Solo to work globally. **Mute/Solo do not chain.**
> **Do this**: Solo on the destination mixer that contains the channel you want, or use a single bigger setup.

You can partially chain — disconnect specific Aux Send/Chaining cables to give a sub-mixer its own independent FX returns.

### Signal flow
Channel In → Pan/EQ → Level Fader → (Aux Sends tap here) → Master Out. Solo includes Aux Send effects in the soloed signal, so you hear the channel with its reverb, not dry.

### Pitfalls
- The 12 kHz / 80 Hz EQ is fixed-frequency. For surgical work, insert a parametric EQ on the channel.
- **Pre-fader Aux 4 only**. If you need pre-fader on Aux 1–3, route via a Spider Audio splitter.
- Aux Returns have no EQ and no pan — what comes back is what comes back.

---

## Pulsar Dual LFO

### Type and role
Two independent, modulatable LFOs in one device, plus an AR envelope. Outputs CV **and** audio-rate signals. Each LFO can modulate the other for FM/AM/sync experiments.

### Best uses
- Tempo-synced filter / pitch / pan / FX modulation (vibrato, tremolo, panning).
- Audio-rate modulation as a poor-man's monosynth (sine LFO at 1.05 kHz with KBD Follow + envelope is a working two-osc voice).
- Driving the **Phase** or **Shuffle** input of *another* LFO for evolving rhythmic modulation.
- Using the AR envelope as a triggerable transient generator independent of the LFOs.

### Per-LFO controls (LFO 1 and LFO 2 share these)
- **Rate** — frequency. Free mode: **0.06 Hz – 1.05 kHz**. Tempo Sync mode: **32/4 down to 1/64** note resolution. Modulating Rate can push beyond default range.
- **Waveform selector** — **9 waveforms**: sine, triangle, sawtooth, square / pulse, plus random, slope, and stepped variants. **All waveforms are bipolar** (swing positive and negative around 0).
- **Level** — output amplitude.
- **Phase** — 0°–360° offset — where in the cycle the wave starts on retrigger.
- **Shuffle** — 50%–75% — affects pairs of cycles, gives swing to LFO output.
- **Lag** — lowpass smoothing of the output; turns a square into a smooth ramp at high settings.
- **Tempo Sync** button — locks Rate knob to musical divisions.

### LFO-specific extras
- **LFO 1 only**: **ENV Sync** button — restarts LFO 1 every time the AR envelope retriggers.
- **LFO 2 only**: **On/Off** activation switch + **LFO 2 Trig** button (manually fires envelope from LFO 2).

### Sync modes summary
- **Free Running** — independent oscillator.
- **Tempo Sync** — Rate knob picks musical division.
- **ENV Sync** (LFO 1) — restarts on envelope trigger.
- **LFO 2 → LFO 1 Sync** — every new LFO 2 cycle restarts LFO 1, creating polyrhythmic patterns.

### LFO 2 → LFO 1 cross-modulation
- **Rate Mod** — LFO 2 frequency-modulates LFO 1 (FM).
- **Level Mod** — LFO 2 amplitude-modulates LFO 1 (AM).
- **Sync** — phase-resets LFO 1 each LFO 2 cycle.

### AR envelope
- **Attack**: 0.1 ms – 3.00 s.
- **Release**: 0.0 ms – 10.00 s.
- **Trigger sources**: front-panel Manual Trig button, every LFO 2 cycle, **CV Gate In**, MIDI Note On.
- **Modulation outputs**: separate **Rate** and **Level** mod amount knobs for both LFOs (bipolar — centre = no mod). So one envelope can sweep LFO 1 rate up while pulling LFO 2 level down, or vice versa.

### Outputs (rear panel)
Per LFO:
- 2× **CV out** + 2× **inverted CV out**
- 2× **audio out** + 2× **inverted audio out**

Combined:
- 1× **CV out (LFO 1 + 2 summed)**
- 1× **audio out (LFO 1 + 2 summed)**

Envelope:
- **Envelope CV Out**
- **Envelope Gate In**

### Modulation inputs (per LFO)
**Rate**, **Phase**, **Shuffle**, **Amount/Level** — each with its own attenuator. So you can patch external CV into any of these on a per-LFO basis.

### KBD Follow
Bipolar parameter that makes LFO rate track MIDI notes:
- **0** (centre) — no tracking.
- **+100** — chromatic 1:1 with MIDI notes; centre note **C3**.
- **-100** — inverse: higher notes give slower rates.

This is what makes audio-rate Pulsar work as a pitched oscillator.

### Patching examples

> **Quick recipe — Tempo-synced filter wobble**
>
> 1. Create Pulsar after a synth.
> 2. LFO 1: triangle, **Tempo Sync ON**, Rate **1/8**.
> 3. Cable **LFO 1 CV Out → Synth Filter Freq mod input**.
> 4. Adjust Lag to taste — higher Lag for smooth wave, 0 for stepped.

> **Quick recipe — Evolving polyrhythm**
>
> 1. LFO 1: sine, Tempo Sync, **1/4**. Output → some target.
> 2. LFO 2: square, Tempo Sync, **1/3** (dotted-related). Cable **LFO 2 CV Out → LFO 1 Phase mod input**.
> 3. Now LFO 1's phase is being shoved around at LFO 2's rate, creating cross-rhythms that never quite repeat the same way.

> **Quick recipe — Pulsar as a VCO**
>
> 1. LFO 1: sine, **Free** mode, Rate around 440 Hz region.
> 2. **KBD Follow = +100**.
> 3. Cable **Envelope Gate In ← MIDI Note On / external Gate**.
> 4. Patch one of the **audio outs** through a filter and amp (or another Pulsar's envelope) to a Mix Channel.

### Pitfalls
- LFO output is **always bipolar**. To use it as a unipolar modulator (e.g. always-positive filter sweep), feed it through a Combinator CV input set to **Unipolar polarity**, or scale/offset elsewhere.
- **Audio-rate use eats CPU** — at 1 kHz with stepped waveforms you're effectively running an aliasing oscillator. Add Lag if you want to soften it.
- Phase modulation of an LFO that is also Tempo Synced can break the perceived sync — be intentional.

---

## RPG-8 Monophonic Arpeggiator

### Type and role
A monophonic arpeggiator. Takes incoming MIDI notes (live or sequenced), generates an arpeggio pattern, and outputs **Note CV + Gate CV** plus a stack of performance-controller CVs. Sits above an instrument or inside a Combi.

### Best uses
- Classic synth arpeggios over a sustained chord.
- Driving any device's Sequencer Control inputs with rhythmically rendered note streams.
- Wrapped in a Combi with a synth + delay for performance-style trance/euro-style stabs.

### Modes
The **Mode** switch — five directions:
- **Up** — lowest to highest, repeat.
- **Up+Down** — lowest to highest then back, no endpoint repetition.
- **Down** — highest to lowest, repeat.
- **Random** — input notes arpeggiated in random order.
- **Manual** — notes play in the order they were input (great for melodic hooks where order matters).

### Octave range
Four buttons stack the pattern across:
- **1 Oct** — straight notes only.
- **2 Oct** — pattern repeats one octave up.
- **3 Oct** — three-octave span.
- **4 Oct** — four-octave span.

### Insert (note repetition)
Adds intermediate notes between arpeggio steps:
- **Off** — none.
- **Low** — lowest note interleaves between every second note.
- **Hi** — highest note interleaves.
- **3-1** — play 3 notes forward, step 1 back, repeat (longer melodic shape).
- **4-2** — play 4 forward, step 2 back.

### Gate length
Continuous control: **0** = no output (gate closed) up to **Tie** at maximum (gate stays open between notes — legato).

### Rate / sync
- **Sync mode** — straight, dotted, or triplet values from **1/2** to **1/128**.
- **Free mode** — 0.1 Hz – 250 Hz, free-running, ignores transport tempo.

### Shuffle vs straight
The RPG-8 has its own **Shuffle on/off** toggle. Intensity is **global**, set via the ReGroove Mixer's Global Shuffle (same shared value as Matrix and Redrum). To swing only one device, you have to use a separate Groove channel in the ReGroove Mixer and apply it just to that track.

### Pattern editor
A 16-step on/off grid:
- Click a step to **darken** = rest at that step.
- **+/− buttons** set length 1–16 steps.
- Pattern functions: **Alter Pattern**, **Randomize Pattern**, **Invert Pattern**, **Shift Pattern L/R**.
- Pattern automation works via **snapshots** — record the whole-pattern state at points in time, not individual steps.

### Velocity
- Knob 0–127 sets a fixed output velocity, **OR**
- **Manual (Man.)** mode passes input velocity through unchanged.
- **Velocity CV In** on the rear panel modulates velocity at signal rate.

### Single Note Repeat
- **On** — a held single key retriggers the gate: note repeats.
- **Off** — single keys play through unchanged; arpeggio only kicks in with two or more notes (chords).

### Hold
- Keeps the arpeggio running after you release all keys.
- Adding more keys merges them into the running pattern.
- Responds to the **Sustain Pedal** (sustain = hold-on while pedal down).

### Octave Shift
Transposes output ±3 octaves in semitone steps. Has its own CV input.

### Rear panel CV
**Inputs:**
- **Gate Length CV In**
- **Velocity CV In** (sums with knob value)
- **Rate CV In**
- **Octave Shift CV In**
- **Start of Arpeggio Trig In** — gate-trigger here forces the arpeggio to restart from step 1. Critical: if you patch this input, **no arpeggio is generated unless a gate trigger is received**. So either patch nothing or patch a deliberate trigger source.

**Outputs:**
- **Gate CV Out** — auto-routed to target instrument's Gate input.
- **Note CV Out** — auto-routed to target instrument's CV input.
- **Mod Wheel CV Out**
- **Pitch Bend CV Out**
- **Aftertouch CV Out**
- **Expression CV Out**
- **Breath Controller CV Out**
- **Start of Arpeggio Trig Out** — gate signal at each pattern restart (great for re-triggering an envelope on another device).
- **Sustain Pedal Gate Out** — separate sustain output; **patching this disables the Hold function**.

### Combinator integration
- Place the RPG-8 inside a Combinator above an instrument; the Combi's Run button governs its playback.
- Use **Spider CV Merger/Splitter** to fan one RPG-8 out to multiple synths inside the Combi — but they all play the same monophonic line.
- For independent harmonised arpeggios, use multiple RPG-8s, one per voice, fed by note-doubled or transposed input via Note Echo / Scales & Chords Players.

### Rendering to MIDI
**Edit > Arpeggio Notes to Track** renders the live arpeggio output as note clips on the target instrument's track. After rendering:
- Mute the Arp track (otherwise you'll hear both).
- **Performance data (Pitch Bend, Mod Wheel) recorded on the Arp track is NOT rendered into the note clips** — re-record it on the target track if you need it.
- **CV-modulated parameters (Rate, Velocity, Octave Shift)** are also not captured by the render.

> **Quick recipe — Sustained-chord trance arp**
>
> 1. Create Combi → add Subtractor or Europa with a short-attack patch.
> 2. Add RPG-8 above the synth.
> 3. Mode **Up**, Octave **2 Oct**, Insert **Off**, Rate **Sync 1/16**, Gate Length around 60%.
> 4. **Hold = ON**.
> 5. Hold a 4-note chord; release to leave it running. Add DDL-1 with Sync 3/16 after the synth for the classic offset-delay shimmer.

> **Quick recipe — Monophonic bass with pattern gate**
>
> 1. RPG-8 above a Subtractor with Polyphony 1, fast envelope.
> 2. Mode **Manual**, Insert **Off**, Octave **1 Oct**, Single Note Repeat **ON**.
> 3. Set the 16-step Pattern editor to a syncopated rhythm (e.g. dark steps on 3, 7, 11, 15).
> 4. Play single bass notes — pattern controls the rhythm, you control the pitch.

### Pitfalls

> **Don't this**: Patch into Start of Arpeggio Trig In and forget about it. The arpeggio will go silent because the input is now "armed but never gated."
> **Do this**: leave it unpatched, or feed it a deliberate trigger (e.g. Matrix Gate or beat-clock).

> **Don't this**: Record into the Arp track expecting the actual arpeggiated notes to show up.
> **Do this**: Recording captures only the **input notes** (your held chord). To get the arpeggiated stream as MIDI, use **Arpeggio Notes to Track** afterwards.

- **Hold + recording = trouble**: with Hold on, releasing the keys doesn't stop the recorded take; the next recording pass is a wall of held notes. Disable Hold while tracking.
- **Single Note Repeat OFF + only one note held = no output**. By design, but easy to forget.
- **RPG-8 is monophonic**. Multiple lanes on its track merge into one mono stream — overlapping inputs don't yield polyphonic arpeggios. For poly arps, use multiple RPG-8s or render to track and edit.
- **Sustain Pedal Gate Out disconnects Hold** the moment a cable lands in it.
- **Pattern editor only steps the gate on/off**; it doesn't reorder notes. If you want melodic step variation, use Matrix instead.

---

## Combining the devices — common architectures

### Combi as a self-contained "performance instrument"
```
Combinator
├─ Combi Mixer (always)
├─ RPG-8           ← above synth, drives note/gate
├─ Subtractor      ← receives RPG-8 CV
├─ Pulsar          ← LFO modulating Subtractor filter
├─ Matrix          ← Curve CV → Subtractor amp level (rhythmic ducking)
└─ DDL-1 + RV7000  ← effects on the synth output
Combi Mixer "From Devices 1" ← DDL-1 out
External Out      ← Combi Mixer master
```
- Combinator Rotaries: Filter cutoff, Reverb wet, Arp rate, Matrix curve depth.
- Combinator Buttons: Hold on/off (RPG-8), Run (Matrix + RPG-8), Effect bypasses.
- Run button of Combi triggers Matrix and RPG-8 transport simultaneously.

### Mixer 14:2 vs Line Mixer 6:2 — which to choose
- **Inside a Combinator** with ≤6 sound sources and no need for EQ: Line Mixer 6:2.
- **Inside a Combinator** with EQ requirements or 4 separate FX buses: Mixer 14:2.
- **Standalone group bus**: Mixer 14:2 unless you really only have 6 sources.

### Matrix vs RPG-8 — which to choose
- Need **fixed-pitch step sequence** that doesn't follow incoming MIDI: **Matrix**.
- Need **arpeggiation of currently-held chord** (responds to MIDI input): **RPG-8**.
- Need **CV modulation** to other devices' parameters: **Matrix Curve** or **Pulsar**.
- Need **swing/groove on a per-pattern basis**: both have shuffle, but only Matrix exposes it as a pattern toggle.

### Pulsar vs Matrix Curve as modulator
- Want continuous, smoothly-shaped LFO with FM/AM cross-mod and audio-rate option: **Pulsar**.
- Want stepped, melodic, programmable, per-step modulation tightly locked to bars: **Matrix Curve**.
- Want both summing into one target: use a **Spider CV Merger** (utility device, not in this skill but present in Reason).

---

## Cheat sheet — defaults to remember

- **Combinator panel**: 4 rotaries, 4 buttons, 2 wheels, Run, Bypass FX. Max 32+32 + extras.
- **Combinator transpose**: ±36 semitones per device.
- **Matrix**: 4 banks × 8 patterns = 32 slots; 1–32 steps.
- **Mixer 14:2 EQ**: Treble 12 kHz, Bass 80 Hz, ±24 dB.
- **Pulsar Free Rate**: 0.06 Hz – 1.05 kHz. Sync: 32/4 – 1/64.
- **Pulsar Envelope**: Attack 0.1 ms – 3 s; Release 0 ms – 10 s.
- **RPG-8 Sync rates**: 1/2 to 1/128 incl. dotted/triplet. Free: 0.1–250 Hz.
- **RPG-8 Octave Shift**: ±3 octaves.
- **KBD Follow centre note (Pulsar)**: C3.
