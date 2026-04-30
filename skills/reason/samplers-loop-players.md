# Reason 13: Samplers & Loop Players
Based on Reason 13.4 documentation.

This document covers Reason's sampler family and the REX loop player. Pick the right device for the job — they overlap in places but each has a sweet spot.

## Comparison Table

| Device | Type | Best for | Sample format support | CPU/RAM |
|---|---|---|---|---|
| **Dr. Octo Rex** | REX loop player (slice-based) | Tempo-following drum loops, beat mangling, slice-level remixing | .rex, .rcy, .rx2 (REX2 stereo); patch = .drex | Low–medium. Polyphony ceiling doesn't reserve voices; HQ Interpolation increases load |
| **Grain** | Granular synthesizer + spectral engine | Atmospheric pads, drones, frozen textures, sound design from any source | .wav, .aif, .mp3, .aac, .m4a, .wma; SoundFont/REX as source samples | High. FFT (Spectral Grains) and many grains are CPU-intensive; high voice counts compound |
| **Mimic** | 8-slot creative sampler with auto-pitch / slice / stretch | Quick chops, drum-machine-style triggering, vocal chops, melodic samples | Standard audio + drag-and-drop sampling; slices stored in patch | Medium. Granular/Vocal stretch modes hit DSP harder than Tape |
| **NN-XT** | Multi-sample multi-zone sampler | Multisampled instruments, drum kits with per-sound output, velocity-layered libraries | .wav, .aif, .mp3, .aac, .m4a, .wma (+ .3g2/.3gp/.au/.sd2/.caf/etc. on macOS), SoundFont, REX; patch = .sxt | Medium. Scales with zone count, velocity layers, polyphony, HQ Interpolation |
| **NN-19** | Classic single-zone-per-key sampler | Lightweight multisamples, simple chromatic instruments, legacy patches | Same audio formats as NN-XT, SoundFont, REX; patch = .smp | Low. The original lightweight sampler |
| **Radical Piano** | Sample + physical-model hybrid (acoustic piano) | Realistic acoustic piano with resonance and pedal noise | Built-in piano models only (Bechstein/Steinway/Futura) | Medium–high. Sympathetic resonance + multiple mic blends raise CPU |

**Quick decision tree:**
- Need a tempo-locked drum loop with per-slice control → **Dr. Octo Rex**
- Need a granular pad / spectral texture → **Grain**
- Want fast chops / 8-pad style triggering → **Mimic**
- Building a serious multisampled instrument or drum kit → **NN-XT**
- Loading a legacy patch or want a simple chromatic sampler → **NN-19**
- Need an acoustic piano → **Radical Piano**

**Cross-references:**
- NN-XT vs NN-19: NN-XT supports overlapping zones, velocity layers, crossfades, groups, alt switching, and 8 stereo outs. NN-19 is one zone per key, no velocity layering. Use NN-XT for anything beyond the most basic multisample.
- Grain vs Mimic: Grain is a granular synth disguised as a sampler; Mimic is a sampler with a granular *stretch* mode. For frozen textures and spectral work go Grain. For chop-and-trigger go Mimic.
- Dr. Octo Rex vs NN-XT (with REX): Dr. Octo Rex *plays* the loop and follows tempo. NN-XT loads REX slices as a chromatic key map (no automatic tempo follow). To recreate the original loop in NN-XT you must use Dr. Octo Rex's "Copy Loop To Track" then move the MIDI to the NN-XT track.

---

## Dr. Octo Rex Loop Player

### Role
A REX loop player that holds **eight loops** in slot-based pattern memories. Loops are pre-sliced (each slice = a transient event) and slices are mapped chromatically starting at C1, so the loop plays back at any tempo without pitch shift or time-stretch artifacts.

### Architecture
- **8 slots**, each holds one REX file (.rex / .rcy / .rx2). The patch (.drex) stores only references — the REX files must remain on disk.
- **Slices** trigger as MIDI notes from C1 upward. Each slice has independent pitch / pan / level / decay / reverse / filter freq offset / alt group / output routing.
- **Synth section** (filter, envelopes, LFO, pitch, master volume) sits on top of the slice playback — all global across loops, except per-slot Loop Level and Loop Transpose.
- Backward-compatible with Dr. Rex (legacy patches auto-convert; legacy automation maps to new equivalents; advanced new features stay dormant).

### Loop Slots & Switching
- **Enable Loop Playback** → pressing Run / Play plays the active slot.
- **Loop Slot button click**: immediate switch.
- **Trig Next Loop** parameter: quantizes the switch to Bar / Beat / 1/16.
- **Pattern Automation**: per-beat switching that bypasses Trig Next Loop quantization — use this for fast slot stutters.
- **MIDI control**: E0–B0 selects slots 1–8. D#0 stops. D0 single-shot triggers the loop pointed at by **Note To Slot**.

### Note To Slot (the secret weapon)
The **Note To Slot** knob picks which slot receives sequencer / keyboard MIDI input — separate from the Loop Slot button (which is only for Run-based playback). **Automatable per-note** in the sequencer: set slice 1 to play from slot 1, slice 2 from slot 2, etc., for cross-loop remixes at slice resolution.

### Per-slice parameters (in waveform display)
| Parameter | What it does |
|---|---|
| Pitch | ±8+ octaves transpose |
| Pan | Per-slice stereo position |
| Level | Per-slice volume (default 100) |
| Decay | Truncates / shortens slice |
| Rev | Reverse playback toggle |
| F.Freq | Cutoff offset relative to global filter |
| Alt | Alt group 1–4 (random selection within group) |
| Output | Routes slice to output pair 1-2/3-4/5-6/7-8 |

**Slice Edit Mode** = pick one parameter, draw across the waveform display to set values for all slices at once. Ctrl/Cmd-click resets a slice to default.

### Alt groups
Assign multiple slices to Alt 1 → only one randomly fires per group trigger. Stack alts on snares (Alt 1) and hats (Alt 2) for evolving "live drummer" variation. Works during Run playback and Pattern Automation switching.

### Synth section essentials
- **Filter**: Notch / HP12 / BP12 / LP12 / LP24, with on/off bypass.
- **Filter Envelope** (ADSR + Amount): Routes to filter freq and/or pitch.
- **Amp Envelope** (ADSR): Per-slice volume shape.
- **LFO**: Tri / Inv-Saw / Saw / Sq / Random / Soft Random → Osc / Filter / Pan, with optional tempo sync (16 divisions).
- **Pitch**: Env A amount, Octave (0–8, default 4), Fine (±50¢).
- **Mod wheel** routes to filter freq / resonance / filter env decay.
- **Pitch bend range**: up to ±24 semitones.
- **Velocity** can scale filter env amount, filter env decay, and amplitude. REX files have no native velocity — Copy Loop To Track defaults to vel 64.
- **Global Transpose** ±12 semis. Real-time control via MIDI notes C-2 to C0; C-1 resets.

### Copy Loop To Track
Generates MIDI notes (one per slice, starting at C1) at the original slice timings, with Note To Slot automation pointing at the source slot. This is how you take a slot loop and turn it into editable MIDI for grooving / quantizing / scrambling / Alter Notes / User Groove extraction.

Caveat: if locators span multiple loop cycles, clips repeat. If a loop runs past the right locator the final clip "sticks out" — mask it manually.

### Outputs and CV
- Eight stereo output pairs. Pan slices hard L/R within a pair to get effectively 16 mono outs.
- CV inputs (with trim): Master Volume, Mod Wheel, Pitch Wheel, Filter Cutoff, Filter Resonance, Osc Pitch.
- Mod outputs: Filter Envelope (voice 1 only), LFO.
- Gate inputs: Amp Env Gate, Filter Env Gate (override MIDI when patched).
- Gate output: per-slice gate.

### Audio quality toggles
- **High Quality Interpolation**: Better high-freq clarity, more CPU. Disable if inaudible in mix.
- **Low Bandwidth**: Removes highs to save CPU; often inaudible in filtered/compressed material.

### Polyphony note
The poly setting is a *ceiling*, not a reservation. Only sounding voices use CPU. Three to four voices is enough for most loop playback; raise it for overlapping decays or live MIDI slice work.

### Quick recipe — slice a drum break to fit a session
1. Drop the .rx2 onto an empty Dr. Octo Rex slot.
2. Press Enable Loop Playback. The session tempo now controls loop speed without pitch change.
3. To get editable MIDI: Copy Loop To Track → edit notes for groove / scramble / quantize.
4. For variation without editing: assign snares to Alt 1 and hats to Alt 2, with multiple sample slices per alt.
5. To remix across loops: load 2–8 loops in the slots, then automate **Note To Slot** per-note in the generated MIDI.

### Quick recipe — beat mangling with cross-loop slicing
1. Load four related breaks into slots 1–4.
2. Copy Loop To Track from slot 1.
3. In the generated clip, automate Note To Slot per slice — slice 2 → slot 3, slice 5 → slot 2, etc.
4. Each slice now plays from a different source loop while keeping the slot-1 timing.

### Pitfalls
- **Custom slice settings are wiped when you load a new REX into the slot.** No undo.
- **Note To Slot redirected to a different-shape loop sounds chaotic by default** — that's because slice counts and content differ. Sometimes a feature, often a footgun.
- **Polyphony myth**: people set it low to "save CPU" — the ceiling alone uses no CPU.
- **Filter knob seems dead?** The Filter Envelope is probably modulating it. Lower freq + raise resonance + raise env amount together to hear the sweep.
- **Legacy Dr. Rex conversion** keeps the song sounding the same but doesn't unlock 8-slot features automatically.
- **REX file dependency**: .drex patches reference REX files by path. Ship the REX library with the patch or it loads silently empty.

---

## Grain Sample Manipulator

### Role
An advanced sampler **and** granular/spectral synthesizer. Grain extracts small audio segments (grains) from a sample and reassembles them with controllable timing, density, pitch, panning, and crossfading. There's also a supplementary classic oscillator and an extensive modulation matrix.

### Playback algorithms (the heart of the device)
| Algorithm | What it does | Use it for |
|---|---|---|
| **Spectral Grains** | FFT analysis of the sample. Snap pitch-shifts inharmonic partials toward harmonic; Filter strips inharmonic content; you can *draw* a custom formant curve. | Turning noisy / inharmonic material into pitched textures. Spectral morphing. |
| **Grain Oscillator** | Plays two very short grains at the rate of the played note. Grain Length, Spacing (high spacing → wavetable-like), Pan Spread, Pitch Jitter, Formant. | Wavetable-style synthesis from sampled material. Oscillator-sync sounds at high spacing. |
| **Long Grains** | Extended grain segments where Root Key affects output pitch. Length, Rate, X-Fade (0% gritty → 100% smooth), Pan Spread, Pitch Jitter. | Slowed-down evolving pads, time-stretched textures. |
| **Tape** | Speed and pitch are linked, like analog tape. Speed 0% = silence (or scrub). Loop X-Fade for clean loops. | Tape stops, scrubbing, freeze-with-pitch effects. |

### Motion modes (how the playhead moves)
- **Freeze** — plays at Sample Start position only; no Sample End marker.
- **One Shot** — start to end once per key.
- **FW Loop** — forward loop between markers.
- **FW-BW Loop** — back-and-forth between markers.
- **End Freeze** — play through, then hold at Sample End.
- **Envelope 1** — playhead position follows Envelope 1's curve. Activate Beat Sync for tempo-locked playback.

### Sample-level controls
- **Speed**: Playhead velocity through the sample. In Tape mode this also sets pitch. 0% = stop.
- **Jitter**: Random micro-position modulation → chorus-like motion / liveness.
- **Global Position**: New voices begin at the *current* blue Position marker, not at Sample Start. Enables vocoder-like and rhythmic results.
- **Root Key**: Auto-detected at Sample Start. Manual Octave / Semi / Tune (±50¢) and a keyboard-tracking parameter.

### Oscillator section (supplementary)
Selectable waveforms (Sine, Triangle, Saw, Square/Pulse, Noise, Band Noise) with a Mod parameter that morphs character (e.g. sine → saw, square → PWM → silence). Tracks keyboard 100% — pairs with the sample for hybrid timbres or as a pitch reference.

### Filter
- HP 12dB, BP 12dB, LP 12dB, LP Ladder 24dB.
- Frequency, Resonance, Envelope 2 (hardwired with velocity), Keyboard Tracking 0–100%.
- Sample and oscillator have independent filter routing buttons.

### Amplitude envelope
ADSR + Gain + Velocity → Gain + Pan. Standard, but Pan is per-voice.

### Modulation system (this is where Grain lives or dies)
- **4 polyphonic envelopes** with preset curves (ADSR, ramp, exp, etc.) and *custom drawing* (click / Ctrl-click adds points; drag segments). Each has a sustain marker, optional Loop Mode (turns it into an LFO with Beat Sync / Key Trigger / Global modes).
  - **Env 1 → hardwired to Motion** (sample playback position).
  - **Env 2 → hardwired to filter frequency**.
- **3 LFOs**: Sine, triangle, pulse, random, slope, stepped. Rate (Hz or tempo-synced), Beat Sync, Key Sync, Global Mode, Delay.
- **8-lane modulation bus**: each lane = source → 2 destinations with independent amounts and a Scale source for secondary control. Sources include velocity, all envelopes, all LFOs, env multiplications (Env3×Env4, Env3×LFO3), Mod / Pitch / Breath / Expression / Aftertouch / Sustain wheel & pedal, key tracking, random, key-in-octave, white noise, voice count, last velocity, sample pitch curve, mouse X / mouse gate in display, CV inputs 1–4 (immediate or latched). Destinations span basically every audible parameter, plus envelope times, LFO rates, portamento, effects, CV outs, Note Trig.

### Effects (6 reorderable, draggable to reorder chain)
1. **Phaser/Flanger/Chorus** — type, depth, rate, spread, amount.
2. **Distortion** — Dist / Scream / Tube / Sine / S/H (bit-crush) / Ring; drive, tone, amount.
3. **Parametric EQ** — single band, ±18 dB, Q.
4. **Delay** (send) — sync, time, ping pong, pan, feedback, amount.
5. **Compressor** — attack, release, threshold, ratio.
6. **Reverb** (send) — decay, size, damp, amount.

### Performance
- **Key modes**: Poly (up to 12 voices), Retrig (mono with envelope/playback restart), Legato (mono, preserves env/playback during legato).
- **Portamento**: Auto (legato only; no effect in Poly), Retrig, Legato.
- **Pitch bend**: ±1 to ±24 semis. Note: in Spectral Grains with Snap/Filter at 0, pitch wheel does nothing audible unless Formant is mapped as a mod destination.
- **Voices**: 1–12. Tip — for monophonic, prefer Retrig/Legato over Voices=1.

### Patch caveat
Patches store device settings and modulation routings but **not the sample** — sample must live on disk / in a ReFill / be self-contained with the song. CV connections only persist when the device is inside a Combinator.

### Quick recipe — granular pad from a vocal
1. Drop the vocal sample in. Choose **Long Grains**, motion mode **FW Loop**.
2. Set Grain Length around 50%, X-Fade ~80% for smoothness, Pan Spread ~50%.
3. Speed → 0% (frozen). Move the Position marker manually to a vowel.
4. Modulation bus: LFO 1 → Position (small amount, slow rate) for drift.
5. Add some Pitch Jitter for liveness, then a touch of reverb.

### Quick recipe — frozen spectral texture
1. Algorithm **Spectral Grains**, motion **Freeze**.
2. Crank Snap to ~70% to harmonize inharmonic partials.
3. Use the Curve Tool to draw a formant emphasizing 1–3 kHz.
4. Modulation: LFO 2 → Curve Amount, slow rate, beat-synced.
5. Long release on the amp envelope. Hold a chord — it's a drone now.

### Quick recipe — wavetable-style synth from any sample
1. Algorithm **Grain Oscillator**, motion any.
2. Set Grain Spacing high (the timbre stops tracking source position and starts behaving like a wavetable).
3. Mod wheel → Position (in the mod bus) lets you sweep through "wavetables" (positions in the sample).
4. Add a touch of Pitch Jitter and Pan Spread for animation.

### Quick recipe — tape-stop FX
1. Algorithm **Tape**, motion **End Freeze**.
2. Modulation: envelope or mod wheel → Speed, ramp from 100% → 0%.
3. Hold a note → it slows to a halt at the end of the sample, frozen there.

### Pitfalls
- **CPU**: Spectral Grains with high FFT size + many voices is the most expensive combo. Cut polyphony before raising FFT.
- **Patches don't carry samples** — moving songs/patches needs the audio bundled or accessible.
- **Pitch wheel silent in Spectral Grains?** Snap/Filter at 0 disables audible pitch behavior. Map Formant as a mod destination, or raise Snap.
- **Env 1 and Env 2 are hardwired** — Env 1 to motion, Env 2 to filter. Don't expect them to be free.
- **Global Position + Freeze** is amazing, but new voices will pile up at the same position — manage polyphony or you get phasing.

---

## Mimic Creative Sampler

### Role
A streamlined "creative sampler" with **8 sample slots**, four playback modes, automatic pitch detection, automatic transient slicing, and five stretch algorithms. Built for fast chopping, slot triggering, and quick sample-flips rather than deep multisample work (use NN-XT for that).

### Playback modes (per device)
1. **Pitch** — single slot played melodically across the keyboard.
2. **Slice** — triggers individual slices of a slot from the keyboard, no pitch shift.
3. **Multi Slot** — drum-machine-style; each slot mapped to a key for triggering.
4. **Multi Pitch** — up to 8 slots layered with custom keyboard ranges (multisample-lite).

Note: pitch detection runs in **Pitch and Multi Pitch** only.

### Sample editing
- **Start / End markers**: drag, double-click to set; Option/Alt-click previews.
- **Loop**: forward loop at sample end (red transparent region). Adjust length via knob or Cmd/Ctrl-drag.
- **Speed**: 0% (stop) up to standard rate, modulatable.
- **Slices**:
  - Auto-generated by transient detection (yellow markers).
  - Sensitivity adjustable.
  - Max 92 slices.
  - Double-click slice lane to add a manual marker (different color); double-click a marker to delete.
  - **Reset** restores auto slices, removing manual ones.
  - **Play Thru** toggles continuous playback past a slice boundary while sustained.

### Stretch algorithms
| Algorithm | Use for |
|---|---|
| **Tape** | Coupled speed/pitch; classic tape behavior. Cheapest. |
| **Advanced** | High-quality polytrend with transient preservation. General-purpose. |
| **Melody** | Optimized for monophonic melodic sources. |
| **Vocal** | Includes formant shifting + fixed-pitch auto-tune behavior. |
| **Granular** | Grain-based, with length / overlap / jitter / stereo spread. |

### Synthesis per slot
- **Pitch**: ±24 semis + cents. LFO and velocity modulation.
- **Filter**: 8 types — LP24, LP12, HP24, HP12, BP, Notch, two Comb variants. Frequency 37 Hz → 16 kHz, resonance, drive, kbd tracking, velocity, envelope mod.
- **Envelopes**: ADSR for filter cutoff and amp gain (independent).
- **LFO**: sine / triangle / pulse / random / slope / stepped; rate, key sync, beat sync, delay; LFO Scale (introduce mod via mod wheel).

### Effects / shaping
- **Compressor** (Squeeze knob) with LED metering.
- **Effect Section**: 7 algorithms — Noise, Resonant Noise, Ring Mod, Bitrate, Lowres (combined), sine fold distortion, Scream distortion. Character + wet/dry.
- **EQ**: Lo Cut (20 Hz–4 kHz), Hi Cut (200 Hz–20 kHz).

### Performance
- Portamento + Poly / Mono Retrig / Mono Legato.
- Pitch bend ±24.
- Velocity scaling on gain, filter, amp.
- Per-voice pan with mod source assignment.

### Routing
- Individual slot outputs (discrete processing).
- FX Send outputs route to external effects via separate mixer channels.
- Master outs auto-route on creation.

### Patch caveat
Patch references samples — samples must be on disk or in a ReFill (or self-contained with the song).

### Quick recipe — chop a vocal hook
1. Drag the vocal into slot 1, set mode **Slice**.
2. Adjust slice sensitivity until each phrase / syllable has its own marker.
3. Manually double-click to add markers where the auto detector missed.
4. Play your MIDI keyboard — each note triggers a slice in order.
5. Drop in some Bitrate and a touch of Vocal stretch for character.

### Quick recipe — drum-machine kit (Multi Slot)
1. Set device mode **Multi Slot**.
2. Drag a kick to slot 1, snare to slot 2, hat to slot 3, etc.
3. Each slot maps to a MIDI key; play / sequence as a drum kit.
4. Tighten each slot's amp envelope (fast attack, short decay) and use Filter + Squeeze per slot for the hit shape.

### Quick recipe — pitched melodic sample (Pitch mode)
1. Mode **Pitch**, drag in a one-shot synth note.
2. Mimic auto-detects root key. If wrong, set Root + Tune.
3. Choose **Melody** stretch algorithm (or **Vocal** for formant control).
4. Play it across the keyboard — Mimic stretches without pitch coupling.

### Quick recipe — sample tail extension
- Speed mod via filter envelope decay → speed slows toward zero across the decay → effective tail extension without looping.

### Pitfalls
- **Patch ≠ sample**: same as Grain / NN-XT. The audio must be accessible.
- **Granular and Vocal stretch are CPU-heavy**. Drop to Tape or Advanced when Mimic isn't doing anything dramatic.
- **Pitch detection only in Pitch / Multi Pitch modes** — don't expect auto-tuning in Slice or Multi Slot.
- **Max 92 slices** — long busy material may need re-chopping into multiple slots.
- **Avoid playing very low-pitched samples way up the keyboard** — high-pitch playback raises DSP load.

---

## NN-XT Sampler

### Role
The "professional" multi-zone sampler. Use it any time you need:
- Multisamples (multiple takes of the same instrument across the keyboard).
- Velocity layers / crossfades.
- Drum kits with per-sample output routing.
- Group-level performance settings (mono, legato, alt switching).
- Loading SoundFonts or REX content as a chromatic key map.

### Architecture
- **Samples** load into **Zones**. A zone is a container with its own key range, velocity range, root note, tuning, sample start/end, loop mode, level, pan, and output routing.
- New zones default to C1–C6 and become the edit focus.
- Zones live inside **Groups**, which carry shared settings: Key Poly, Group Mono, Legato/Retrig, Portamento, LFO 1 Rate (when in Group Rate mode).

### Key map management
- **Boundary handles** in the key map / tab bar resize zones (multi-select sets all to focus zone's range).
- **Lo Key / Hi Key knobs** for precise numerical ranges.
- **Automap Zones** — arranges by root key with split points midway between adjacent samples.
- **Automap Zones Chromatically** — single semitone per zone (drum kits, REX slices).
- **Sort by Note / Velocity** for clean lists.

### Velocity architecture
- Each zone has a 1–127 velocity range.
- Full-range zones are outlined; partial-range zones show a striped pattern.
- **Overlapping ranges** = layered playback (e.g., piano + strings on the same notes).
- **Non-overlapping ranges** = velocity switching (only one zone per velocity band).
- **Fade Out / Fade In** parameters create velocity crossfades for smooth transitions between layers.
- **Create Velocity Crossfades** auto-calculates fade values across overlapping zones.

### Layer management
- Stack zones with overlapping key ranges → simultaneous layered playback.
- **Groups** let you select related zones for collective edits and shared performance behavior.
- **Alternate function**: semi-random pick between overlapping zones each trigger — perfect for round-robin drums or string articulations.

### Sample parameter editing (focused zone)
- **Root note + Tune** (±50¢).
- **Sample Start / End** offsets.
- **Loop modes**: FW (no loop), FW-LOOP, FW-BW, FW-SUS (loop only while held), BW.
- **Output routing** to any of 8 stereo pairs.

### Synth section (right side of Remote Editor)
- **Filter**: Notch, HP12, BP12, LP6 (no resonance), LP12, LP24. Frequency, resonance, kbd tracking.
- **Modulation Envelope**: Attack, Hold, Decay, Sustain, Release, Delay, Key→Decay. Routed to pitch and/or filter.
- **Amplitude Envelope**: Same shape parameters + Level + Spread/Pan (Key / Key 2 / Jump modes) + per-zone Pan.
- **LFO 1**: Tri / Inv-Saw / Saw / Sq / Random / Soft Random; Group Rate / Tempo Sync / Free Run; optional key sync; targets pitch / filter / level.
- **LFO 2**: Triangle only, always key-synced; targets pan / pitch.

### Performance / global controls
- **Key Poly** (1–99). Set 1 for monophonic.
- **Group Mono** — only one zone per group sounds at once (closed/open hat pairs etc.).
- **Legato Mode** — no envelope retriggering on legato passages.
- **Retrig** — standard polyphonic retrigger.
- **Portamento** — glide time during legato.
- **Pitch Bend Range** ±24 semis.
- Front panel global bipolar knobs: Filter Freq/Res, Amp Attack/Decay/Release, Mod Env Decay, Master Volume.
- **High Quality Interpolation** toggle.

### Modulation sources
- **Mod Wheel (W)** and **External Control (X)** (aftertouch / expression / breath) routed to filter freq, mod env decay, filter res, level, LFO 1 rate/amount.
- **Velocity** routed to filter freq, filter env decay, amp, attack time, sample start position. Bipolar (positive = harder = more; negative = inverted).

### Selection vs edit focus
- *Selection* = one or many zones (collective parameter changes).
- *Edit focus* = the single zone whose values appear on the panel.
- **"M" symbol** appears on a parameter when selected zones disagree on its value — flags conflicts so you can edit them down.
- **Solo Sample** plays the focused sample across the entire keyboard ignoring velocity ranges — handy for testing transposition range.

### Format support
- **Patches**: .sxt (samples + zone map + parameters).
- **Audio**: .wav, .aif, .mp3, .aac, .m4a, .wma (Windows). macOS adds .3g2, .3gp, .mp1, .mp2, .mpeg, .mpa, .snd, .au, .sd2, .ac3, .adts, .amr, .caf, .m4r, .mp4.
- **SoundFonts**: full presets load and map automatically.
- **REX**: each slice gets a chromatic key starting at C1 with default settings.

### Output routing
8 stereo output pairs (16 individual channels). Pair 1 auto-routes to mixer; others are manual. Pan a mono sample hard L or R within a pair to use a stereo pair as 2 mono outs.

### Quick recipe — build a multisample piano in NN-XT
1. Drag all sample files onto the device. They land as zones spanning C1–C6.
2. Select all → **Set Root Notes from Pitch Detection**.
3. Select all → **Automap Zones**. Done — root notes centered, splits between samples.
4. If you have soft / medium / hard takes per note: assign each to a velocity range. Then **Create Velocity Crossfades** for smooth transitions.

### Quick recipe — build a drum kit (with per-pad outputs)
1. Drop each drum sample in.
2. **Sort by note**, then **Automap Zones Chromatically** so each sample gets one semitone.
3. For each zone, set the **Output** to a different pair (1, 2, 3, …).
4. On the rack rear, route each pair to a separate mixer channel for individual EQ / comp / send treatment.
5. For round-robin variants: put 4 snare takes on the same key, group them, enable **Alternate**.

### Quick recipe — round-robin layered strings
1. Load 3 string articulations.
2. Stack them on overlapping key ranges (zones overlap = simultaneous play).
3. Group them, enable **Alternate** for variation each trigger.
4. Optionally split velocities + Fade In/Out for soft → loud crossfade.

### Quick recipe — REX file as melodic instrument
1. Load .rx2 as a *patch* into NN-XT.
2. Slices auto-map chromatically from C1 up.
3. Now play melodies on the slices, or select all and tweak amp envelope / filter to taste.

### Pitfalls
- **CPU/RAM scaling**: serious multisample libraries can fill RAM fast. Trim sample lengths and turn off HQ Interpolation when inaudible.
- **Velocity layer crossfades** can cause amplitude bumps if Fade In/Fade Out aren't symmetric — use **Create Velocity Crossfades** to auto-balance.
- **Key-mapping mistakes**: forgetting to set root notes (or trusting wrong embedded metadata) makes Automap useless. Run **Set Root Notes from Pitch Detection** when in doubt.
- **Patches don't bundle samples** by default — store self-contained or keep the audio in the project's folder structure.
- **Output pair 1 is the only auto-routed pair** — multi-out drum kits won't be heard until you wire the rest.
- **"M" on a knob** isn't a bug — it means selected zones disagree on that parameter.

---

## NN-19 Sampler

### Role
The classic, lightweight sampler. **One sample per zone, one zone per key range, no velocity layering.** Use it for: legacy patches, quick single-sample chromatic instruments, low-CPU multisamples, or simple drum triggering. For anything with velocity layers, alt switching, or per-zone outputs, reach for NN-XT instead.

### Architecture
- A **key zone** is a keyboard range playing one sample.
- A **key map** is the collection of zones across the keyboard. Zones cannot overlap.
- Only one zone selected at a time (light-blue highlight).
- The inverted note on the keyboard display = the **root key**. It can sit outside the zone if you really want.

### Zone management
- Split a zone in half via Edit / context menu.
- Alt/Option-click above the keyboard display to create a new empty zone.
- Drag handles or use **Low Key / High Key** knobs.
- **Select Key Zone via MIDI** — playing a key selects its zone.
- **Solo Sample** plays the selected zone across the whole keyboard (when "Select via MIDI" is off) — for verifying root key and acceptable transposition range.

### Sample assignment
- Click **Browse Sample**, pick a file, Load. Empty zone gets the sample full keyboard.
- Existing zone? Sample is replaced (unless used elsewhere).
- Loading multiple at once: one goes to the selected zone, the rest stay unassigned in memory.
- **Sample knob** dials between samples in memory for the selected zone (without re-browsing).
- **Level** knob per zone (compensates between multisample takes).
- **Tune** knob per sample (±0.5 semis / ±50¢) for inter-sample pitch correction.
- **Automap Samples** — arranges all loaded samples by root key (read from file metadata), centering each in its zone.
- **Delete Unused Samples** purges anything in memory not assigned to a zone.

### Looping
- NN-19 *cannot create* loop points. Set them externally (in the Edit Sample window or another editor).
- Modes: OFF / FWD / FWD-BW.

### Synth section
Samples act as oscillators. Pitch controls work *globally* across all zones; for per-sample tuning use the keyboard-display Tune knob.

- **Sample Start** offset (with optional velocity → start position).
- **Pitch**: Octave (0–8, default 4), Semitone (12), Fine (±50¢).
- **Keyboard Tracking** toggle — turn off for non-pitched material like drums.
- **Osc Envelope Amount** — Filter Envelope to pitch.
- **Filter**: LP24 / LP12 / BP12 / HP12 / Notch + freq + resonance.
- **Filter Envelope**: ADSR + Amount + Invert toggle.
- **Amplitude Envelope**: ADSR + Level master.
- **LFO**: Tri / Saw / Inv-Saw / Sq / Random / Soft Random → Osc / Filter / Pan, with optional tempo sync (16 divisions).

### Performance
- **Velocity** → Amp / Filter Env Amount / Filter Env Decay / Sample Start / Amp Attack. Bipolar.
- **Pitch Bend Range** up to ±24 semis.
- **Mod Wheel** simultaneously routes to Filter Freq / Res / Decay / LFO Amount / Amp Level (each bipolar).
- **Performance modes**:
  - *Legato* — best at polyphony 1 (or activates when all voices are full).
  - *Retrig* — standard polyphonic.
  - *Portamento* — glide time between notes.
  - *Polyphony* 1–99 (ceiling, not reservation).
  - *Voice Spread*: Key / Key 2 / Jump.
- **Low Bandwidth** to save CPU when high-freq detail is inaudible.

### External controllers
Source-selectable: Aftertouch / Expression / Breath → Filter Freq / LFO Amount / Amp Level (bipolar).

### Loading workflows
- **Patches** (.smp): Browse Patch → loads samples + key map + synth settings as one bundle. Init Patch resets.
- **REX as a patch**: each slice mapped chromatically from C1, default settings. To recreate the loop, load the same REX into Dr. Octo Rex, Copy Loop To Track, then move the MIDI to the NN-19 track and delete Dr. Octo Rex.
- **REX individual slices**: Browse Sample → open the .rx2 like a folder → pick slices.
- **SoundFonts**: Browse Sample → pick the .sf2 → open the Samples folder → pick a sample (NN-19 loads individual samples, not whole presets).

### Back panel
- L / R audio outs (auto-routed).
- CV / Gate inputs (mono control, e.g. from Matrix).
- Mod CV inputs (with trims): Osc Pitch / Filter Cutoff / Filter Res / Amp Level / Mod Wheel.
- Mod outs: Filter Envelope, LFO.
- Gate inputs: override normal MIDI triggering.
- **CV connections do not save in .smp patches**.

### Quick recipe — build a quick chromatic instrument
1. Browse Sample → load all samples at once.
2. **Automap Samples** — they spread across the keyboard centered on root keys.
3. Tune individual samples with the Tune knob if needed.
4. Save as .smp patch.

### Quick recipe — drums in NN-19 (lightweight)
1. Disable **Keyboard Tracking** (samples won't transpose).
2. Create empty zones via Alt/Option-click for each drum.
3. Load one sample per zone (Browse Sample with that zone selected).
4. Set Polyphony low if you want choke behavior.
5. (For velocity layers / per-pad outputs / round-robin → use NN-XT instead.)

### Quick recipe — REX loop in NN-19 + Dr. Octo Rex assist
1. Load .rx2 patch into NN-19. Slices map chromatically from C1.
2. Add a temporary Dr. Octo Rex with the same .rx2.
3. **Copy Loop To Track** in Dr. Octo Rex → drag the resulting MIDI clip to the NN-19 track.
4. Delete Dr. Octo Rex. NN-19 now plays the loop with NN-19 character.

### Pitfalls
- **No velocity layers, no overlapping zones** — for round-robin / vel layering, switch to NN-XT.
- **No internal sample loop editor** — set loop points externally first.
- **CV connections aren't saved in .smp patches** — re-patch on recall.
- **Filter knob seems dead** = the filter envelope is doing the moving. Same trap as in Dr. Octo Rex / NN-XT.
- **Polyphony myth** — same as elsewhere; the ceiling is free.

---

## Radical Piano

### Role
A hybrid acoustic piano instrument combining sample playback with physical modeling. Three sampled instruments, multiple mic configurations, blendable timbres, sympathetic resonance, key/pedal mechanics — designed for realism without the disk footprint of a giant multisample library.

### Piano models
1. **Home Grand** — Bechstein grand, intentionally "not perfectly tuned" home character.
2. **Deluxe Grand** — Steinway Model D from Sveriges Radio, premium concert grand.
3. **Upright** — Futura upright, living-room aesthetic.

### Microphone configurations
Up to 9 microphones were used in recording; 5 selectable configurations:
- **Vintage Mono** — single mic from outside (ribbon for Steinway, tube for Futura).
- **Ambience** — 2 mics in AB stereo, distant room reflections.
- **Floor** — pressure zone mics behind front legs, depth and richness.
- **Jazz** — 2 mics AB just outside / in front; full body, wide stereo.
- **Close** — 2 mics XY near hammers; sharp attack, ideal for uptempo pop/rock.

### Blending
Two simultaneous sound sets — same piano with different mics, or *different* pianos — controlled by the **Blend** knob. Mix a Steinway Close with a Bechstein Ambience for hybrid character.

### Character control
**Character** knob, 24 steps, Subdued ↔ Agitated (12 o'clock = natural). Subdued = warmth, Agitated = brightness/pronounced attack. **Heads-up: changing Character temporarily mutes audio outputs.** Don't ride the knob during a take.

### Velocity response
Not fixed velocity layers — seamless ranges:
- **High knob** — timbre at maximum velocity (can extend beyond acoustic piano range).
- **Low knob** — timbre at minimum velocity (zero = silence at softest playing).
- **Curve knob** — exponential / linear / logarithmic curve shape.

### Tuning
- **Cent**: master tuning ±1 semitone.
- **Drift**: slow irregular pitch wandering for atmospheric / lo-fi vibes.

### Sustain & sympathetic resonance
- **Sustain**: continuous control, not just on/off — pedal up through pedal down. Receives standard sustain pedal as binary; edit to continuous 0–127 in the sequencer for half-pedaling.
- **Sympathetic Resonance**: undamped strings vibrating in response to played notes. **Level** = overall amount; **Release Time** = fade to silence.

### Envelope
- **Attack**: 0–200 ms (from natural to unnaturally slow).
- **Decay Curve**: exponential = minimal body sustain; logarithmic = extended sustain.
- **Release**: simulates damper behavior; longer = worn dampers.

### Mechanics
- **Key Down** noise level (12 o'clock = natural).
- **Key Up** noise (hammer/damper return).
- **Pedal** mechanical noise.

### Effects (built-in)
- **3-band EQ** (±18 dB per band, tuned for piano).
- **Ambience** reverb: Small Room / Large Room / Hall / Theater.
- **Compression** for output dynamics.
- **Stereo Width** (no effect on Vintage Mono).

### External audio input
Route external audio through Radical Piano's Resonance, EQ, Ambience, and Compression. Run a vocal through the resonance with the sustain pedal down for a strings-against-the-soundboard effect.

### CV and MIDI
- CV inputs: pitch (±1 octave), master volume.
- Pitch Bend: ±7 semis (can be reduced by Character settings or Pitch CV).
- Sustain pedal: standard switch type, but the sequencer can hold continuous 0–127 values.

### Patch caveat
**CV connections are not stored in the patch.** Re-patch on recall.

### Quick recipe — convincing solo piano sound
1. Pick **Deluxe Grand**.
2. Mic config **Jazz** (or **Close** for upbeat pop), Blend ~30% with **Ambience** for room.
3. Character at 12 o'clock, Curve linear, Low ~10 (so soft playing is soft, not silent).
4. Sympathetic Resonance Level around 40–60%.
5. Ambience: Hall, modest amount; tame highs with the EQ if mics are bright.

### Quick recipe — lo-fi upright vibe
1. **Upright**, mic **Vintage Mono**.
2. **Drift** mid-high.
3. Character toward Subdued.
4. Compression up, slight EQ scoop.
5. Ambience: Small Room, wet.

### Quick recipe — mangle a vocal through piano resonance
1. Plug a vocal channel into the Radical Piano audio input.
2. Hold the sustain pedal down (so all dampers lift).
3. Play held chords on the keys — sympathetic resonance excites the modeled strings against the vocal.
4. Mix in dry vocal and the resonance-only output.

### Pitfalls
- **Character changes mute audio temporarily** — never automate it through a held note.
- **CV doesn't persist** — re-route on patch recall.
- **Stereo Width does nothing on Vintage Mono** — that's expected.
- **Pitch Bend is fixed at ±7** (not ±24 like the samplers).
- **CPU**: blending two mic sets with sympathetic resonance + reverb can climb. If running multiple instances, drop one mic set or freeze tracks.

---

## Cross-cutting tips & traps

These show up across multiple devices and are worth internalizing:

1. **Filter knob "doesn't move the sound"** — usually because the Filter Envelope is modulating cutoff. Lower the freq, raise resonance, raise env amount, or zero the env amount to verify. Applies to Dr. Octo Rex, NN-XT, NN-19, Grain, Mimic.

2. **Polyphony is a ceiling, not a reservation.** Setting it to 32 doesn't burn CPU — only sounding voices do. Don't artificially lower it "for performance."

3. **Patches don't bundle samples.** Dr. Octo Rex (.drex), NN-XT (.sxt), NN-19 (.smp), Grain, Mimic — every one of them stores a *reference* to the sample, not the audio. Self-contain the song or ship the audio with the patch.

4. **CV connections often don't survive patch recall.** Especially in NN-19 and Radical Piano. If you rely on CV routing, save the device inside a Combinator or restore the patches programmatically.

5. **HQ Interpolation / Low Bandwidth toggles** exist on most of these. Disable HQ when you can't hear the difference (filtered, compressed, deep in mix). Enable Low Bandwidth on background pads.

6. **REX file dependency**: .drex patches and any NN-XT/NN-19 patch built from REX content needs the original REX accessible. Bundle when sharing.

7. **Velocity layer crossfades**: easy to introduce volume bumps if Fade In and Fade Out don't match. NN-XT's **Create Velocity Crossfades** auto-balances — use it.

8. **Key-map mistakes** — wrong root notes mean Automap places samples at the wrong pitch. Run pitch detection (NN-XT: "Set Root Notes from Pitch Detection"; Mimic, Grain: automatic at Sample Start) before automapping.

9. **Choosing between Grain and Mimic for sound design**: Grain is purpose-built for granular/spectral textures with a deep mod matrix. Mimic's Granular stretch is a feature, not the device's identity. For pad/drone design pick Grain.

10. **Choosing between NN-19 and NN-XT**: there is rarely a reason to start fresh with NN-19. Use NN-19 when opening legacy patches, when you want the simplest possible workflow, or to keep CPU minimal on a basic chromatic part. Otherwise default to NN-XT.

11. **Choosing between Dr. Octo Rex and NN-XT for REX content**: Dr. Octo Rex *plays the loop* tempo-locked. NN-XT *holds the slices* as a chromatic key map. If you want the original groove playing, Dr. Octo Rex. If you want to play the slices like an instrument, NN-XT. Use Copy Loop To Track to bridge them.
