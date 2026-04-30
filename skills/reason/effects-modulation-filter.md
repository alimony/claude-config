# Reason 13: Modulation, Filter & Gate Effects
Based on Reason 13.4 documentation.

This skill covers four of Reason's most powerful "motion" effects: devices that don't just process sound, they *animate* it. They share DNA — every one of them sync to host tempo, every one of them exposes CV in/out for cross-device modulation, and every one of them rewards thinking rhythmically about effect parameters rather than statically.

## Comparison table

| Device | Role | Tempo-synced | CV inputs | CV outputs | Best for |
|---|---|---|---|---|---|
| **Alligator** | Triple-band pattern gate (HP/BP/LP) with per-band FX | Yes — 64 patterns + LFO + delay sync to song tempo, plus ReGroove shuffle | 3× Gate In, 3× Filter Freq CV, LFO Rate CV | 3× Gate Out, LFO CV Out | Beat-slicing pads, rhythmic chops, dub/glitch reshaping of full mixes |
| **Pulveriser** | Compressor + distortion + filter combo with LFO + envelope follower | Yes — Tremor LFO sync, sequencer-locked rate divisions | Squash, Dirt, Filter Freq, Tremor Rate, Volume, Follower (replaces internal); audio-rate inputs for Filter & Volume | Follower CV, Tremor CV | Pumping bass, lo-fi crunch, parallel-compressed drums, dynamic envelope-driven movement |
| **Sweeper** | LFO + envelope-driven phaser/flanger/filter modulator | Yes — LFO and envelope curves sync to sequencer (8 bars to 1/64) | Frequency, Feedback/Reso, Spread, Dry/Wet, Trig Envelope | LFO, Fol/Env, Trigger | Insert sweeps on synths, rhythmic phasers, dubstep filter rides, audio-followed motion |
| **Synchronous** | Rhythmic curve-based modulator over Distortion + Filter + Delay + Reverb | Yes — entire device is built around 2-bar (or 1/4-bar) sequencer-locked loops | 3× Curve In, 3× Freeze In, Master Level | 3× Curve Out, 3× Curve Out Inverted | EDM/dubstep filter sweeps, animated FX automation, bar-locked stutter and pumping |

## Quick mental model

- **Alligator** = a *programmed pattern* device. It thinks in 16th notes and gate triggers.
- **Pulveriser** = a *signal processor* with motion bolted on. It thinks in dB and dirt.
- **Sweeper** = a *sweeper* (literally) — one filter/phaser, but the LFO/envelope is the star.
- **Synchronous** = an *automation engine in a box*. You draw curves, they drive everything.

If you find yourself fighting one of them, ask: "am I using the right brain?" Don't try to draw delicate curves on Alligator (use Synchronous), and don't reach for Synchronous when you need a bandpass-then-lowpass split (use Alligator).

---

## Alligator — Triple Filtered Gate

A three-channel parallel gate with one HP band, one BP band, one LP band, each with its own gate, filter, distortion, phaser send, and delay send. It has a built-in 64-pattern step sequencer that drives the three gates, but you can bypass that and drive the gates from CV, MIDI notes, or Matrix sequencers. It is the device you reach for when you want to *chop* something rhythmically.

### Architecture

The signal splits three ways at the input. Each channel has the same chain: gate → amp envelope → filter → filter envelope → drive → phaser send → delay send → channel pan/volume. The three channels recombine with the dry signal (which has its own pan, volume, and "dry ducking" — an inverted amp envelope that lets the gates appear to *carve out* of the dry signal). One global delay and one global phaser are shared. One global LFO modulates all three filter frequencies. One filter envelope is shared across all three channels.

The three channels are hard-wired to filter types:
- **Channel 1**: High Pass
- **Channel 2**: Band Pass
- **Channel 3**: Low Pass

So Alligator is essentially a 3-band crossover where each band has its own gate. That mental model is the key to using it well.

### Pattern sequencer

64 built-in patterns, mostly 2 bars long, displayed as a dot grid showing all three gate tracks. Patterns sync to song tempo. Resolution scales playback speed (1/16 default; 1/4, 1/8, 1/32 etc. available). Shift offsets the pattern by ±16 steps. Shuffle applies the global ReGroove mixer settings (works best at 1/16 resolution).

The Pattern On switch is critical: when on, the internal patterns drive the gates. When off, only CV/MIDI input opens the gates. **If you want pure CV control, turn Pattern Off.** Otherwise the sources combine and you'll get patterns leaking through.

### Front panel parameters (all of them)

**Gate / Amp Envelope**
- Manual Gate Trig buttons (override pattern)
- Amp Env Attack / Decay / Release — shapes the gate volume contour
- Filter Env Attack / Decay / Release — shapes the per-channel filter envelope (shared)

Note: Filter Env Release only audible if Amp Env Release is high enough to keep the gate open through the release.

**Per-channel filter**
- Filter On (just the filter; gate stays active)
- Frequency, Resonance
- LFO Amount (bipolar), Envelope Amount (bipolar)

**Per-channel effects**
- Drive Amount (distortion)
- Phaser Amount (send to global phaser)
- Delay Amount (send to global delay, post-volume)

**Per-channel mix**
- Pan, Volume

**Global LFO**
- Waveform: 9 options (sine, triangle, square, random, stepped variants)
- Frequency
- Sync (musical values when on)

**Global delay**
- Time (up to 2/4 bars synced, 1 second free)
- Sync, Feedback, Pan

**Global phaser**
- Rate, Feedback

**Dry / master**
- Dry Ducking (inverted amp env on dry signal — only audible if Dry Volume > 0)
- Dry Pan, Dry Volume
- Master Volume

### Sync / tempo

- Patterns: locked to song tempo. Resolution scales (1/4 to 1/64).
- LFO: free-run in Hz, or musical values when Sync is on.
- Delay: free in seconds, or musical values when Sync is on.
- Shuffle: pulls from the ReGroove mixer global setting.

### Modulation sources / CV

**Inputs (rear)**
- 3× Gate In — CV ≥7 opens the gate; velocity-sensitive (higher CV = louder). Auto-routes from Matrix when selected.
- 3× Filter Freq CV — modulates each channel filter
- LFO Rate CV — modulates the global LFO

**Outputs (rear)**
- 3× Gate Out — sends current gate values regardless of source (great for triggering other devices in lockstep)
- LFO CV Out — global LFO available for external use
- Separate Channel Outputs — three individual outputs *post* channel volume but *pre* master volume. **Connecting a separate output removes that channel from the main mix.** Useful for sending each band to a different destination (Kong, separate reverb, etc.).

**MIDI**
- F#1 = HP gate, G#1 = BP gate, A#1 = LP gate (all velocity-sensitive)

### Quick recipes

```
Recipe 1: Trance gate on a pad
- Alligator after pad
- Pattern On, choose a 1/16 pattern with all three channels active
- Lower all three filter Frequencies until they overlap roughly, low Resonance
- Long Amp Env Release (~200ms) for smooth tails
- Add Delay 1/8 with Feedback ~30%, Sync on
- Result: classic chopped pad with rhythmic delay tail
```

```
Recipe 2: Three-band beat splitter
- Alligator on a drum loop
- Pattern Off
- Use three Matrix sequencers connected to Gate In 1, 2, 3 (auto-routes)
- Program: matrix 1 hits kicks (LP-band passes lows on Channel 3)
  Wait — Channel 1 is HP, Channel 3 is LP, so:
    Matrix 1 → Gate 1 (HP) for hats
    Matrix 2 → Gate 2 (BP) for snares/mids
    Matrix 3 → Gate 3 (LP) for kicks
- Different patterns per band for polyrhythmic groove
```

```
Recipe 3: Live keyboard performance
- Pattern Off
- Play F#1, G#1, A#1 from a controller — velocity controls level
- Each band gets its own filter envelope shape and drive amount
- Cross-channel volume balancing acts as a real-time 3-band remix tool
```

```
Recipe 4: Whole-mix remix
- Alligator on master bus (use sparingly!)
- Pattern On with sparse pattern
- Heavy Dry Ducking + Dry Volume up so the dry "punches through" between gate hits
- Master Volume down a few dB to compensate for level boost from drives/phasers
```

### Pitfalls

- **Phase issues across the three bands.** Because HP, BP, LP are parallel filters, their crossovers can produce comb-filter cancellation when their frequency ranges overlap or when delays differ. If you hear hollow/phasey artifacts, separate the band frequencies more cleanly, or solo bands to verify.
- **Pattern + CV double-trigger.** If you wired up CV gates and still hear pattern triggers, you forgot to turn Pattern Off.
- **Filter Env Release inaudible.** Caused by Amp Env Release closing the gate before the filter env releases. Raise Amp Env Release.
- **Dry Ducking does nothing.** Dry Volume is at zero. Raise it.
- **Master Volume vs. separate outputs.** Separate channel outs ignore Master Volume. Don't expect master gain to balance external routing.
- **Shuffle feels off at non-1/16 resolutions.** Optimized for 1/16; expect weirdness at 1/32 or 1/4.

---

## Pulveriser — Compressor / Distortion / Filter / Tremor

A "demolition" multi-effect: a compressor (Squash) feeding a distortion (Dirt) feeding a filter, with two parallel modulation engines (Tremor LFO, Follower envelope follower) that can drive Filter Freq, Volume, and even Tremor Rate. The whole thing has a Blend knob for parallel processing.

### Architecture

Two routing modes:

1. **Squash → Dirt → Filter** (default): compress, then distort, then filter. The classic "smash-and-shape" order.
2. **Filter → Squash → Dirt**: filter first defines what hits the compressor and distortion. Use this when you want the distortion to react only to a specific frequency band.

Tremor and Follower live outside the audio path — they generate CV that modulates the audio sections.

### Front panel sections

**Squash (compressor)**
- Squash knob — single combined control over ratio, threshold, makeup gain. "Musical" rather than surgical.
- Release — short release + high Squash = the canonical pumping sound.

**Dirt (distortion)**
- Dirt — drive amount
- Tone — low-pass filter on the distortion (fully clockwise = open)

**Filter**
- 5 types: Bypass, Lowpass 24, LP12+Notch, Bandpass, Highpass 12, Comb
- Frequency (cutoff or center)
- Peak (resonance)

**Tremor (LFO / tremolo)**
- Rate — extremely wide range; can hit audio rate for FM/AM territory
- Waveform: 9 options (sine, triangle, square, random, non-linear, stepped variants)
- Sync — locks LFO to sequencer
- Spread — 180° phase shift between channels for stereo motion
- Lag — smooths the LFO signal (essential when modulating Rate in Sync mode)
- Modulation Amount knobs (bipolar):
  - To Filter Frequency
  - To Volume (wet only — dry is unaffected by Tremor's volume mod, which is what makes Blend useful for parallel motion)

**Follower (envelope follower)**
- Trig — manual gate
- Threshold — input level that triggers; red lamp shows CV output level
- Attack — response to rising input. Note: can only *increase* attack relative to input, never sharpen it.
- Release — fall time. Same caveat: only lengthens, never shortens.
- Modulation Amount knobs (bipolar):
  - To Tremor Rate (envelope-controlled tremolo speed!)
  - To Filter Frequency (auto-wah territory)

**Blend / Volume**
- Blend — dry/wet mix; central to parallel-compression workflows
- Volume — total output level

### Sync / tempo

- Tremor Sync mode: Rate knob switches between musical divisions, LFO chases sequencer playhead.
- **Modulating Tremor Rate while in Sync mode produces noise** as it jumps resolutions. Cure: increase Lag to smooth the transitions.
- Follower has no sync — it follows audio, full stop.

### Modulation / CV

**CV Inputs (rear)**
- Squash, Dirt, Filter Frequency, Tremor Rate, Volume
- Follower CV In — if patched, *replaces* the internal envelope follower, but Attack/Release on the panel still shape the incoming CV
- **Audio-rate modulation inputs** for Filter Frequency (filter FM!) and Volume (amplitude modulation / ring-mod-ish effects)

**CV Outputs (rear)**
- Follower (envelope CV — useful for sidechaining other devices to the Pulveriser's input dynamics)
- Tremor (LFO CV — share the LFO with anything else)

**Sidechain pattern.** Pulveriser doesn't have a dedicated sidechain audio input, but you can fake one: send your sidechain source into the Follower CV In (after a Spider Audio → CV trick or via routing the source into another Pulveriser and patching its Follower out). Or — easier — put Pulveriser on the bus you want pumped, and use a separate envelope follower fed from the kick to its Squash CV input.

### Quick recipes

```
Recipe 1: Pumping bass
- Pulveriser on bass
- Squash high, Release short, Blend ~70% wet
- Filter: LP24, Frequency mid-range
- Tremor: Sync on, Rate 1/4, Sine wave
- Tremor → Volume amount: heavy negative (creates pumping on the off-beat)
- Result: side-chain-style bass duck without an actual sidechain
```

```
Recipe 2: Auto-wah from envelope
- Pulveriser on a clavinet/guitar/synth lead
- Filter: BP, Peak high
- Follower → Filter Frequency: heavy positive
- Threshold low so quieter notes trigger
- Tremor disabled
- Result: classic envelope-follower wah, plays itself
```

```
Recipe 3: Lo-fi crunch
- Squash → Dirt → Filter routing
- Squash medium, Dirt high, Tone closed (~9 o'clock)
- Filter: Lowpass 24, Frequency ~1.5kHz
- Blend ~60% — keeps some of the original cleanliness
- Result: warm, broken, "tape-saturation-ish" texture
```

```
Recipe 4: Comb-filter pad movement
- Pulveriser on pad
- Filter: Comb, Peak medium-high
- Tremor: Sync on, Rate 1/2, Triangle, Spread on
- Tremor → Filter Frequency: medium positive
- Follower → Tremor Rate: small positive (pad dynamics speed up the modulation)
- Result: pad that breathes and pitches with input dynamics
```

### Pitfalls

- **Feedback / runaway gain.** Heavy Squash + heavy Dirt + high Peak on the filter = output level explosion. Always set Volume conservatively, watch the master meters.
- **Tremor Rate noise in Sync mode.** Add Lag. Always.
- **Follower can't sharpen incoming dynamics.** If your kick triggers the follower but the resulting envelope feels too soft, you cannot make the attack faster than the audio's natural attack. Pre-process with a transient shaper or use the Trig button programmatically.
- **Blend not mixing dry properly.** Tremor's Volume modulation only affects the wet path. If your dry signal isn't pumping, that's by design — increase Blend toward wet, or duplicate the device.
- **Routing mode confusion.** Filter → Squash → Dirt sounds dramatically different from Squash → Dirt → Filter. If your distortion sounds wrong, check which routing you're in.
- **Audio-rate FM aliasing.** Patching audio into Filter Frequency CV at audio rate produces FM, but the filter design isn't band-limited for this — expect aliasing if you push it.

---

## Sweeper — Modulation Effect

A focused phaser/flanger/filter device with extremely flexible modulation. The "personality" lives in the LFO and the custom envelope you can draw. It's like a Synchronous Lite for sweeping a single effect, with much better filter quality.

### Architecture

Audio in → routing (Stereo or Dual Mono) → Phaser / Flanger / Filter → Volume → out. In parallel, three modulation sources (LFO, custom Envelope, Audio Follower) modulate the effect's Frequency and Volume parameters.

**Routing**
- **Stereo**: L+R sum at input, then process. Mono input becomes stereo output.
- **Dual Mono**: L and R processed independently — useful for asymmetric stereo sweeps.

### Effect modes

**Phaser**
- 1–40 all-pass stages (each adds one notch in the spectrum)
- Frequency 37.6 Hz – 16.17 kHz
- Bandwidth, Feedback
- Polarity button — inverts spectrum (notches become peaks)
- Mute Dry — kills dry signal, leaves only the phased signal (creates tremolo-like artifacts)

**Flanger**
- Comb-filter based
- Frequency 37.6 Hz – 16.17 kHz (controls delay time)
- Feedback intensifies resonance
- Polarity, Mute Dry as above

**Filter**
- Filter types from Europa: SVF HP/LP/BP 12dB, SVF Notch, Ladder LP 24dB, MFB LP/HP 12dB, MFB LP/HP 24dB, K35 LP 12dB
- Drive — overdrive/saturation
- Frequency, Resonance
- In Notch type, Resonance controls notch width

### Global controls

- Volume (master output)
- Spread — stereo detuning, behavior varies per effect mode
- Dry/Wet — wet mix
- LFO → Freq (bipolar)
- Mod → Freq (bipolar; from envelope or follower)
- LFO → Volume (bipolar)
- Mod → Volume (bipolar)

### LFO

- 10 waveforms: sine, triangle, pulse, random, slope, stepped, decay variants
- Manual rate: 0.05–50 Hz
- Sync rate: 8 Bars to 1/64
- Rate Mod — modulates the LFO rate via envelope/follower; in Sync mode this jumps between sync divisions

### Envelope Modulator

A drawable envelope curve with preset library (ADSR, etc.). Three modes:

1. **One-shot**: Plays once when triggered.
2. **Loop**: Acts as a custom-shape LFO, syncs to sequencer.
3. **Audio Trig**: Triggered when audio crosses threshold. In one-shot mode, max one cycle per trig; in loop mode, restarts on trig.

**Editing**
- Standard mode: drag points and shape segments.
- Edit mode: lock changes to *level only* — useful for stepped/sequencer-style presets where horizontal positions stay fixed.
- Free-form: hold Ctrl/Cmd and drag to add points continuously (drawing a line).

### Audio Follower

- Tracks input audio amplitude
- Gain In — attenuates/amplifies the modulation signal
- Attack, Release — same caveats as Pulveriser's follower (only lengthens, never shortens)
- Real-time level display

### Sync / tempo

- LFO syncs to bar-relative divisions (8 Bars to 1/64).
- Envelope (in Loop mode) syncs to sequencer timeline.
- Audio Follower has no sync — it follows audio.

### Modulation / CV

**CV Inputs (rear)**
- Frequency, Feedback/Reso, Spread, Dry/Wet — all bipolar with attenuation
- Trig Envelope — zero-to-positive trigger (works alongside Audio Trig)

**CV Outputs (rear)**
- LFO (bipolar)
- Fol/Env — follower/envelope output (unipolar)
- Trigger — unipolar trig from the Audio Trig function

**Audio I/O**
- Input L & R (mono input → connect L only; processed and output stereo)
- Output L & R

### Quick recipes

```
Recipe 1: Classic synced phaser sweep
- Sweeper after a synth pad
- Mode: Phaser, Stages 8, Feedback ~50%
- LFO: Sync on, Rate 4 Bars, Triangle
- LFO → Freq: heavy positive
- Result: slow, classic 4-bar phaser sweep
```

```
Recipe 2: Dubstep/EDM filter ride
- Sweeper on a synth bass
- Mode: Filter, Type Ladder LP 24dB, Drive moderate
- Custom Envelope in Loop mode, drawn as a 1-bar swooping curve
- Mod → Freq: heavy positive
- Sync envelope to 1 Bar
- Result: bar-locked filter ride that can be redrawn live
```

```
Recipe 3: Audio-followed flanger
- Sweeper on a guitar
- Mode: Flanger, Polarity inverted
- Audio Follower active, Attack short, Release medium
- Mod → Freq: positive
- LFO → Freq: small (slight always-on motion)
- Result: flange depth keyed to playing intensity
```

```
Recipe 4: Mono-to-stereo widener
- Sweeper after mono synth
- Stereo routing
- Mode: Phaser
- Spread: high
- Dry/Wet: 50% (keep dry mono, phaser stereo)
- Result: instant width without losing mono compatibility
```

### Pitfalls

- **Self-oscillating filters.** Ladder LP 24dB, MFB LP/HP 24dB, K35 LP 12dB self-oscillate at high Resonance and can produce extreme output. Watch master gain.
- **Line curves ignore Phase.** Same as Synchronous — only waveforms respond to phase shifts; hand-drawn lines do not.
- **Stereo vs. Dual Mono confusion.** A mono input with Dual Mono routing leaves R untouched. If you hear nothing on the right, switch to Stereo.
- **Mute Dry tremolo trap.** Mute Dry on Phaser produces a tremolo-like artifact that's easy to mistake for a bug. It's deliberate.
- **Audio Trig latching.** If Audio Trig keeps re-firing, raise the threshold or use envelope Loop mode instead.

---

## Synchronous — Timed Effect Modulator

The most "compositional" of the four: an effects rack (Distortion + Filter + Delay + Reverb) wrapped in a curve-drawing engine. You draw up to three independent modulation curves (yellow/cyan/magenta), each looping over 1, 2, or 4 bars, and route them to any combination of the effect parameters. It's automation-as-a-device. EDM/dubstep producers live in this thing.

### Architecture

Audio in → Distortion → Filter → Delay → Reverb → Level → out. Three modulation curves (Curve 1, 2, 3) running on independent loop lengths control any subset of the effects' parameters. Each parameter has a dedicated mod knob whose color reflects which curve is currently selected for editing. Multiple curves can hit the same parameter with different amounts and polarities.

### Curves

- 3 curves (color-coded yellow / cyan / magenta)
- Each curve has its own loop length (set with triangular Loop Locators)
- Each curve can be Frozen (FRZ button — holds current value) or Killed (mutes curve while preserving content)
- Phase shifts are *per-curve* but only affect waveform-drawn segments; line/free-drawn segments ignore Phase (use Master Offset for those)

### Speed modes (per curve, sets loop length and grid)

| Speed | Display | Grid |
|---|---|---|
| x1 (default) | 2 bars | 1/16 |
| x0.5 | 4 bars | 1/8 |
| x2 | 1 bar | 1/32 |

The grid is the **shortest editable interval**. If you need finer detail than 1/16, switch to Speed x2.

### Drawing tools

- **Stepped Line** — fixed levels between grid lines (jagged)
- **Linear Line** — straight interpolation between points
- **Sine, Triangle, Sawtooth, Positive Sawtooth** waveform generators
- **Free** — unrestricted drawing between grid lines
- **Rate** for waveforms only: 1/32, 1/16, 1/8, 1/4, 1/2, 1/1

### Front panel parameters

**Display section**
- Phase (0–360°, waveforms only)
- Master Offset (shifts *all* curves' start position; works on lines too)
- Dim (visibility of unselected curves)
- Loop Locators (per-curve loop length)
- FRZ buttons, Kill buttons (per curve)

**Distortion**
- Amount (0 = clean)
- Character
- Type: Dist, Ring Mod, Lo-Fi
- Post Filter button (routes distortion *after* the filter)
- On/Off

**Filter**
- Frequency, Resonance
- Lag (smoothing for fast modulation — essential for clean sweeps)
- Type: HP 12dB, BP 6dB, LP 24dB, Comb
- On/Off

**Delay**
- Amount, Time
- Feedback
- Keep Pitch (no pitching artifacts on time changes)
- Ping Pong, Sync, Roll (frozen/stutter mode)
- Pan
- Send/Return switch
- On/Off

**Reverb**
- Amount, Decay, Size, Damp
- Send/Return switch
- On/Off

**Level**
- Level (−∞ to +12 dB)
- In/Out switch (where in the chain Level applies)

**Master**
- Dry/Wet (0 = bypass)
- Master Level (−∞ to +12 dB)

### Sync / tempo

The whole device is built around bar-locked modulation. Curves loop in 1, 2, or 4 bars depending on Speed. Delay times sync to divisions when Sync is on. Master Offset can shift the entire performance ±32 sixteenth notes (in Speed x1).

### Modulation / CV

**CV Inputs (rear)**
- Curve 1/2/3 (bipolar; *added* to the corresponding internal curve; per-input attenuation)
- Freeze 1/2/3 (CV > 0 freezes the curve)
- Master Level CV In (with attenuation)

**CV Outputs (rear)**
- Curve 1/2/3 (positive unipolar, follows curve shape)
- Curve 1/2/3 Inverted (negative unipolar)

The Inverted outputs are the secret weapon: patch a curve to one parameter normally and to another via Inverted for "mirrored" modulation (one parameter goes up while another goes down).

### Quick recipes

```
Recipe 1: Dubstep filter ride + delay throw
- Synchronous on a synth bass/lead
- Filter LP 24dB, Resonance ~30%, Lag medium
- Curve 1: drawn as a slow rising sawtooth over 4 bars (Speed x0.5)
  - Routed to Filter Frequency, heavy positive amount
- Curve 2: linear line that spikes only on bar 4 beat 4
  - Routed to Delay Amount, positive
- Sync delay 1/8 dotted, Feedback ~40%
- Result: filter sweeps over 4 bars with a delay throw on the last beat
```

```
Recipe 2: Animated reverb gate
- Synchronous on a vocal/snare
- Reverb in Send mode, Decay long, Size large
- Curve 1: 1/16-stepped pattern alternating high/low
  - Routed to Reverb Amount, full positive
- Result: classic gated reverb pattern, perfectly bar-locked
```

```
Recipe 3: Polyrhythmic motion
- Curve 1 loop = 2 bars, Curve 2 loop = 3 bars (use Locators)
  - Both routed to different params
- Pattern repeats every 6 bars (LCM)
- Adds long-form variation without manual automation
```

```
Recipe 4: Mirrored modulation
- Curve 1 → Filter Freq (positive)
- Curve 1 Inverted CV Out → Reverb Amount via patch cable
- As filter opens, reverb closes; as filter closes, reverb opens
- Built-in "tension and release" pump
```

### Pitfalls

- **Phase doesn't shift Line curves.** Caught me out. If you need to shift a hand-drawn line, use Master Offset.
- **Grid is your editing limit.** In Speed x1 you cannot edit finer than 1/16. If you can't draw the detail you want, switch to Speed x2 (1/32 grid, 1-bar display) and accept the shorter loop.
- **Filter modulation zipper noise.** Fast curve changes on Filter Frequency without Lag will zipper. Lag fixes it; too much Lag smooths out intentional steps. Tune to taste.
- **Frozen curves still output.** FRZ holds the *current* value as a constant CV — it doesn't disable modulation. Use Kill to silence the curve.
- **Bipolar curves reverse polarity.** A curve value below zero with a positive mod amount applies *negative* modulation. If your filter goes the "wrong way," check for negative regions in the curve.
- **Display section can't be control-mapped.** Master Offset, Speed, Phase, Loop Locators, FRZ/Kill, and the Mod knobs accept *automation* (parameter automation lanes / record-during-playback) but not right-click control mapping. If you want hardware control of those, you have to record automation.
- **Send/Return switches change everything.** Reverb in Send mode plus modulating Reverb Amount = gated/reversed-feel reverb. In Return mode, modulating Amount affects the wet return only. Different sound entirely. Read the panel state before troubleshooting.

---

## Order of effects: combining them

These four devices stack beautifully if you respect their personalities. A few rules of thumb:

1. **Alligator first** when you want rhythmic chops to be the *gateway* into other processing. Putting Alligator after a Pulveriser means the gates carve up an already-processed signal — sometimes useful, but you lose the pre-gate dynamics that follower-based devices want to track.

2. **Pulveriser before Sweeper / Synchronous** for tonal shaping. The compression and distortion benefit from a clean, pre-modulation signal. Modulating after Pulveriser means the Sweeper/Synchronous filter rides on a fully-shaped tone.

3. **Sweeper or Synchronous last** for the "sweep on top" feel. They're the icing.

4. **Two cases where you flip the order:**
   - Synchronous *before* Pulveriser when you want the modulation to *drive* the compressor (e.g., curve hits Pulveriser's Squash CV input → compressor pumps with the curve).
   - Sweeper *before* Alligator when you want each Alligator band to chop an already-swept signal (very dub-techno).

### Cross-device CV patterns

- **Alligator's Gate Out → Pulveriser's Follower Trig**: every gate triggers a Pulveriser envelope event.
- **Alligator's LFO Out → Sweeper's Frequency CV**: share one LFO across two devices for synchronized motion.
- **Synchronous's Curve 1 → Pulveriser's Squash CV**: programmed, bar-locked sidechain pumping driven by a hand-drawn curve.
- **Sweeper's Fol/Env Out → Alligator's Filter Freq CV**: audio-followed filter movement on the Alligator bands.
- **Pulveriser's Follower Out → Synchronous's Curve 1 CV In**: combine envelope-followed CV *with* the drawn curve (CV adds bipolar, attenuated).

### Suggested chain templates

```
Template A — "EDM bass"
Synth → Pulveriser (LP24, Squash, Tremor sync 1/8) → Synchronous (Filter ride curve, Delay throw curve) → Master

Template B — "Chopped pad"
Pad → Alligator (1/16 pattern, LP24 on Channel 3, drive) → Sweeper (Phaser, slow LFO 8 bars) → Master

Template C — "Dub vocal"
Vocal → Synchronous (Reverb in Send, gated by Curve) → Sweeper (Filter, audio-follower) → Pulveriser (parallel Blend ~30%) → Master

Template D — "Drum bus mangler"
Drums → Alligator (sparse pattern, dry ducking) → Pulveriser (Filter→Squash→Dirt routing) → Synchronous (1-bar curve on Distortion Amount) → Master
```

---

## Cheat sheet: reach for which?

- "I want it to chop on every 16th." → **Alligator**
- "I want it to pump like a sidechain." → **Pulveriser** (Tremor → Volume) or **Synchronous** (curve → Master Level)
- "I want it to sweep over 4 bars." → **Sweeper** or **Synchronous**
- "I want one knob that smashes everything." → **Pulveriser** (Squash + Dirt)
- "I want the same sound to do something different in bar 4." → **Synchronous** (longer loop than 1 bar)
- "I want the effect to react to playing dynamics." → **Pulveriser Follower** or **Sweeper Audio Follower**
- "I want a filter that self-oscillates and screams." → **Sweeper** Ladder LP 24dB
- "I want three filters at once." → **Alligator** (parallel HP/BP/LP)
- "I want to draw my own LFO shape." → **Sweeper** Envelope Modulator (loop mode) or **Synchronous** (any curve)
- "I want polyrhythmic FX motion." → **Synchronous** (different loop lengths per curve)

## Final practical note

All four devices have CV inputs that are *bipolar* and *attenuated*. That means: external CV can push parameters in either direction, and the in-jack attenuation knob on the rear is your fine-tune. Whenever you patch CV between these devices and the modulation feels weak, check the rear attenuation first — it ships at a sensible default but is rarely 100%.
