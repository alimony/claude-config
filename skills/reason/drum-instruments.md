# Reason 13: Drum Instruments
Based on Reason 13.4 documentation.

Reason ships three distinct drum devices, each occupying a different niche. Choosing the right one shapes your entire workflow — Redrum for live pattern jamming, Kong for sound design, Rytmik for fast embedded-sample beats. This skill covers all three plus how to combine them.

## Comparison Table

| Device | Type | Best for | Pads/Channels | Pattern-based | CV out (per voice) | Sample sources |
|---|---|---|---|---|---|---|
| **Kong** | Drum designer / sound design hub | Custom kits, layering, physical-modeled drums, REX chopping | 16 pads (4x4) | No (uses main sequencer) | 16 gate outs | WAV, AIFF, MP3, AAC, M4A, SF2, REX (.rx2/.rex/.rcy), platform formats |
| **Redrum** | Classic step-based drum machine | Programming linear beats, classic 808/909 workflows, on-the-fly pattern jams | 10 channels | Yes — 32 patterns x 4 banks, 1-64 steps | 10 gate outs + per-channel pitch CV in | WAV, AIFF, MP3, AAC, SF2, REX slices |
| **Rytmik** | Modern sample-based drum machine | Quick beats with embedded factory samples, Reason Compact integration | 8 channels | No (main sequencer only) | 8 gate ins + 8 gate outs | Embedded factory samples ONLY (no external import) |

**Quick rules of thumb:**
- Need to step-program live and tweak knobs? **Redrum**.
- Need to sound-design a kit, layer engines, or chop REX? **Kong**.
- Need a fast, portable beat with no sample management? **Rytmik**.

---

## Kong Drum Designer

### Type & Role

Kong is Reason's flagship drum *designer* — a semi-modular drum synth/sampler with 16 pads, each routing through up to two FX inserts plus shared Bus FX and Master FX. It is **not** a step sequencer; it relies on Reason's main sequencer or external MIDI/CV for triggering. Use it when you want to build a kit from scratch, blend synthesis and samples, or process drums heavily in-device.

### Best Uses

- Building custom kits that mix sampled drums with synthesized or physical-modeled hits
- Layering engines per pad (sample + synth click + noise tone)
- Triggering REX loops via Nurse Rex (loop / chunk / slice / stop modes)
- Routing drum pads to separate outputs for external mixing
- Combining with Redrum: have Redrum trigger Kong via gate-out to gate-in for advanced sound design with pattern programming

### Architecture

```
[16 Pads (4x4)] → assigns to → [16 Drum Channels]
                                     │
                                     ▼
        Drum Module → FX1 → FX2 → Pan/Tone → Bus FX (send) → Master FX → Main Out
                                                  │
                                                  └→ Aux 1/2 sends, Separate Outs 3-16
```

**Per-pad slots:**
- 1 Drum Module (the sound generator)
- 2 FX/Support Generator slots (FX1, FX2 — inserts)

**Shared:**
- Bus FX (1 slot, send or insert depending on output mode)
- Master FX (1 slot, always last in chain)

**Pad-to-drum mapping is flexible** — multiple pads can drive the same drum with different hit types, useful for open/closed hi-hat pairs or velocity-layered pads.

### Drum Modules (Sound Generators)

| Module | What it does | Notes |
|---|---|---|
| **NN-Nano Sampler** | Multi-sample drum playback | Up to 4 hit types per drum, multiple velocity-layered samples per hit, alt-mode for round-robin |
| **Nurse Rex Loop Player** | REX loop playback | Modes: Loop Trig, Chunk Trig, Slice Trig, Stop |
| **Physical Bass Drum** | Physical modeled kick | Pitch, damping, decay, shell, beater — CPU heavier |
| **Physical Snare Drum** | Physical modeled snare | Same family |
| **Physical Tom Tom** | Physical modeled tom | Same family |
| **Synth Bass Drum** | Synthesized kick | Click, bend, noise component |
| **Synth Snare Drum** | Synthesized snare | Harmonic + noise mix |
| **Synth Tom Tom** | Synthesized tom | Click, bend, noise |
| **Synth Hi-Hat** | Analog-modeled hi-hat | Ring resonance, decay |

### Support Generators (FX1 / FX2)

These ADD sound on top of the drum module — they're not just effects:
- **Noise Generator** — pitch, attack, decay, resonance, sweep, click, velocity-responsive level
- **Tone Generator** — pitch, attack, decay, bend decay, bend, shape, velocity-responsive level

Both can be activated per-hit-type (e.g., add noise only to "open" hat hits).

### FX Modules

Available in FX1, FX2, Bus FX, or Master FX slots:

- **Drum Room Reverb** — size, decay, damping, width, dry/wet
- **Transient Shaper** — attack boost/cut, decay time, amount
- **Compressor** — amount (sensitivity), attack, release, makeup gain
- **Filter** — state-variable LP/BP/HP, freq, resonance, MIDI-triggered envelope (E2 in Bus FX, F2 in Master FX)
- **Parametric EQ** — single band, freq/gain/Q
- **Ring Modulator** — frequency, amount, MIDI-triggered envelope
- **Rattler** — adds snare resonance to anything (snare tension, tone, decay, tune)
- **Tape Echo** — time, feedback, wobble, freq, resonance, dry/wet
- **Overdrive/Resonator** — drive, resonance, chamber size, 5 body models

### Sample Loading

**Supported formats:**
- macOS: WAV, AIFF, 3G2, 3GP, MP1/2/3, MPEG, MPA, SND, AU, SD2, AC3, AAC, ADTS, AMR, CAF, M4A, M4R, MP4
- Windows: WAV, AIF, MP3, AAC, M4A, WMA
- Both: SoundFonts (.sf2), REX (.rx2, .rex, .rcy)
- Any sample rate / bit depth

**How to load:**
1. Click a pad to select its drum
2. Click the folder button (or right-click → Browse Drum Patches)
3. Or **drag and drop** a sample/.drum/.kong/REX file directly onto the Kong panel or pad
4. For NN-Nano: click sample slot, browse, assign velocity range and hit type

### Per-Pad Processing (Drum Control Panel)

Each pad has macro controls that scale module parameters:

| Control | Effect |
|---|---|
| **Pitch Offset** | Scales all module pitch params (not FX) |
| **Decay Offset** | Scales amplitude decay/release + compatible FX decay |
| **Pan** | Stereo position (post-FX1/2, pre-Bus/Master) |
| **Tone** | Built-in filter (Redrum-style), post-FX1/2 |
| **Bus FX Send** | Send level to Bus FX |
| **Aux 1 / Aux 2 Send** | External aux sends |
| **Master Level** | Final output level for that pad |

### Pad Groups (9 total)

- **3 Mute Groups** — playing one pad mutes its partners (open/closed hat pair)
- **3 Link Groups** — assigned pads trigger together (layered hits)
- **3 Alt Groups** — pads alternate or randomize on trigger

### CV / Back Panel

- **Sequencer Control**: CV pitch in, Gate in (note + velocity)
- **Modulation inputs** (with trim): Volume, Pitch, Mod
- **16 Gate Inputs** + **16 Gate Outputs** (one per pad — huge for inter-device triggering)
- **Main Out** stereo + **Outputs 3-16** (7 stereo pairs, manually routed via Drum Output selector)
- **Aux Send Out** — 2 stereo pairs
- **External Effect** ins/outs (when rack unfolded) — process external audio through Bus/Master FX

### Pad Playing & MIDI Mapping

- **Click position on pad** = velocity. Bottom of pad = soft, top = hard.
- **C1–D#2** (16 notes): one note per pad
- **C3–B6**: three adjacent keys per pad (C3-D3 → Pad 1, D#3-F3 → Pad 2…) for fast passages

### Automation Limits

- Drum modules: only **4 pre-defined parameters** are automatable
- FX/Support modules: only **2 pre-defined parameters** are automatable
- Bus FX / Master FX: first two FX params accept CV via back panel (with attenuation knobs)

### Patch Files

- **.kong** — full kit (all 16 channels + settings + sample paths)
- **.drum** — single drum/channel
- Samples stored externally; patches reference paths only

### Quick Recipe — Build a Kong Kit From Scratch

1. Create Kong (right-click rack → Create → Kong Drum Designer).
2. Click Pad 1. Open Drum & FX section (lower panel).
3. Click drum module slot → choose **NN-Nano Sampler**. Drag a kick sample onto the sample area.
4. Tune with Pitch Offset, shorten with Decay Offset (or use module's amp envelope for finer control).
5. Add **FX1 → Compressor** for snap, **FX2 → Parametric EQ** for tone shaping.
6. Click Pad 2. Load NN-Nano with snare. Add **FX1 → Transient Shaper** to emphasize attack.
7. For hi-hats: load on Pad 9 as NN-Nano with 2 hit types (closed, open). Assign Pad 10 to the *same drum* but with the open hit type. Put both pads in **Mute Group 1** so open kills closed.
8. Bus FX slot → **Drum Room Reverb**. Use Bus FX Send knob per pad to season individual drums.
9. Master FX slot → **Compressor** for glue.
10. Save as .kong patch.

### Quick Recipe — REX Loop Chopping with Nurse Rex

1. Pad 1: drum module = **Nurse Rex Loop Player**, drag REX file in.
2. Set Pad 1 hit type to **Loop Trig** (plays full loop).
3. Assign Pads 2–5 to the *same Nurse Rex drum*, set each to **Chunk Trig** — Kong divides loop equally across them.
4. Pad 6 = **Slice Trig** (single slice, alternating across multiple Slice pads = round-robin).
5. Pad 7 = **Stop** (kills playback).
6. Now you can program a Reason sequencer track that retriggers the loop, drops in chunks, and stops it on cue.

### Pitfalls

- **CPU spikes**: Physical modeling modules (PM kick/snare/tom) are CPU-hungry. Stacking 16 PM drums + heavy FX can choke. Use sampled equivalents where you don't need the modeled feel.
- **Bus FX Send doubles up in Bus FX Output Mode**: When Output Mode is set to Bus FX, the Bus FX acts as both insert AND send — set Bus FX Send to zero to avoid double-processing.
- **Automation is restricted**: Only 4 module params and 2 per FX. If you need to automate something obscure, you can't — design that knob to be one of the exposed ones, or use CV to Bus/Master FX.
- **Sample tail truncation**: NN-Nano respects sample length but the amp envelope's Decay/Release will cut tails. Use Gate mode or longer envelope times for cymbal washes.
- **Pad copy/paste**: Cmd/Ctrl+C on a pad duplicates the entire drum patch — easy way to make alt versions, but you're now editing two independent copies.

---

## Redrum Drum Computer

### Type & Role

Redrum is the classic Reason drum machine — a 10-channel sample player with a built-in 32-pattern step sequencer. It's the fastest path to a usable beat in Reason. Its workflow is "load a kit, click steps, hit Run." It also has a richer-than-it-looks per-channel parameter set: pitch, length, tone, sample start with velocity modulation, two send routings.

### Best Uses

- Programming linear beats fast (the step buttons are the killer feature)
- Classic drum-machine workflows (TR-style step programming, pattern chaining)
- Live pattern switching during arrangement
- Driving Kong or external synths via per-channel gate outs (use Redrum as a *trigger source*)
- Quickly rendering pattern data to a MIDI clip (Copy Pattern to Track)

### Architecture

10 channels in a horizontal row. Each channel is a sample slot + parameter strip + 16-step button row. Specialized channels:

- **Channel 1, 2, 10**: have **Tone** (brightness control)
- **Channel 6, 7**: have **Pitch Bend** (with Rate and Velocity)
- **Channel 3-5, 8-9**: have **Sample Start** (with velocity modulation)
- **Channel 8 & 9**: can be set to **Exclusive** (one mutes the other) — designed for closed/open hat

All channels: Pitch (±1 octave), Length, Pan, Level, VEL (velocity-to-volume), S1/S2 sends, Decay/Gate mode toggle.

### Pattern Programming

**Layout:**
- **32 patterns total**, in **4 banks (A, B, C, D)** of 8 patterns each
- **Steps per pattern**: 1-64 (extend via Edit Steps switch revealing 17-32, 33-48, 49-64)
- **Resolution**: changes step length relative to tempo (e.g., 1/16, 1/32, triplet)
- **Shuffle**: per-pattern toggle; global amount in ReGroove Mixer
- **Flam**: adds a double-strike with global Flam knob delay; red LEDs mark flammed steps

**Velocity per step (3 levels):**
| Level | Click | Color | Velocity |
|---|---|---|---|
| Hard | Shift+click (or Hard mode + click) | Red | 127 |
| Medium | Click in Medium mode | Orange | 80 |
| Soft | Alt/Option+click (or Soft mode + click) | Light yellow | 30 |

The **VEL knob** on each channel scales how strongly velocity affects that channel's volume (0 = velocity does nothing).

### Run Modes & Pattern Section

- **Run** button: starts pattern playback (works independently of main sequencer transport in some cases — useful for auditioning)
- **Pattern button**: when off, mutes pattern playback at next downbeat
- **Enable Pattern Section** toggle: when OFF, Redrum becomes a pure sound module triggered by main sequencer notes only. **Always disable this after Copy Pattern to Track** to avoid double-triggering.

### Pattern Functions

- **Shift Pattern Left/Right** — rotate all notes by one step
- **Shift Drum Left/Right** — rotate just one channel
- **Randomize Pattern/Drum** — generate random hits
- **Alter Pattern/Drum** — redistribute existing hits randomly

### Sample Loading

Same formats as Kong: WAV, AIFF, MP3, AAC, M4A (+ platform-specific), SF2, REX slices. Drag-drop onto a channel, or use the channel folder button. REX files unfold into individual slices for selective loading.

### Per-Channel Processing

| Param | Range / Notes |
|---|---|
| **Pitch** | ±1 octave, LED if non-zero |
| **Length** | Time-based; behavior depends on Decay/Gate mode |
| **Decay/Gate toggle** | Decay = gradual fade, classic drum-machine feel; Gate = abrupt cutoff at Length value |
| **Sample Start** (Ch 3-5, 8-9) | Offset into sample; velocity modulation via Start Velocity knob (great for "harder hits skip the click") |
| **Tone** (Ch 1, 2, 10) | Brightness; velocity affects brightness |
| **Pitch Bend** (Ch 6, 7) | Bend from start pitch to main pitch, with Rate and Velocity |
| **Pan** | Stereo; LED indicates stereo sample |
| **Level** | Channel volume |
| **VEL** | How much velocity scales level (positive or negative — negative = harder hits are quieter, weird and useful) |
| **S1, S2** | Send to mixer aux inputs (default: first two Chaining Aux inputs) |

### CV & MIDI

**MIDI note triggers:**
- **C1 (MIDI 36) – A1 (MIDI 45)**: trigger channels 1-10
- **C2–E3 (white keys)**: hold to mute channels
- **C4–E5 (white keys)**: hold to solo channels
- Velocity responds dynamically only when **Enable Pattern Section is OFF**

**CV per channel:**
- **Gate Out** — trigger pulse (Decay mode) or sustained gate (Gate mode)
- **Pitch CV In** — modulate that channel's pitch from external CV
- **Send Outputs** (master): 2 master sends to effect returns
- Individual **separate channel outs** bypass master stereo, allowing per-channel insert FX or mixing

### Pattern → Sequencer Conversion

Two transforms:
- **Copy Pattern to Track**: set locators to a multiple of the pattern length, select the device, run "Copy Pattern to Track" from Edit menu. Pattern becomes a single MIDI clip on the device's track, repeating to fill locators. Velocities map: Soft=30, Medium=80, Hard=127. **Disable Pattern Section afterward.**
- **Convert Pattern Automation to Notes**: turns recorded pattern-change automation into note clips. Auto-disables pattern section.

### Quick Recipe — Program a 909-Style Beat

1. Create Redrum. Load a 909 kit (.drp) via Browse Patches or drag-drop.
2. Pattern A1 selected. Steps = 16. Resolution = 1/16.
3. Click Run. Press kick-on-1 (step 1 channel 1), kick-on-9 (step 9), classic four-on-the-floor: also steps 5 and 13.
4. Snare on 5 and 13 (channel 2). Use Hard (shift+click) for emphasis.
5. Closed hat on every odd step (channel 8). Open hat on the off-beat 8th notes (channel 9). Enable **Channel 8 & 9 Exclusive** so open hat chokes closed.
6. Add a soft hat on step 4, 12 with Alt/Option+click for ghost hits.
7. Toggle **Shuffle** for swing. Adjust ReGroove Mixer Shuffle amount.
8. Add **Flam** to step 13 snare for a fill flourish.
9. Tune the kick: pull Pitch down -2 semitones, set Decay mode, Length around 11 o'clock.
10. Copy Pattern A1 to A2. Modify A2 for a fill. Use main sequencer to chain A1 four bars then A2.

### Quick Recipe — Use Redrum as a Trigger Brain

1. Program a pattern in Redrum but disable Master Out to mixer (or just turn channel levels down).
2. Flip rack to back. Connect Redrum **Channel 1 Gate Out** → Kong **Pad 1 Gate In**.
3. Now Redrum's pattern triggers Kong's much fancier kick — but you keep Redrum's step UI.
4. Repeat for snare, hats, etc. Effectively a 10-voice step sequencer driving any device.

### Pitfalls

- **Pattern lane vs main sequencer double-triggering**: After Copy Pattern to Track, the pattern still plays AND the new MIDI clip plays. Always disable **Enable Pattern Section** after copying.
- **Sample tail truncation in Decay mode**: Decay length cuts samples regardless of note length. Long crash cymbals need maximum Length, or switch to Gate mode and use the sequencer to hold notes.
- **Looped samples + max Length = infinite ringing**: If a sample contains an embedded loop and Length is at max, it never fades. Reduce Length.
- **Soloing Redrum mutes its sends in mixer**: When you solo Redrum on the mixer, the S1/S2 chained aux sends are also muted. Soloing the destination FX channel works around it.
- **High Quality Interpolation costs CPU** but markedly improves high-frequency content for pitched-up samples.
- **Pattern data lives in songs, not patches**: .drp patches store kit + parameters but NOT patterns. Save the song to keep your patterns.

---

## Rytmik Drum Machine

### Type & Role

Rytmik is the newest, simplest of the three: an **8-channel sample-based drum machine** with **embedded factory samples only** — you cannot import external samples. It's designed for fast beat creation with guaranteed patch portability (no missing-sample headaches) and tight integration with Reason Compact projects. There is **no internal pattern sequencer** — Rytmik plays from the main sequencer or MIDI/CV.

### Best Uses

- Quick beats with the factory drum library, no sample management
- Reason Compact / mobile-friendly workflows
- Patches that need to be portable (everything is embedded)
- Layering on top of Kong/Redrum for additional textures
- When you don't need pattern programming inside the device

### Architecture

8 channels arranged horizontally. Each channel is a fully embedded sample player with a built-in signal chain:

```
Sample → Distortion → Filter (HP + LP) → Pan/Volume → Send routing → Master section
```

**Master section** (always at end of chain):
- Master Compressor (always on)
- Master Pitch
- Master Reverb return
- Master Filter
- Master Volume

### Sample Loading

**No external import**. All samples are embedded factory content. Selection per channel is via dropdown menus organized into **8 sub-groups by drum type**. Use arrow buttons to step through, or pick directly from menu.

This is by design — the documentation states *"when you save a Rytmik patch the samples are always included,"* which guarantees portability with no sample paths to break.

### Per-Channel Processing

| Param | Range |
|---|---|
| **Sample Start / End** | Graphical handles on waveform |
| **Pitch** | ±1200 cents |
| **Pan** | 100L to 100R |
| **Fade In** | Independent |
| **Fade Out** | Independent (graphical envelope display) |
| **Distortion** | Transistor-type, 0–100% input gain |
| **Low Cut (HP)** | 20 Hz – 25 kHz |
| **Hi Cut (LP)** | 20 Hz – 25 kHz |
| **Volume** | Per-channel slider |
| **Mute / Solo** | Per channel |
| **Delay Send** | Per channel |
| **Reverb Send** | Per channel |

Note: there are **no LFOs, no traditional ADSR envelopes** beyond Fade In/Fade Out. This keeps Rytmik intentionally simple.

### Built-In Effects (Shared / Send)

**Delay** (send):
- Modes: Stereo, Ping Pong
- Tempo-synced divisions: 1/1, 1/2D, 1/1T, 1/2, 1/4D, 1/2T, 1/4, 1/8D, 1/4T, 1/8, 1/16D, 1/8T, 1/16
- Feedback: 0-100%
- Hardwired to main sequencer tempo

**Reverb** (send):
- 6 algorithms: Room, Large Room, Culvert, Plate, Gated, Hall
- Decay (drag to adjust)
- Built-in HP/LP on the reverb signal (Low Cut to clean up "muddy" reverb)
- Low/Hi Cut: 20 Hz – 25 kHz

**Master section:**
- **Master Compressor** (always active): Threshold (-60–0 dB), Ratio (1:1–20:1), Attack (0–200 ms), Release (0–200 ms), gain reduction meter. To "disable": set Threshold = 0 dB and Ratio = 1:1.
- **Master Pitch**: ±1200 cents on whole device
- **Master Reverb return**: ±100% (bipolar — yes, negative phase)
- **Master Filter**: combined HP/LP, ±100%
- **Master Volume**: -∞ to +6 dB

### MIDI & CV

**MIDI**: Channels respond to **C0–G0** (8 keys = 8 channels).

**CV** (back panel):
- 8 Drum Gate **Inputs** — accept Note On/Off + velocity from external CV
- 8 Drum Gate **Outputs** — send Note On/Off + velocity to other devices

**Important**: CV connections are **NOT stored in Rytmik patches**. To persist CV routings, place Rytmik inside a **Combinator** and save the Combinator patch.

### Output Architecture

- **Main L/R**: stereo mix post-Master FX, auto-routed to Mix Channel
- **8 Separate Outputs**: post-Filter, **pre-Send Effects**. Critically, *"Drum Channels routed via separate outputs are automatically disconnected from the Master FX section."* If you split out a channel, it bypasses Master Compressor/Filter/Reverb/Volume entirely.

### Quick Recipe — Quick Beat in Rytmik

1. Create Rytmik. The default kit is already loaded with embedded samples.
2. Click each channel's sample dropdown — pick kick on Ch1, snare on Ch2, hats on Ch3, etc.
3. Adjust per-channel: Pitch for tuning, Low Cut to roll off rumble, Distortion for grit.
4. Set Reverb mode = Plate. Dial Reverb Send on snare to taste.
5. Set Delay = 1/8D, Stereo. Send a small amount from a percussion channel.
6. On the main sequencer track for Rytmik, draw notes on C0 (kick), C#0 (snare), D0 (hat) etc.
7. Tighten Master Compressor: Threshold around -12 dB, Ratio 4:1 for glue.

### Quick Recipe — Persisting CV Routings

1. Create a Combinator. Drop Rytmik inside it.
2. Set up your CV connections (e.g., Matrix sequencer → Rytmik Gate Inputs).
3. Save the Combinator patch (.cmb). Now opening that Combinator restores the entire CV setup.

### Pitfalls

- **Cannot import external samples** — period. If you need your own samples, use Kong or Redrum.
- **Filter inversion**: Low Cut and Hi Cut can cross each other (Low Cut > Hi Cut), silencing the channel. Same risk in the reverb's filter.
- **CV not in patches**: Always wrap in Combinator to preserve CV setups.
- **Send effects always on**: No bypass switch on Delay/Reverb sends — only the per-channel send level. Set sends to zero rather than expecting a master bypass.
- **Master Compressor always active**: Even if you don't want compression, it's processing. Neutralize with Threshold 0 dB + Ratio 1:1.
- **No LFOs / mod matrix**: Rytmik is deliberately simple. For modulation, automate parameters via the main sequencer or use external CV.
- **Separate outs bypass Master FX**: A channel sent out the back loses Master Compressor/Pitch/Reverb/Filter/Volume.

---

## Combining the Three

These devices play well together. Some patterns:

### Layer Kong with Redrum
- Use Redrum for the rhythmic backbone (kick + snare + hats) — fast to program, easy to tweak.
- Add Kong on top for layered/sound-designed elements (a synth kick under Redrum's sampled kick, a noise sweep, a physical-modeled tom fill).
- Trigger Kong from Redrum gates: wire Redrum Channel 1 Gate Out → Kong Pad 1 Gate In. Now your Redrum step pattern drives Kong without needing two MIDI clips.

### Use Redrum as a Pattern Brain for Anything
- Redrum's per-channel Gate Outs can trigger any CV-equipped device, not just drums. Trigger Thor, Subtractor, Europa from a Redrum step pattern. The 10-channel step UI is the appeal.

### Rytmik for Reliable Bounces
- If you're sending a song to someone else and worried about missing samples, Rytmik's embedded library is bulletproof. Use it for the core kit and Kong for anything custom.

### Send Architecture Trick
- Redrum's S1/S2 → mixer aux returns. Run Kong as the "FX brain" by routing Kong's external audio inputs from the aux send returns. Now Redrum's drums get processed through Kong's Bus FX / Master FX chain.

### Pattern Conversion Workflow
- Program in Redrum's step UI for speed. **Copy Pattern to Track** to convert into MIDI notes on the main sequencer. Disable Pattern Section. Now you can humanize timing, layer additional notes, or move to Kong/Rytmik.

---

## Cross-Device Cheatsheet

**Need step programming?** Redrum is the ONLY one with built-in patterns. Kong and Rytmik rely on the main sequencer.

**Need to import your own samples?** Kong and Redrum yes; Rytmik no.

**Need physical-modeled drums?** Kong only.

**Need REX loop chopping?** Kong (Nurse Rex) is purpose-built. Redrum can load REX slices but as individual sample channels.

**Need a separate output per drum?** All three offer separate outs, but Kong has 7 stereo pairs (14 channels routable), Redrum has 10 individual channel outs, Rytmik has 8 separate outs (which bypass Master FX).

**Need pad-velocity sensitivity from clicking the device UI?** Kong (click-position-on-pad = velocity).

**Need patch portability with embedded samples?** Rytmik only. Kong and Redrum reference samples by path.

**Lowest CPU?** Rytmik (simple, embedded sample playback). Highest CPU is Kong with all-physical-modeling kits.

**Best for live pattern jamming?** Redrum (pattern banks, Run button, step UI, on-the-fly Shuffle/Flam).

**Best for sound design?** Kong (16 pads, multiple engines, 2 FX inserts per pad, Bus + Master FX, support generators).
