# Reason 13: Dynamics & EQ Effects
Based on Reason 13.4 documentation.

This skill covers Reason 13's built-in dynamics processors and equalizers: the Channel Dynamics, Channel EQ, Master Bus Compressor, and the four M-Class mastering devices. All of these exist as both Main Mixer channel-strip components and as standalone rack devices (and are surfaced as VST3 plugins for use in other DAWs).

## Device Comparison

| Device | Role | Sidechain | Typical placement | Character |
|---|---|---|---|---|
| **Channel Dynamics** | Compressor + Gate/Expander, per-channel | External SC L/R inputs | Channel insert (or rack) on individual tracks | Clean, surgical, mixer-style |
| **Channel EQ** | 4-band EQ + HPF + LPF, per-channel | None (audio); 6 CV inputs for modulation | Channel insert on individual tracks | Two voicings (Normal / E mode) |
| **Master Bus Compressor** | SSL G-style stereo bus comp | External SC L/R inputs | Master bus (or drum bus / submix) | Glue, "fairy dust," punchy bus comp |
| **M-Class Equalizer** | Mastering EQ | None (audio) | First in mastering chain | Clean, parametric, with Lo Cut |
| **M-Class Stereo Imager** | 2-band stereo width | None | After EQ in mastering chain | M/S-style, frequency-dependent |
| **M-Class Compressor** | Mastering compressor | External SC L/R + Solo SC | After Imager in mastering chain | Soft Knee, Adapt Release |
| **M-Class Maximizer** | Brick-wall limiter / loudness | None | LAST in mastering chain | Look Ahead + Soft Clip |

**Order of effects on a master bus (Mastering Combi):** EQ → Stereo Imager → Compressor → Maximizer. The Maximizer is always the last device before the Hardware Interface output.

---

## Channel Dynamics (Compressor + Gate/Expander)

### Role
A per-channel dynamics processor that mirrors the dynamics section of the Main Mixer channel strip. Combines a soft-knee compressor and a gate/expander in one device. Designed for taming individual tracks (vocals, drums, bass) before they hit the bus.

### Best uses
- Taming vocal dynamics with transparent compression
- Removing mic bleed or noise on drum tracks (Gate)
- Subtle level evening on bass DI
- Sidechain ducking / rhythmic gating effects (synth pad keyed by drum loop)
- Parallel compression via the Mix knob

### Compressor section parameters

| Parameter | Range | What it does |
|---|---|---|
| **Threshold** | -52 dB to 0 dB | Level at which compression begins. Lower = more compression. |
| **Ratio** | 1:1 to ∞:1 | How hard the signal is squashed above threshold. 4:1 = 4 dB in produces 1 dB out. ∞:1 = limiting. |
| **Release** | 100–1000 ms | How fast the compressor lets go after the signal drops below threshold. |
| **Fast (Peak) Mode** | On/Off | Switches the compressor into a peak-detecting limiter with a fixed 3 ms attack. Use for transient-heavy material (drums). When off, the comp uses RMS-style soft-knee detection. |
| **Gain Reduction Meter** | LED | Shows real-time GR in dB. Aim for the ranges in recipes below. |

Note: Channel Dynamics has **automatic makeup gain** — you don't dial it in manually like a 1176. There is no "knee" knob; the compressor is soft-knee unless Fast/Peak mode is engaged.

### Gate / Expander section parameters

| Parameter | Range | What it does |
|---|---|---|
| **Threshold** | -52 dB to 0 dB | Level below which gating/attenuation kicks in. |
| **Range** | 0 to -40 dB | How much attenuation is applied below threshold. 0 dB = gate has no effect. -40 dB = full mute (Gate). Anything in between = Expander behaviour (gradual reduction, like an "inverted compressor"). |
| **Hold** | 0–4000 ms | How long the gate stays open after the signal drops below threshold. Prevents chatter on decaying material. |
| **Release** | 100–1000 ms | Fade time from open to closed once Hold expires. |
| **Fast Mode** | On/Off | Tightens the open/close response to ~100 µs per 40 dB. Use for snappy percussion. |

**Gate vs Expander:** Range = -40 dB makes it a hard gate (chops below threshold). Range between 0 and -40 dB gives expander behaviour, which is musically gentler — good for cleaning up a noisy vocal without the "tomb door" effect of a strict gate.

### Global controls
- **Input Gain:** ±18 dB. Pre-comp/gate level.
- **Mix:** 0–100% dry/wet. <100% enables parallel compression. The Gate/Expander is also affected by Mix.

### Sidechain
- **Sidechain Inputs:** Stereo L/R on the rear panel.
- **Sidechain button + Connected LED:** Front-panel toggle that routes the SC inputs to the compressor and/or gate detector. The LED indicates an active patch.
- **Use case:** Route a kick into the SC to duck a synth pad; route a drum loop into the SC of a Gate on a held pad to chop it rhythmically.

### CV outputs
- **Compressor Gain Reduction CV** — modulate other parameters with the comp envelope.
- **Gate Gain CV** — high when gate is open, low when closed. Useful for triggering envelopes synced to the gate.

### Recipes (Channel Dynamics)

```
Vocal compression (general pop)
  Threshold: ~-18 dB (aim for 3-6 dB GR)
  Ratio:     3:1 to 4:1
  Fast:      Off (smooth, RMS-style)
  Release:   ~150 ms
  Mix:       100%
```

```
Vocal de-harshing / parallel
  Threshold: -25 dB (aggressive, 8-10 dB GR)
  Ratio:     6:1
  Fast:      Off
  Release:   100 ms
  Mix:       30-50% (parallel)
```

```
Snare / kick (transient)
  Threshold: -15 dB (3-5 dB GR)
  Ratio:     4:1
  Fast:      On (3 ms attack, peak detect)
  Release:   80-150 ms
  Mix:       100%
```

```
Bass DI (level even-out)
  Threshold: -20 dB (2-4 dB GR)
  Ratio:     2:1
  Fast:      Off
  Release:   200 ms
  Mix:       100%
```

```
Vocal noise gate (cleanup, gentle)
  Threshold: -45 dB
  Range:     -20 dB    (expander, not full gate)
  Hold:      200 ms
  Release:   400 ms
  Fast:      Off
```

```
Tom gate (tight)
  Threshold: -30 dB
  Range:     -40 dB    (full gate)
  Hold:      150 ms
  Release:   200 ms
  Fast:      On
```

```
Sidechain pad ducking (kick into pad)
  Comp Threshold: -25 dB
  Ratio:          6:1
  Fast:           On
  Release:        300 ms (set to taste with kick tempo)
  Sidechain:      On, fed from kick send
```

### Do this / Don't do this

**Do:**
- Use Fast (Peak) mode for drums and percussive material — its 3 ms fixed attack catches transients.
- Lean on the auto-makeup gain — Channel Dynamics handles output level for you.
- Use the Mix knob for parallel compression instead of routing to a separate channel.
- Use Range (-15 to -20 dB) for transparent expansion rather than a hard gate.

**Don't:**
- Set Ratio to ∞:1 on full mixes — Channel Dynamics is not a brickwall limiter. Use the Maximizer for that.
- Use a hard gate (Range -40 dB) on sustained material like vocals or pads — chatter on decay tails will be obvious.
- Pile on >8 dB GR in series with another compressor without checking for pumping.
- Stack the SC button on without anything patched — the "Connected" LED is the truth.

---

## Channel EQ

### Role
A per-channel equalizer mirroring the Main Mixer channel strip EQ. Two filters (HPF, LPF) plus 4 fully featured EQ bands (LF shelf, LMF parametric, HMF parametric, HF shelf). Identical specs to the channel-strip version.

### Best uses
- Per-track tonal shaping during mixdown
- High-pass everything that isn't bass/kick
- Surgical mid cuts (LMF/HMF parametric)
- Air boost on vocals (HF shelf)
- Warmth on bass (LF shelf, with Bell mode for surgical)

### Filter section

| Filter | Slope | Frequency range | Function |
|---|---|---|---|
| **High Pass (HPF)** | 18 dB/octave | 20 Hz – 4 kHz | Removes low frequencies. Steep slope = aggressive cutoff. Independent on/off. |
| **Low Pass (LPF)** | 12 dB/octave | 100 Hz – 20 kHz | Removes high frequencies. Independent on/off. |

The HPF is markedly steeper than the LPF (18 vs 12 dB/oct), which tends to suit how mixers actually use these — cutting rumble below vocals/synths, gentler high cuts.

### EQ band section

| Band | Type | Gain | Frequency | Q |
|---|---|---|---|---|
| **LF** | Shelf (switchable to peaking/Bell) | ±20 dB | 40 Hz – 600 Hz | (fixed when shelf; fixed Q when Bell) |
| **LMF** | Parametric (Bell only) | ±20 dB | 200 Hz – 2 kHz | 0.70 – 2.50 |
| **HMF** | Parametric (Bell only) | ±20 dB | 600 Hz – 7 kHz | 0.70 – 2.50 |
| **HF** | Shelf (switchable to peaking/Bell) | ±20 dB | 1.5 kHz – 22 kHz | (fixed when shelf; fixed Q when Bell) |

Each band has its own on/off switch. The LF and HF Bell switches convert the shelving filters into peaking filters with a fixed Q.

### Global controls
- **Gain:** ±18 dB output trim. Use for level compensation when doing drastic boosts/cuts.
- **Signal Meter:** Input/output level indication.

### Operating modes (Normal vs E)
- **Normal mode:** Higher gain narrows Q on the parametric bands (LMF/HMF). Sounds more "musical" — small boosts are wide, big boosts get focused.
- **E mode:** Constant Q across all gain settings. More predictable surgical work; "slightly different curve characteristics." Use for problem-solving cuts where you don't want the bandwidth to swing as you adjust gain.

### CV inputs (six, with trim pots)
- HPF Frequency
- LPF Frequency
- LMF Gain, LMF Frequency
- HMF Gain, HMF Frequency

Useful for automating filter sweeps or modulating the EQ from an LFO/sequencer.

### Recipes (Channel EQ)

```
Vocal cleanup + air
  HPF:  on, ~80 Hz
  LMF:  -2 dB at 250 Hz, Q 1.0   (mud cut)
  HMF:  +1.5 dB at 4 kHz, Q 1.2   (presence)
  HF:   +2 dB shelf at 12 kHz    (air)
  Mode: Normal
```

```
Kick drum punch
  HPF:  on, 30 Hz                (subsonic only)
  LF:   +3 dB shelf at 60 Hz     (weight)
  LMF:  -3 dB at 350 Hz, Q 1.5   (boxiness)
  HMF:  +2 dB at 4 kHz, Q 1.2    (beater click)
  Mode: Normal
```

```
Snare clarity
  HPF:  on, 120 Hz
  LMF:  -2 dB at 500 Hz, Q 1.5    (woof)
  HMF:  +3 dB at 5 kHz, Q 1.0     (crack)
  HF:   +2 dB shelf at 10 kHz
```

```
Acoustic guitar
  HPF:  on, 100 Hz
  LMF:  -2 dB at 300 Hz, Q 1.0    (boxiness)
  HMF:  +2 dB at 3 kHz, Q 0.8     (definition)
  HF:   +1.5 dB shelf at 10 kHz   (sparkle)
```

```
Bass DI / synth bass
  HPF:  on, 30 Hz
  LF:   +2 dB at 80 Hz (Bell on, surgical)
  LMF:  +1 dB at 800 Hz, Q 1.5    (growl, optional)
  HMF:  -1 dB at 2.5 kHz, Q 1.0   (de-fret-buzz)
  Mode: E
```

```
Surgical resonance cut
  Mode: E
  LMF or HMF: -8 dB, Q 2.5, sweep frequency to find offender
```

### Do this / Don't do this

**Do:**
- Use the HPF on most mix elements. 18 dB/oct is steep enough to clean up rumble without thinning the body.
- Use E mode for surgical cuts so Q doesn't widen as you reduce gain.
- Use Normal mode for musical tone shaping — gain-dependent Q is part of the character.
- Engage Bell mode on LF/HF when you want to add a surgical bump (e.g., 60 Hz kick weight) without affecting everything below/above.

**Don't:**
- Pile on huge boosts (+15 dB) without using the global Gain to compensate — you'll overdrive the next stage.
- Stack Channel EQ + M-Class EQ doing the same job. Pick one.
- Use the LPF heavily on bright sources before mastering — leave high-end shaping for the mastering EQ if possible.
- Forget that "EQ phase smearing" is a real thing — narrow Q boosts (>2.0) on transient material introduce ringing.

---

## Master Bus Compressor

### Role
A glue compressor for the master bus, modelled in the SSL G-series tradition: punchy, cohesive, "fairy dust" on a finished mix. Available as a Main Mixer master section component and as a rack device. Equally useful on drum buses and submixes.

### Best uses
- Master bus glue (1–3 dB GR, gentle ratios)
- Drum bus cohesion (3–6 dB GR)
- Aggressive parallel "smash" on a drum bus aux
- Sidechain pumping effects (kick keyed into bass/pad bus)

### Parameters

| Parameter | Range | Function |
|---|---|---|
| **Input Gain** | ±18 dB | Pre-comp drive. Use to align with threshold without touching threshold itself. |
| **Threshold** | -30 to 0 dB | Onset of compression. Mix bus comps usually sit around -10 to -20 dB threshold for subtle GR. |
| **Ratio** | **2:1, 4:1, 10:1** (stepped) | Three discrete ratios in classic SSL bus-comp style. 2:1 = invisible glue. 4:1 = obvious cohesion. 10:1 = aggressive limiting. |
| **Attack** | **0.1, 0.3, 1, 3, 10, 30 ms** (stepped) | Six discrete values. Faster = more transient catching (and pumping). Slower = lets transients through. |
| **Release** | **0.1, 0.3, 0.6, 1.2 s + Auto** | Stepped + program-adaptive Auto. Auto is the safe default for full mixes. |
| **Make-Up Gain** | -5 to +15 dB | Compensates for level loss caused by GR. |
| **Mix (Dry/Wet)** | 0–100% | <100% = parallel compression. Critical for retaining transients on drums. |

The stepped Attack/Release/Ratio values are characteristic of classic SSL bus comps — they reduce parameter overload and encourage decisive choices.

### Sidechain
- **External SC L/R inputs** on the rear panel.
- Front-panel **Sidechain button** with **Connected LED**.
- **CV output:** Gain Reduction.

### Metering
Real-time GR meter in dB.

### Recipes (Master Bus Compressor)

```
Master bus "glue" (the classic)
  Threshold:  -10 to -14 dB (aim for 1-3 dB GR on peaks)
  Ratio:      2:1
  Attack:     10 ms or 30 ms (let transients through)
  Release:    Auto
  Make-Up:    +1 to +2 dB
  Mix:        100%
```

```
Drum bus pump
  Threshold:  -18 dB (4-6 dB GR)
  Ratio:      4:1
  Attack:     1 ms
  Release:    0.1 s
  Make-Up:    +3 dB
  Mix:        70-80% (parallel keeps transients)
```

```
Aggressive parallel smash (drum aux)
  Threshold:  -28 dB (10-15 dB GR — yes, really)
  Ratio:      10:1
  Attack:     0.3 ms
  Release:    0.1 s
  Make-Up:    +6 dB
  Mix:        Send a copy to this device, blend in alongside dry drum bus
```

```
Sidechain pumping (kick keys synth bus)
  Threshold:  -20 dB
  Ratio:      4:1
  Attack:     0.3 ms
  Release:    0.3 s
  Sidechain:  On, fed from kick send
  Mix:        100%
```

```
Vocal bus cohesion
  Threshold:  -16 dB (2-3 dB GR)
  Ratio:      2:1
  Attack:     10 ms
  Release:    Auto
  Make-Up:    +2 dB
  Mix:        100%
```

### Do this / Don't do this

**Do:**
- Aim for 1–3 dB GR on the master bus. More than that and you're mixing with the comp, not gluing the mix.
- Use Auto release on full mixes — it adapts to program material and avoids pumping.
- Use the stepped attack values decisively: 10 ms or 30 ms for "glue," 1 ms or 0.3 ms for "pump."
- Use Mix < 100% on drum buses to retain transient impact.

**Don't:**
- Set Threshold so low that GR is constant — you'll pancake the mix's natural dynamics.
- Use 0.1 ms attack on a finished mix — it kills transients and dulls the master.
- Stack Master Bus Comp into M-Class Compressor doing the same job. If you use both, give them distinct duties (e.g., MBC for glue, M-Class for level control).
- Forget gain staging: heavy Make-Up Gain into a Maximizer that's also pushing hard = double-limiting and squashed mids.

---

## M-Class Effects (Mastering Suite)

The M-Class Effects are four devices designed for the final mastering stage. They appear in the Factory Sound Bank as **Mastering Combi patches** intended to be used as Master Insert FX in the Main Mixer. The four devices are:

1. **M-Class Equalizer** — tone shaping
2. **M-Class Stereo Imager** — stereo width
3. **M-Class Compressor** — dynamics control
4. **M-Class Maximizer** — loudness + brick-wall limiting

**Standard mastering chain order: EQ → Stereo Imager → Compressor → Maximizer.** All four common-feature elements (Input meter, Bypass/On/Off, Signal Flow Graph) apply.

---

### M-Class Equalizer

#### Role
Mastering-grade EQ. Lo Cut + Lo Shelf + 2 parametric bands + Hi Shelf, with a graphic frequency response display. Used for final tonal adjustments and to prevent subsonic content from hitting the limiter.

#### Bands

| Band | Type | Frequency | Gain | Q |
|---|---|---|---|---|
| **Lo Cut** | 12 dB/oct HPF below 30 Hz | Fixed at 30 Hz | switch on/off | — |
| **Lo Shelf** | Shelf | 30 Hz – 600 Hz | ±18 dB | High Q creates "bump" in the opposite direction (resonance) |
| **Parametric 1** | Bell | 39 Hz – 20 kHz | ±18 dB | Higher = narrower |
| **Parametric 2** | Bell | 39 Hz – 20 kHz | ±18 dB | Higher = narrower |
| **Hi Shelf** | Shelf | 3 kHz – 12 kHz | ±18 dB | High Q creates opposite-direction bump |

#### Tip from the docs
> "Activating the Lo Cut switch prevents subsonic sound from 'topping' the compressor/limiter."

Always engage Lo Cut on the master if your mix has any sub-30 Hz content (kick, sub bass) that you don't want eating limiter headroom.

#### Recipes (M-Class EQ)

```
Master tonal polish
  Lo Cut:    On
  Lo Shelf:  +0.5 dB at 80 Hz, Q low (broad warmth)
  Para 1:    -1 dB at 350 Hz, Q 1.0 (de-mud, gentle)
  Para 2:    +0.7 dB at 8 kHz, Q 0.8 (presence)
  Hi Shelf:  +1 dB at 12 kHz, Q low (air)
```

```
Brighten a dull mix
  Lo Cut:    On
  Para 2:    +1.5 dB at 6 kHz, Q 0.9
  Hi Shelf:  +1.5 dB at 10 kHz, Q low
```

```
Tame harshness
  Para 1:    -1.5 dB at 2.5 kHz, Q 1.2
  Para 2:    -0.8 dB at 4.5 kHz, Q 1.5
```

#### Do / Don't (M-Class EQ)
**Do:** Make small moves on the master (≤2 dB). Engage Lo Cut by default. Use broad Q (low values) for tone, narrow Q for problems.
**Don't:** Boost narrow Q peaks heavily — it sounds like a phaser ringing on transients. Don't try to fix mix problems here that should be fixed in the mix.

---

### M-Class Stereo Imager

#### Role
Frequency-dependent stereo width. Splits the signal into two bands at a user-set crossover frequency, then lets you widen or narrow each band independently. Classic application: tighten the bass, widen the highs.

#### Important constraint
> "Does not create stereo from mono input."

It can only widen what's already stereo. Mono in = mono out, no matter the Width setting.

#### Parameters

| Parameter | Range | Function |
|---|---|---|
| **X-Over Frequency** | 100 Hz – 6 kHz | Splits the signal into Lo and Hi bands |
| **Lo Width** | Variable (anti-clockwise narrow / clockwise wide) | Stereo width below crossover |
| **Hi Width** | Variable (anti-clockwise narrow / clockwise wide) | Stereo width above crossover |
| **Solo switch** | Lo / Hi / Normal | Monitor each band in isolation |

#### Connections
- Standard L/R in/out
- **Separate L/R outputs** that can be set to carry the Lo or Hi band only, for parallel processing routing

#### Recipes (M-Class Stereo Imager)

```
Tight bass, wide highs (mastering default)
  X-Over:    250 Hz
  Lo Width:  ~9 o'clock (narrow toward mono)
  Hi Width:  ~2 o'clock (subtle widen)
```

```
Vocal de-widen (focus center)
  X-Over:    400 Hz
  Lo Width:  Centered
  Hi Width:  ~10 o'clock (slight narrow)
```

```
"Big" master cheat (use sparingly)
  X-Over:    500 Hz
  Lo Width:  Centered to slight narrow
  Hi Width:  ~3 o'clock (more width)
```

#### Do / Don't (Stereo Imager)
**Do:** Always check mono compatibility after widening. Solo each band to verify what's where. Narrow the bass — it tightens punch and gives the limiter cleaner peaks.
**Don't:** Crank Hi Width to extremes — phase issues collapse on mono playback (phones, club PA in mono, Bluetooth speakers). Don't expect mono sources to "become stereo."

---

### M-Class Compressor

#### Role
Mastering-grade compressor. From subtle glue to "aggressive pumping effects." Soft Knee + Adapt Release give it a smooth, transparent character at moderate settings.

#### Parameters

| Parameter | Range | Function |
|---|---|---|
| **Input Gain** | ±12 dB | Compression "drive" — push into threshold without changing threshold knob |
| **Threshold** | -36 to 0 dB | Onset level |
| **Ratio** | 1:1 to ∞:1 | Continuously variable, unlike Master Bus Comp's stepped values |
| **Attack** | 1–100 ms | Slower than Channel Dynamics — built for program material, not transients |
| **Release** | 50–600 ms | Recovery time |
| **Output Gain** | ±12 dB | Make-up gain |
| **Soft Knee** | On/Off | Gradual onset around threshold; smoother sound |
| **Adapt Release** | On/Off | Auto-extends release on sustained peaks; prevents pumping on long notes |

#### Sidechain
- **External SC L/R inputs**
- **Solo Sidechain** switch — listen to what's hitting the detector (essential for tuning de-essers and ducking)
- **CV out:** Gain Reduction (modulate other params with the comp envelope)

#### Sidechain applications (per docs)
- **Ducking:** Send voice-over to MClass Comp's SC. The music bed (going through the comp) automatically drops when voice plays.
- **De-essing / frequency-sensitive compression:** Insert M-Class EQ into the SC path, boost the offending frequency (e.g., sibilants at 6–8 kHz), and the compressor will only react to that band. Use Solo Sidechain to confirm what you're keying off.

#### Recipes (M-Class Compressor)

```
Mastering glue
  Threshold:    -14 dB (1-2 dB GR on peaks)
  Ratio:        1.5:1 to 2:1
  Attack:       30 ms
  Release:      300 ms
  Soft Knee:    On
  Adapt Rel:    On
  Output Gain:  +1 to +2 dB
```

```
Vocal-bus level control
  Threshold:    -18 dB (3-5 dB GR)
  Ratio:        3:1
  Attack:       10 ms
  Release:      200 ms
  Soft Knee:    On
  Adapt Rel:    On
```

```
De-esser via sidechain
  Threshold:    -20 dB
  Ratio:        6:1
  Attack:       1 ms
  Release:      80 ms
  Sidechain:    On, fed via M-Class EQ with +12 dB at 7 kHz, Q 2.0
  Solo SC:      Confirm you're hearing only sibilants
```

```
Aggressive pump
  Threshold:    -30 dB (heavy GR)
  Ratio:        ∞:1
  Attack:       1 ms
  Release:      50 ms
  Soft Knee:    Off
  Adapt Rel:    Off
```

#### Do / Don't (M-Class Compressor)
**Do:** Keep mastering GR conservative (1–3 dB). Use Soft Knee + Adapt Release for transparency. Use Solo Sidechain when tuning a de-esser or ducker.
**Don't:** Use this for fast drum-transient catching — its 1 ms minimum attack is fine but Channel Dynamics' Fast mode (3 ms peak detect) and the Master Bus Comp (0.1 ms) are designed for that role. Don't smash the master with infinite ratio unless you genuinely want a pump effect.

---

### M-Class Maximizer

#### Role
Loudness maximization with **brick-wall limiting**. Always the last device in the master chain. Designed to sit "between the mixed final output and the Hardware Interface."

#### Parameters

| Parameter | Options | Function |
|---|---|---|
| **Input Gain** | ±12 dB | The main "push into the limiter" knob — drives loudness |
| **Limiter On/Off** | Toggle | Enables the limiting section |
| **Look Ahead** | On/Off | 4 ms delay so the limiter can detect and pre-react to peaks. Cleaner limiting at the cost of 4 ms latency. |
| **Attack** | Fast / Mid / Slow | Limiter response speed. Fast for clean ceiling, Slow for more punch |
| **Release** | Fast / Slow / Auto | Recovery; Auto adapts to program. Auto is the safe default. |
| **Output Gain** | Variable | Final ceiling. Typically 0 dB. |
| **Soft Clip On/Off** | Toggle | Adds gentle saturation as a secondary safeguard, "pleasant warm-sounding distortion" |
| **Soft Clip Amount** | Variable | Distortion intensity |
| **Output Meter** | Peak / VU | Switch between peak (true ceiling) and VU (perceived loudness) metering |

#### Brick-wall mode (per docs)
> "With Fast Attack and Look Ahead activated (Output Gain at 0 dB) you will get 'brick wall' limiting — no signal peaks over 0 dB will pass."

#### Soft Clip
A second-stage safety net that tames any peaks the limiter doesn't catch. It introduces musical distortion — at modest amounts it sounds warmer and louder; pushed hard it audibly distorts.

#### Recipes (M-Class Maximizer)

```
Transparent mastering ceiling (modern release)
  Input Gain:    +3 to +6 dB
  Limiter:       On
  Look Ahead:    On
  Attack:        Fast
  Release:       Auto
  Output Gain:   -0.3 dB (true-peak safety)
  Soft Clip:     Off (or very low amount)
  Meter:         Peak
```

```
"Loud" master (push it)
  Input Gain:    +6 to +9 dB
  Limiter:       On
  Look Ahead:    On
  Attack:        Fast
  Release:       Auto
  Output Gain:   -0.3 dB
  Soft Clip:     On, amount low (warmth)
```

```
Punchy master (lets transients breathe)
  Input Gain:    +3 dB
  Limiter:       On
  Look Ahead:    On
  Attack:        Slow
  Release:       Slow
  Output Gain:   -0.3 dB
  Soft Clip:     Off
```

```
Safety limiter only (don't change tone)
  Input Gain:    0 dB
  Limiter:       On
  Look Ahead:    On
  Attack:        Fast
  Release:       Auto
  Output Gain:   -0.3 dB
  Soft Clip:     Off
```

#### Do / Don't (M-Class Maximizer)
**Do:** Set Output Gain to -0.3 dB (or -1 dB for streaming) to leave true-peak headroom. Always use Look Ahead for clean limiting. Use Auto release as the default.
**Don't:** Push Input Gain so hard the meter sits at the ceiling permanently — 3–6 dB of GR is the loud-but-clean zone; 8+ dB starts to pump and distort. Don't put any device after the Maximizer (no EQ, no comp, nothing). Don't enable Soft Clip at high amount on a delicate master — it grits the top end.

---

## End-to-end mastering chain

For a finished mix going through the master section as Master Insert FX, the recommended order is:

```
Mix Bus
  └─ M-Class Equalizer       (Lo Cut on; gentle tonal moves <2 dB)
       └─ M-Class Stereo Imager  (tight bass; subtle width on highs)
            └─ M-Class Compressor    (1-3 dB GR glue, Soft Knee + Adapt Release)
                 └─ M-Class Maximizer    (Look Ahead + Fast attack; -0.3 dB ceiling)
                      └─ Hardware Interface
```

Reason ships **Mastering Combi patches** in the Factory Sound Bank that pre-wire this chain — load one of those as a starting template.

### Channel-strip vs master-bus compressors at a glance

| When | Use |
|---|---|
| Single-track dynamics (vocal, bass, drum) | **Channel Dynamics** |
| Drum bus glue/pump or master bus glue | **Master Bus Compressor** |
| Mastering compression with sidechain finesse | **M-Class Compressor** |
| Brick-wall limiter / loudness | **M-Class Maximizer** |

### Single-track vs mastering EQ at a glance

| When | Use |
|---|---|
| Per-track tonal shaping during mix | **Channel EQ** (HPF + LPF + 4 bands, Normal/E modes) |
| Final master tonal polish | **M-Class Equalizer** (Lo Cut + Lo Shelf + 2 parametric + Hi Shelf, graphic display) |

---

## Pitfalls to avoid

1. **Over-compression.** GR > 6 dB on a master, or > 10 dB on a track, usually reads as squashed. Use the Mix knob for parallel compression instead of dialing in more GR.

2. **Pumping.** Caused by too-fast release on sustained material. On Master Bus Comp, switch Release to **Auto**. On M-Class Compressor, enable **Adapt Release**.

3. **Brick-wall limiter abuse.** The Maximizer can push 8+ dB GR but it costs transient impact, dynamics, and (eventually) audible distortion. 3–6 dB is the loud-but-clean zone.

4. **EQ phase smearing.** Narrow-Q boosts on transients (drums, plucks) ring audibly. Use broad Q (low values) for tonal moves, narrow Q only for surgical cuts. Use **E mode** on Channel EQ for predictable surgical work.

5. **Forgotten subsonic.** A kick or sub bass with content below 30 Hz eats limiter headroom for nothing — engage **Lo Cut** on the M-Class Equalizer at the top of the master chain.

6. **Stacked compressors doing the same job.** Channel Dynamics → Master Bus Comp → M-Class Comp all squashing 5 dB each = a dead mix. Each stage should have a distinct role (e.g., per-track evening, bus glue, master finishing).

7. **Sidechain SC button engaged but nothing patched.** Trust the front-panel "Connected" LED — if it's not lit, your SC isn't doing anything.

8. **Mono collapsing from over-widening.** Aggressive M-Class Stereo Imager Hi Width settings phase-cancel on mono playback. Always check mono compatibility.

9. **Devices after the Maximizer.** Anything inserted after a brick-wall limiter can push the signal back over 0 dB. The Maximizer is ALWAYS last.

10. **Gain staging.** With ±18 dB Input Gain on Channel Dynamics, ±12 dB on M-Class devices, ±15 dB Make-Up on Master Bus Comp, and ±18 dB on the Channel EQ, it's easy to add up to >40 dB of gain across a chain. Watch the meters at every stage.

11. **Treating mastering EQ as mix rescue.** If the mix needs a 6 dB cut at 200 Hz on the master, fix the bass track in the mix. The mastering chain is for polish, not surgery.

12. **Auto-makeup confusion (Channel Dynamics).** Channel Dynamics has automatic makeup gain, so threshold + ratio changes don't drop the level — be aware that you're hearing the compressed sound at the same level as the dry, which can fool you into pushing the threshold too low.
