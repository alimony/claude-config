# Reason 13: Synthesizers
Based on Reason 13.4 documentation.

This skill covers the six core synthesizer instruments shipped with Reason 13: Europa, Malstrom, Monotone, Polytone, Subtractor, and Thor. Each has a distinct synthesis paradigm and sweet spot. Pick the right tool for the sound you want.

## Comparison Table

| Synth | Type | Polyphony | Best For | CPU Level |
|---|---|---|---|---|
| **Subtractor** | Subtractive (analog-style, dual osc + dual filter) | Up to 99 | Classic basses, leads, simple pads, aggressive FM/ring | Low |
| **Thor** | Hybrid semi-modular (3 osc slots, 3 filter slots, modulation matrix) | Up to 32 | Anything: from analog to wavetable to FM, complex modulated patches | Medium-High |
| **Malstrom** | Graintable (granular + wavetable) | Up to 16 | Evolving textures, special effects, abstract pads, motion-based timbres | Medium |
| **Europa** | Hybrid wavetable / spectral / FM / physical / additive (3 engines) | Up to 16 | Modern pads, complex leads, evolving wavetables, custom waveform design | Medium-High |
| **Polytone** | Subtractive dual-layer with state-variable filter morphing | Up to 20 | Lush analog pads, layered/morphing patches, vintage-flavored sounds | Medium |
| **Monotone** | Subtractive monophonic | 1 (mono) | Sub bass, classic mono bass, lead lines, glides | Very Low |

**Quick guidance:**
- Need a fat mono bass fast? **Monotone**.
- Need a classic poly analog patch with minimal fuss? **Subtractor** or **Polytone**.
- Need analog-flavored layered pads or morphing duo timbres? **Polytone**.
- Need to design something unusual or sound-design-heavy? **Thor**, **Europa**, or **Malstrom**.
- Need complex modulation routing? **Thor**'s matrix is unmatched.
- Need to load custom samples as oscillator material? **Europa**.
- Need motion/time-evolving textures without re-triggering? **Malstrom**.

---

## Subtractor

The classic Reason synth. Two oscillators, dual filter (multimode + 12 dB LP), three envelopes, two LFOs. Subtractor is the simpler classic; **Thor is the modular powerhouse**, but Subtractor is faster, lighter, and still capable of every essential analog-style sound.

### Architecture

**Oscillators (2):**
- 32 waveforms each. First four are standard (saw, square, triangle, sine); the rest are tailored timbres (brass, strings, bells, etc.) that pre-bake harmonic content for instrument emulation.
- **Phase Offset Modulation** — a Subtractor signature. Each oscillator can generate a phase-offset secondary copy of itself, then either *multiply* or *subtract* the two. This produces PWM and oscillator-sync-style effects from any waveform without dedicated PWM/sync controls.
- **FM** — Osc 2 modulates Osc 1's pitch. Tuning relationships determine harmonic vs. enharmonic results.
- **Ring Modulation** — multiplies the two oscillators for bell-like sum/difference content.
- **Noise generator** routed through Osc 2 with Decay, Color (white → sub-rumble), and Level.
- **Keyboard tracking toggle** — disable for fixed-pitch effects/percussion.

**Filters (2 in series):**
- Filter 1: multimode — LP24, LP12, BP12, HP12, Notch.
- Filter 2: fixed 12 dB LP, can **link** to Filter 1 (Filter 1 sweeps drag Filter 2 along while preserving the offset).
- Standard FREQ / RES / Keyboard Track.

**Envelopes (3):** Amp, Filter, Mod (with selectable destination: Osc 1/2 pitch, Osc Mix, FM amount, Phase, Filter 2 freq) — all ADSR with Invert toggle on Filter Env.

**LFOs (2):**
- LFO 1: monophonic. Tempo-syncable (16 divisions). Destinations include Osc 1+2, Osc 2 only, Filter, FM, Phase, Osc Mix.
- LFO 2: **polyphonic** (per-voice cycle). Has Delay (slow-onset modulation) and Keyboard Tracking (rate scales with pitch). Targets Osc 1+2, Phase, Filter 2 freq, Amplitude (tremolo).

### Modulation

- **Velocity** to 10 destinations with bipolar polarity: Amplitude, FM, Mod Env amount, Phase, Filter 2 freq, Filter Env amount/decay, Osc Mix, Amp Env Attack.
- **Mod Wheel** simultaneous control: Filter 1 freq + Filter 1 res + LFO 1 amount + Phase + FM.
- **External MIDI** (aftertouch / expression / breath): Filter 1 freq, LFO 1 amount, amplitude, FM.

### CV I/O

**CV inputs:** Osc 1 & 2 pitch, Phase (both), FM amount, Filter 1 freq + res, Filter 2 freq, Amp level, Mod Wheel.
**CV outputs:** Mod Envelope, Filter Envelope, LFO 1.
**Gate inputs:** Amp, Filter, Mod envelopes — independently triggerable.

### Signature Features

- **Phase Offset Modulation** — the way to get PWM and sync from any of the 32 waveforms.
- **32 instrument-leaning waveforms** save you work for acoustic emulations.
- **Polyphonic LFO 2 with delay** — subtle per-voice movement without monolithic LFO sweeps.
- **Linked dual filters** for cascaded filtering and formant-like effects.

### Quick start: classic acid bass

1. Init patch. Disable Osc 2.
2. Osc 1 = sawtooth, single sustain.
3. Filter 1 = LP24, FREQ low (~30%), RES high (~75%).
4. Filter Env: Attack 0, Decay short (~30%), Sustain 0, Release short. Amount high (~80%).
5. Amp Env: A=0, D=long, S=full, R=short.
6. Slight Portamento. Set polyphony to 1 + Legato for slides.

### Quick start: detuned saw lead

1. Both oscillators = saw, Osc 2 detuned ~7 cents.
2. Filter 1 = LP24, FREQ ~60%, RES low.
3. LFO 2 (poly) → Phase, Delay = halfway, Rate slow → adds slow stereo-like movement.
4. Mod Wheel → Filter 1 freq for expression.

### Tips & Pitfalls

- **Filter slider is fighting the envelope.** If you tweak Filter Freq and "nothing happens," the Filter Env is overriding it. Adjust Env Amount, not the slider.
- **Phase Offset = 0 with subtraction = silence.** If you select waveform subtraction mode, set Phase Offset > 0 or you'll get nothing.
- **Linked filters at low freq + high res = explosion.** Pulling Filter 2 down to 0 with both filters linked and high resonance produces dangerous volume spikes.
- **FM only audible when Osc 2 is on.** The FM knob does nothing if Osc 2 is muted.
- **CV connections do not save in patches.** Wrap in a Combinator or use a Rack Extension Combi to preserve routing.

---

## Thor

The Reason flagship. Semi-modular: oscillator and filter slots accept different module types, and a deep modulation matrix routes anything to anything. **Subtractor is the simpler classic; Thor is the modular powerhouse** — use Thor when you need fine-grained control or unusual signal flow.

### Architecture

**Oscillator slots (3):** any combination of these six types per slot:
1. **Analog** — saw/pulse/tri/sine + PWM. The classic.
2. **Wavetable** — 32 wavetables, up to 64 frames each, with morphable Position and crossfade.
3. **Phase Modulation** — Casio CZ-style; combine two waveforms serially with waveshape control.
4. **FM Pair** — carrier/modulator with ratios 1–32. The simplest "real FM" option.
5. **Multi-Osc** — multiple detuned waveforms per voice for instant supersaw-style fatness.
6. **Noise** — Band (pitched), S/H, Static, Color, White.

All osc types share Octave (±10), Semi (12), Tune (±50¢), Keyboard Track.

**Filter slots (3 — 2 voice + 1 global):**
1. **Ladder LP** — Moog-style. 6/12/18/24 dB slopes, self-oscillating, integrated shaper in feedback (Type I/II at 24 dB).
2. **State Variable** — 12 dB multimode (LP/BP/HP/Notch/Peak), with sweepable HP/LP blend on Notch/Peak.
3. **Comb** — positive/negative; resonant feedback for phasing/flanging.
4. **Formant** — vowel synthesis with X/Y axes and Gender control.

Shared filter params: FREQ, RES, KBD (keyboard track), ENV (env amount), VEL (velocity sens — only active when ENV ≠ 0!), INV (invert env), Drive.

**Filter routing:** Filter 1 and Filter 2 can be parallel or serial via routing arrows. Filter 3 is a global filter after the Shaper/Amp/Effects chain — perfect for processing audio inputs.

**Envelopes:**
- **Filter Env** (per voice, ADSR; pre-wired to F1+F2)
- **Amp Env** (per voice, ADSR; gates voice output — cannot be bypassed)
- **Mod Env** (per voice, ADR with pre-delay + loop; **freely assignable via matrix**)
- **Global Env** (ADSR with pre-delay, hold, loop, tempo sync; single-trigger — does NOT retrigger on legato notes)

**LFOs:**
- **LFO 1** — voice section, polyphonic.
- **LFO 2** — global, monophonic, single-trigger Delay/Key Sync.

**Step Sequencer:** 16 steps. Per-step note, velocity, gate length, step duration. Two assignable Curve modulation parameters per step. Run modes: Repeat, 1-Shot, Step-by-step. Direction: Forward, Reverse, Pendulum 1/2, Random. Tempo-syncable.

**Shaper:** 9 modes (Soft Clip, Hard Clip, Saturate, Sine, Bipulse, Unipulse, Peak, Rectify, Wrap) with Drive — sits between Filter 1 and Amp.

**Effects (global):** Chorus + Delay, both tempo-syncable, with internal LFO modulation per effect.

### Signal Flow

Osc 1/2/3 → Mixer → routing buttons select Filter 1 / Filter 2 (parallel or series) → Shaper → Amp → Global Filter (F3) → Chorus/Delay → Outputs.

### Modulation Matrix — the heart of Thor

Three bus types stacked in the matrix:
1. **Standard (7 rows)** — Source → Amount → Destination → Amount → Scale (a third source that scales the amount).
2. **Dual Destination (4 rows)** — Source → Dest 1 + Dest 2 (independent amounts) → Scale.
3. **Dual Scale (2 rows)** — Source → Destination, with two independent Scale modulators.

Sources include audio (Osc 1/2/3 audio, Filter audio, Shaper audio, Amp audio — yes, you can use audio as CV), all envelopes, both LFOs, performance controllers, polyphony, sequencer parameters, CV inputs, audio inputs.

Destinations: pitch, FM, oscillator modifier knobs, filter freq/freq-FM/res/drive/gender/LP-HP-mix, shaper drive, amp gain/pan, mixer levels and balance, envelope times, portamento time, LFO rates, sequencer Trig/Rate/Transpose/Velocity/Gate Length, CV outputs, audio outputs.

### CV I/O

**CV inputs:** Sequencer Control (CV pitch + Gate), 4 rotary CV ins with trim pots, dedicated Filter 1 input (frequency or Formant X), 4 generic CV ins (matrix sources).
**CV outputs:** Global Env, LFO 2, 4 assignable.
**Audio I/O:** 4 audio ins (mono routing to voice section needs gate; stereo to global section doesn't), 4 audio outs.

### Signature Features

- **The modulation matrix.** Audio-rate modulation, audio-as-CV, CV-as-audio — anything to anything.
- **Modular oscillator/filter slots** — switch synthesis paradigms mid-patch.
- **Self-oscillating filters** as additive sources (Ladder, SVF, Comb).
- **Per-step sequencer curves** — two extra modulation lanes per step beyond note/vel/gate.
- **Global section** — a whole second LFO/Env/filter chain that survives polyphonic playback.

### Quick start: screaming Thor lead

1. Osc 1 = Analog Saw, Osc 2 = Analog Saw with Tune +7¢.
2. Filter 1 = Ladder LP 24, FREQ ~50%, RES ~70%. Drive halfway up.
3. Filter Env to F1: ENV ~70%, A=0, D=400 ms, S=60%, R=300 ms.
4. Amp Env: A=0, D=long, S=full, R=300 ms.
5. Matrix: Mod Wheel → Filter 1 Freq +60.
6. Matrix: LFO 1 (triangle, slow) → Osc 2 Pitch +1¢ for shimmer.
7. Polyphony = 1, Mono Legato, Portamento Auto.

### Quick start: evolving wavetable pad

1. Osc 1 = Wavetable, choose a wide-spectrum table.
2. Filter 1 = State Variable LP, FREQ ~70%, RES low.
3. Mod Env: long A (3s), long R, loop on.
4. Matrix: Mod Env → Wavetable Position +50.
5. Matrix: LFO 1 (slow random) → Wavetable Position +20 (Scale = Mod Wheel for player control).
6. Global Filter (F3) = Comb, slight modulation from LFO 2 → Filter 3 Freq.

### Quick start: FM bell

1. Osc 1 = FM Pair, ratio C:M = 1:7.
2. Filter 1 = bypass (RES 0, FREQ max) or SVF HP for thinning.
3. Mod Env: A=0, D=2s, R=2s. Matrix: Mod Env → Osc 1 FM Amount +80.
4. Filter Env minimal. Amp Env: short A, long D, S=0, long R.

### Tips & Pitfalls

- **Routing buttons matter.** Oscillators only feed filters via the numbered routing buttons (1/2/3). If an oscillator is silent despite the Mixer level, check it's routed.
- **Audio inputs to voice section need gate.** Routing audio in to voice destinations requires keyboard or sequencer gate. Use global section to process audio without gating.
- **Changing filter type keeps modulation assignments.** If you change a filter and parameter X no longer exists, prior matrix assignments may misbehave. Audit the matrix after swapping modules.
- **VEL only works with ENV.** Velocity sensitivity on filters is gated by Env Amount being non-zero.
- **LFO 2 is mono and single-trigger.** New polyphonic notes don't restart LFO 2 or Global Env. Use LFO 1 / Mod Env for per-voice movement.
- **Step Sequencer octave persistence.** The octave lever stores per-step; mid-edit changes only affect newly-edited steps.
- **CPU.** Thor at high voice counts with multiple osc slots active is the heaviest of these synths. Drop polyphony, freeze tracks, or simplify modulators if your project crawls.

---

## Malstrom

A graintable synth: granular synthesis sampling cut into grains, plus a wavetable-style index sweep. Where everything else generates from oscillator math, Malstrom plays *recorded sound material* and lets you scrub, freeze, and harmonically warp it. Best for evolving textures, abstract sound design, and motion-driven leads/pads.

### Architecture

**Oscillators (Osc:A, Osc:B):** two graintable oscillators, up to 16 voices. Each has:
- **Octave** (±4), **Semi** (0–12), **Cent** (±50).
- **Index slider (0–127)** — playback start point. The 0–127 range *always* spans the entire graintable regardless of the actual grain count (which can be 3 to 333) — beware: this isn't 1:1 with grains.
- **Motion knob** — speed of advancement through grains. Fully left = freeze on a single static waveform.
- **Shift knob** — pitch-shifts individual grains, altering harmonic content without changing perceived pitch. Independent timbral morphing.

Graintable motion patterns: Forward (loop) or Forward-Backward (bidirectional).

**Filters (Filter:A, Filter:B):** two identical multimode filters.
- LP12, BP12, Comb+ / Comb– (short-delay resonant; Comb– has bass cut), AM (ring mod with internal sine).
- Per filter: Freq, Res (in AM mode controls clean/modulated balance), Kbd track, Env enable.

**Shaper** (pre-Filter A): five modes — Sine (smooth), Saturate (rich), Clip (harsh), Quant (bit-reduction), Noise (multiplicative).

**Envelopes (3 ADSR):**
- Amp Env A → Osc:A level
- Amp Env B → Osc:B level
- Filter Env → shared, with Inv toggle and Amount

**Critical:** Amp envelopes are *before* the filters. Filter sweeps need the Filter Env enabled separately on each filter.

**Modulators (2 LFOs: Mod:A, Mod:B):**
- Curve, Rate, Sync (16 divisions), **One Shot** (turns LFO into envelope — plays once per note).
- A/B selector routes modulation to A, B, or both.
- **Mod:A** destinations: Pitch, Index, Shift.
- **Mod:B** destinations: Motion speed, Volume, Filter freq, Mod:A amount (meta-modulation!).

### Routing

Front-panel routing buttons select signal flow. Key configurations:
1. Bypass filters entirely (oscillators direct to outputs).
2. Both osc → single filter (mono).
3. Osc:A → both filters in **parallel** (parallel only available for Osc:A).
4. Osc:A → both filters in series (or with Osc:B mixed in).
5. Shaper position: pre-Filter A or as final stage.

**Limitation:** Osc:B can route to both filters but only in **series**.

### Modulation Targets

- **Velocity** (bipolar): Osc A/B level, Filter Env amount, Attack time, Shift, Modulation amount.
- **Mod Wheel** (bipolar): Index, Shift, Filter freq, Mod amount (A/B selector chooses target).

### CV I/O

**Audio:** main outs (Filter A L / Filter B R), Osc:A/Osc:B direct outs (bypass filters), audio inputs for external processing or self-patching.
**Gate inputs:** Amp Env, Filter Env.
**CV inputs:** Osc pitch, Filter freq, Index offset, Shift, Amp level, Mod amount, Mod wheel — all with trim pots and A/B selectors.
**CV outputs:** Mod:A, Mod:B, Filter Env.

### Signature Features

- **Graintable scrubbing** — Index, Motion, and Shift work independently. You can freeze on a grain (Motion = 0), then sweep Index to morph through the timbre, then shift harmonics without changing pitch.
- **Filter morphing via routing** plus **AM (ring mod) filter mode** for non-harmonic content.
- **Mod:B → Mod:A amount** lets you create modulated modulation depth.
- **Self-patching** for vintage-style multi-trigger filter behavior.

### Quick start: evolving texture pad

1. Osc:A = a vocal/string graintable. Motion = halfway. Index = 0.
2. Mod:B → Motion (slow rate, sync to bar). Slowly walks through the timbre.
3. Filter:A = LP12, Freq 70%, Filter Env enabled, slow attack/release.
4. Long Amp Env A: 2s attack, full sustain, 3s release.
5. Mod:A → Shift (slow sine LFO) for harmonic shimmer.

### Quick start: abstract glitch lead

1. Osc:A = an aggressive/noisy graintable. Index = 30. Motion = 70%. Shift hard right.
2. Shaper = Quant.
3. Filter:A = Comb+, high Res, Env enabled, fast Decay.
4. Mod:B One-Shot → Filter freq, Curve = ramp down.
5. Mod:A → Index, fast random for glitchy scrubbing.

### Quick start: vintage multi-trigger pad

Connect Osc:A out → Malstrom audio input. This forces Filter Env to retrigger on *any* voice, creating shared monophonic filter behavior across all voices — classic vintage poly-synth quirk.

### Tips & Pitfalls

- **Index is not grain-accurate.** 0–127 spans whole table regardless of grain count. Don't expect step-wise grain selection.
- **Amp envs are pre-filter.** A long filter sweep needs Filter Env enabled separately, not just the Amp env.
- **Spread parameter only valid with both filters used.** Single-output configs require Spread = 0 to avoid phase weirdness.
- **Velocity/Mod Wheel are bipolar.** Center = no effect. Negative values invert the response (e.g., negative attack-velocity makes hard hits *shorter*).
- **Filter Env triggers per any voice.** When self-patching audio in, all voices share one filter envelope retriggered globally. Useful, but confusing if unintended.
- **Polyphony.** Up to 16 voices but unused voices cost nothing. Higher polyphony has no penalty until used.

Cross-ref: Malstrom's Mod:A/B with One-Shot = closer in spirit to **Europa**'s drawable envelopes than to **Subtractor/Thor**'s LFOs.

---

## Europa

Three independent sound engines running in parallel, each with its own oscillator/modifier/spectral filter/harmonics/unison chain. After mixing, signal hits a master filter, amp section, and a six-slot reorderable effects chain. Distinguishes itself with the **spectral filter**, **drawable envelopes**, **user-loadable wave samples**, and the deep modulation bus. Closest peer is **Thor**, but where Thor is modular slots + matrix, Europa is fixed-architecture-three-engines + spectral-domain processing.

### Architecture

**Three sound engines** — each is a complete chain:

1. **Oscillator** with extensive waveform menu:
   - Analog morphing (sine→tri→square→saw)
   - Physical models (Karplus-Strong string, vocal cord)
   - Spectral types (Formant Sweep, Synced Sine)
   - FM variants with 1:1, 1:2, 1:8, 2:1 ratios
   - Noise (S/H, Perlin, Bit)
   - 8-waveform wavetable banks
   - **User-loadable samples** (auto-pitch-detected or 2048-sample-cycle assumed)

   Per oscillator: Oct (±5), Semi (±12), Tune (±50¢), Kbd track (0–100%), **Shape** with modulation source assignment.

2. **Two Modifiers** in series — 18 algorithms (sync, distortion, harmonics multiplication, detuning, etc.).

3. **Spectral Filter** — 12 types (LP/HP/BP/Notch, parametric EQ, comb, resonators, custom envelope curves). Operates on partials.

4. **Harmonics processor** — 8 algorithms (random gain, harmonic mixing, stretch, ensemble, noise modulation) modulating partial relationships.

5. **Unison** — up to 7 detuned voice pairs in stereo, 4 type variations.

**Master filter (post-mix):**
- 9 types: SVF (HP/BP/LP/Notch), Ladder LP 24 dB, MFB (LP 12/24, HP 24), K35 LP 12.
- Drive parameter for overdrive distortion.
- Kbd track, modulation source, velocity scaling.

**Amplifier:** ADSR envelope shared across all three engines, plus Pan and Gain (with velocity).

**Envelopes (4 polyphonic, drawable):**
- Preset curves (ADSR, ramps, custom).
- Interactive point editing, draggable sustain, **loop mode**, Key Trigger / Global mode.
- Edit Y-Position mode (level-only).
- Cmd/Ctrl+drag = freehand drawing.
- **Env 3 & 4 drawable curves usable as oscillator waveforms.**
- **Env 4 usable as Spectral Filter curve.**
- Multiplication modes: Env 3 × Env 4, Env 3 × LFO 3.

**LFOs (3):** sine/triangle/pulse/random/slope/stepped, beat-syncable, Key Sync per note, Delay (Ctrl+drag for length), Global mode for monophonic operation.

**Effects (6 reorderable, drag-and-drop):**
1. Reverb (send): Decay, Size, Damp, Amount.
2. Delay (send): Sync, Time, Ping Pong, Pan, Feedback, Amount.
3. Distortion: 6 types (Dist, Scream, Tube, Sine, S/H, Ring).
4. Compressor: Atk, Rel, Threshold, Ratio.
5. Phaser/Flanger/Chorus: toggleable.
6. Parametric EQ: Freq, Q, Gain ±18 dB.

All effect parameters routable as Modulation Bus destinations.

### Modulation Bus

8 source→destination strips. First four pre-assigned. Each strip supports **dual destinations** with independent amounts and **optional scaling** by an additional source.

**Sources:** Velocity, Last Velocity, Aftertouch, 3 LFOs, 4 custom Envelopes, Mod/Pitch wheels, Breath, Expression, Sustain pedal, Kbd, random, noise, polyphony, CV inputs 1-4 (latched variants available).

**Destinations:** engine parameters (pitch, shape, modifier amounts, filter freq/reso, harmonics, unison), mixer (level/pan per engine), filter section (drive/freq/reso), amp (gain/pan/env times), LFO delay/rate, portamento time, all effect parameters, CV outputs 1-4.

### CV I/O

Sequencer Control: CV pitch, Gate (note on/off + vel), Pitch Bend, Mod Wheel inputs.
CV Modulation: 4 assignable CV ins (standard + latched variants), 4 assignable CV outs.
Audio: stereo L/R outs.

### Signature Features

- **Three parallel engines** — layer entirely different syntheses (e.g., FM lead + sampled string + noise sub) inside one device.
- **Spectral Filter** — frequency-domain processing with custom envelope curves.
- **Drawable envelopes used as oscillator/filter source** — Env 3/4 themselves become waveforms or filter shapes.
- **User Wave loading** — drop a sample in as oscillator material.
- **Interactive displays** — Waveform, Spectral Filter, Unison panes update in real time and are drag-controllable + automatable.

### Quick start: lush wavetable pad

1. Engine 1: Wavetable, Shape modulated by LFO 1 (slow).
2. Engine 2: same wavetable, detuned -5¢, Unison 3 voices.
3. Engine 3: Noise (S/H), low level, panned right.
4. Master filter: Ladder LP 24, FREQ 65%, slight Drive.
5. Mod Bus: Mod Wheel → Spectral Filter curve position.
6. Reverb amount up, Delay sync 1/4 dotted with low feedback.

### Quick start: drawn-envelope morphing lead

1. Engine 1: Analog saw.
2. Engine 2: Analog square, detuned.
3. Draw Envelope 3 as a custom waveform (peaks/dips); use as Engine 3's oscillator.
4. Loop Env 3 to create motion.
5. Master filter: K35 LP, Mod Wheel → Filter Freq.
6. Amp Env: short A, long D, low S, long R.

### Quick start: physical-model plucked string

1. Engine 1: Karplus-Strong oscillator.
2. Modifiers: minimal, just one for harmonic shaping.
3. Spectral Filter: HP, modest cutoff.
4. Amp Env: A=0, D=2s, S=0, R=1s — natural pluck decay.
5. Velocity → Filter Freq for dynamics.

### Tips & Pitfalls

- **Patches store sample references, not embedded audio.** User samples must remain on disk and accessible.
- **Amp Env is shared across all three engines.** No way to give Engine 2 a different envelope shape directly — but you can modulate per-engine Mixer level with separate envelope curves to fake it.
- **Filter self-oscillation hazard.** Ladder and MFB filters at high resonance can produce dangerous amplitude spikes.
- **Spectral Filter display is non-interactive.** Unlike the Waveform display, you can't drag the Spectral Filter visualization.
- **Polyphony 1–16.** DSP load scales with simultaneous notes, not the polyphony setting.
- **Unison is expensive.** 7 voices × polyphony adds up fast. Use sparingly per engine.
- **CV connections do not save in patches.** Embed in a Combinator if you need persistent routings.

Cross-ref: Europa's three engines + master filter is conceptually closer to **Polytone**'s dual-layer structure than to **Thor**'s modular slots, but Europa adds spectral processing and drawable envelopes that no other Reason synth has.

---

## Polytone

Dual-layer subtractive synth. Each layer is a complete two-osc + state-variable-filter + envelopes voice. Layers can play singly, mix together, or **morph** continuously between two completely different sounds. Best for analog-inspired pads, vintage-flavored bell tones, and patches you want to evolve between two timbres. **Subtractor** is monosynth-with-extras simple; Polytone gives you that times two with built-in morphing.

### Architecture

**Each layer (A and B) contains:**

**Oscillators (2 + noise per layer):**
- Waveforms: Saw-Pulse, Pulse, Triangle, Sine, Digital (wavetables), Band Noise (Osc 1 only), Chaos (Osc 2 only).
- **Shape parameter** continuously morphs the waveform (e.g., saw→square in Saw-Pulse mode).
- **Cross-modulation:** Osc 2 frequency-modulates Osc 1.
- **Oscillator Sync:** Osc 2 syncs Osc 1 — classic pitch-modulated sync sweeps.
- Octave (5-octave range), Detune (±50¢ per osc).

**Filter (per layer):** continuous **state-variable filter** with seamless morph:
24 dB LP → 12 dB LP → 12 dB BP → 12 dB HP → 24 dB HP.
- Filter Type knob morphs through the curve.
- Sources: Filter Env, Mod Wheel, **Filter FM** (Osc 2 → Filter Freq).
- Drive LED indicates clipping.

**Envelopes (per layer):**
- **Filter Env** — ADSR.
- **Amp Env** — ADSR.
- **Mod Env** — AR (Attack/Release; Release maxed = sustain forever).

**LFOs:**
- **Mod LFO** (per layer) — Rate 0.16–57 Hz, Delay 0–2 s, waveforms: sine, tri, pulse, stepped/smooth random. Targets: pitch, shape, FM amount, filter freq.
- **Global LFO** (affects both layers) — same controls plus Sync, **1-Shot**. Can modulate Mix/Morph balance.

**Amp section per layer:** Gain, Velocity (0–100%), **Spread** (alternating L/R per voice, disabled in Legato mode).

**Pitch:** Bend range ±24 semitones (per layer), Kbd track 0–100%, Fine ±50¢.

### Layer Modes

- **Single** — Layer A or Layer B only.
- **Mix** — Both layers simultaneous, fixed or modulated levels.
- **Morph** — All layer-specific parameters interpolate continuously between A and B.

**Mix/Morph control sources:** Mod Wheel, Velocity, Global LFO, front-panel Fader (center = 50/50), CV input with attenuation.

**Layer operations:** Copy A→B or B→A, Swap layers, Cmd/Ctrl+Z undo.

### Modulation Wheel (per layer, independent)

- FM Amount.
- Filter Freq.
- LFO Depth — scales all parameters set to the "LFO range" (counter-clockwise of center).

### Polyphony & Key Modes

- Max **20 voices**.
- **Poly** — standard polyphonic. Glide is unpredictable across voices.
- **Retrig** — monophonic with envelope retrigger per note.
- **Legato** — monophonic; envelopes sustain through legato. **Spread is disabled in Legato.**
- **Glide/Portamento** with Auto mode (legato-only).

### Effects (Global)

- **Chorus** — stereo, two speeds + fixed-speed flanger option.
- **Reverb** — echo + two stereo reverb types, adjustable decay.

### CV I/O

Sequencer Control (CV pitch + Gate), Mix/Morph CV (with attenuation), CV Modulation inputs for parameters, Wheels CV (Pitch Bend + Mod Wheel emulation), stereo audio outputs.

### Signature Features

- **Continuous-morphing state-variable filter** (LP24→LP12→BP→HP12→HP24 in one knob).
- **Dual layers with continuous Morph mode** — all layer parameters interpolate.
- **"Age" parameter (2024 → 1970)** — simulates analog component drift; intentional pitch/filter fluctuation.
- **Filter FM** built into the per-layer filter (Osc 2 → Filter Freq for vocal-like timbres).

### Quick start: massive analog pad

1. Layer A: Saw-Pulse (Shape ~30%), Osc 2 detuned +5¢. Filter LP24 ~50%, low Res.
2. Layer B: Triangle + Sine, both detuned, Filter LP12 ~70%.
3. Mode: Mix. Fader at 50/50.
4. Both layers: long Amp Env (A=2s, R=3s), slow Mod LFO → pitch (small amount) for drift.
5. Spread on both layers, Poly mode.
6. Chorus on, Reverb decay long.

### Quick start: morph-pad lead

1. Layer A: bright lead — saws, fast filter env, short release.
2. Layer B: pad — triangles, slow filter env, long release.
3. Mode: Morph. Mod Wheel controls Mix/Morph.
4. Player gets to morph between cutting lead and ambient pad in real time.

### Quick start: vintage drift

1. Both layers identical analog saw, Mix mode.
2. Crank "Age" toward 1970.
3. Pitch wobbles, filter cutoff drifts subtly. Instant character.

### Tips & Pitfalls

- **Legato kills Spread.** If you want stereo voice movement, use Retrig or Poly.
- **High Res + high osc level = distortion.** Watch the Drive LED.
- **MOD knobs are bipolar with center deadzone.** Counter-clockwise of center = LFO; clockwise = ENV. Stay at center = no modulation.
- **Global LFO in Morph mode switches** between waveforms rather than morphing them — be aware if you're modulating waveform shape via Morph.
- **"Age" fluctuates pitch.** Intentional. If you need rock-solid tuning, set Age to 2024.
- **Filter Type in series with Mod sources.** Modulation moves around within the morph curve, not just freq.

Cross-ref: Polytone is the natural step up from **Subtractor** when you want stereo/morph capabilities without diving into **Thor**'s matrix complexity.

---

## Monotone

Monophonic subtractive bass synth. Two oscillators, ladder filter, LFO, two envelopes, glide. That's it. **The fastest way to get a fat mono bass in Reason.** No polyphony to worry about, no matrix, no layers — open it, dial it, done.

### Architecture

**Oscillators (2):**
- Waveforms: Ramp (saw), Square (Pulse on Osc 2), Triangle, Sine.
- Octave (5-octave range), Detune ±50¢ per oscillator.
- Independent Noise generator with level.
- **Osc 2 can FM Osc 1** for metallic/bell textures.

**Filter:** classic 24 dB ladder LP with Drive (pre-filter overdrive).
- FREQ, RES (self-oscillates at high settings — explicitly noted in the manual).
- Kbd track (0–100%, 1 semi/note at max).
- Envelope amount, LFO amount.

**Envelopes (2 ADSR):**
- **Amp Env** — output level. Velocity-sensitive.
- **Mod Env** — modulates oscillator FM and filter frequency. Velocity-sensitive.

**LFO:** Rate 0.06–94 Hz. Sine, Triangle, Square. Routes to oscillator pitch (vibrato) and/or filter freq. Mod Wheel scales intensity.

**Portamento:**
- **On** — always glides between consecutive notes.
- **Auto** — glides only during legato.
- **Off** — no glide.
- **Retrig button** — when on, envelopes restart on every new note; when off, you must release the previous note before retriggering.

**Pitch:** Bend ±1 to ±24 semitones.

**Mod Wheel:** controls Filter freq + LFO intensity independently via dedicated FILT and LFO knobs above the wheel.

### Effects

- **Chorus** — stereo: Amount, Rate, Spread.
- **Delay** — tempo-synced (1/16 to 2/4), Amount, Time, Feedback, Ping Pong.

### CV I/O

- Sequencer Control: CV (pitch), Gate (note on/off + vel), Pitch Bend, Mod Wheel inputs.
- Modulation CV inputs for parameters.
- Stereo audio outputs (auto-routed to mixer).

### Signature Features

- **Monophonic by design** — no polyphony controls to mismanage.
- **Ladder LP filter with Drive** — that classic squelchy/aggressive analog character.
- **Retrig switch** — vintage envelope behavior toggle for true mono lead lines.
- **Velocity-sensitive Mod Env** — adds dynamic punch with no matrix configuration needed.

### Quick start: fat mono sub bass

1. Osc 1 = Ramp, Octave low. Osc 2 = Sine, Octave one lower (sub).
2. Detune Osc 1 slightly, mix Osc 2 louder for sub.
3. Filter: LP24, FREQ 30%, RES 15%, Drive 30%.
4. Mod Env (filter): A=0, D=200ms, S=0, R=100ms, Amount ~60%.
5. Amp Env: A=0, D=full, S=full, R=100ms.
6. Portamento Auto for slides on legato.

### Quick start: classic acid mono lead

1. Osc 1 = Ramp, single oscillator.
2. Filter: LP24, FREQ low, RES 75%, Drive 40%.
3. Mod Env: high Amount, fast Decay.
4. Velocity → Mod Env max level.
5. Portamento On with short time. Retrig off for legato slides.

### Quick start: wobble bass

1. Osc 1 = Ramp.
2. LFO: Triangle, Rate ~3 Hz, route to filter.
3. Mod Wheel → LFO intensity.
4. Filter: LP24, FREQ 40%, RES 60%, Drive halfway.
5. Player rides the Mod Wheel for the wobble effect.

### Tips & Pitfalls

- **High Resonance is loud.** Manual explicitly cautions about volume spikes. Use Drive to compensate or back off.
- **LFO requires routing first.** LFO must be enabled to oscillator or filter section before Mod Wheel intensity does anything.
- **CV connections don't save with patches.** Embed in Combinator to preserve routing.
- **Monophonic by design.** Cannot play chords. If you try, it'll voice-steal — that's the point.

Cross-ref: Need polyphony? Go to **Subtractor**. Need a more elaborate mono bass with morphing/layering? **Polytone** in Mono Retrig + Single layer mode, or **Thor** with poly=1.

---

## Choosing Between Them: Decision Cheatsheet

| Need | Use |
|---|---|
| Fast classic poly synth, low CPU | Subtractor |
| Fast mono bass | Monotone |
| Lush layered analog pad, intuitive controls | Polytone |
| Morphing between two timbres in real time | Polytone (Morph mode) |
| Granular/scrubbed evolving texture | Malstrom |
| Complex modulation routing, audio-rate FM, custom matrix | Thor |
| Mix synthesis paradigms (e.g., FM + sample + analog) in one patch | Europa or Thor |
| Drawable custom envelopes/waveforms | Europa |
| Load your own samples as oscillator material | Europa |
| Spectral-domain filtering | Europa |
| Self-oscillating filters as additive sources | Thor |
| Per-step modulation curves in built-in sequencer | Thor |
| Vintage analog drift simulation | Polytone (Age) |
| Phase-offset PWM/sync without dedicated controls | Subtractor |
| Filter morphing through filter types continuously | Polytone (state variable) |

## Universal Pitfalls (apply to all)

1. **CV connections don't save in patches** — every Reason synth shares this. If you're routing Matrix/Pulsar/external CV to a synth's inputs and want to keep it, **wrap the synth in a Combinator** and save the Combi.
2. **Resonance + envelope amount = volume spikes**, especially with self-oscillating filters (Ladder, MFB, Comb). Mind your levels.
3. **Polyphony is voiced on demand, not pre-allocated.** Setting max polyphony high has zero CPU cost until those voices play. Don't set it artificially low for "performance."
4. **Init patches are minimal.** They start with Osc 1 → filter → amp env audible. Anything else (FM, mod env routing, LFO destinations) needs explicit assignment.
5. **Mono synths/modes don't retrigger on legato unless told to.** Use the Retrig button (Monotone) or Mono Retrig key mode (Thor/Polytone) if you want fresh envelopes per note.
6. **Drive parameters (filter Drive, Amp Drive) compound with high resonance.** A low FREQ + high RES + high Drive on any of these synths can produce extreme levels.
