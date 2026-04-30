# Reason 13: Delay, Reverb & Chorus Effects
Based on Reason 13.4 documentation.

A practical reference for the four time-based effects that cover almost every reverb, delay, and modulation chorus duty in a Reason session: **Ripley Space Delay**, **RV7000 Mk II Advanced Reverb**, **The Echo**, and **Quartet Chorus Ensemble**.

## Quick Comparison

| Device | Type | Algorithms / Modes | Sync | Typical Use |
|---|---|---|---|---|
| **Ripley Space Delay** | Multi-section delay + reverb + sound shaping | Single mode, configurable: Mono/Dual delay, Ping-Pong, Band/Hi-Lo feedback filter, Serial/Parallel reverb | Yes (1/128 to 8/4) | Atmospheric multi-tap, dub delay, lo-fi chirps, washed-out spaces, modulated rhythmic delay |
| **RV7000 Mk II** | Advanced reverb + echo with EQ + gate + convolution | 10 algorithms: Small Space, Room, Hall, Arena, Plate, Spring, Echo, Multi Tap, Reverse, Convolution | Yes (Echo, Multi Tap, Reverse) | Vocal plate, drum room/hall, gated 80s snare, IR convolution, classic master/send reverb |
| **The Echo** | Versatile stereo delay with vintage character | 3 modes: Normal, Triggered, Roll. Drive flavors: LIM, OVDR, DIST, TUBE | Yes (1/128 to 1/2) | Tape-style delay, slap-back vocals, dub repeats, glitch/stutter via Roll, distorted feedback |
| **Quartet Chorus Ensemble** | Chorus / ensemble modulator | 4 algorithms: Chorus, BBD, FFT, Grain | No (LFO rates in Hz) | Lush analog chorus, BBD ensemble pads, sparkly synth widening, granular textures |

**Quick selection rule of thumb:**
- Need a *space* (room, hall, plate, gate, IR) → **RV7000 Mk II**
- Need an *atmospheric, modulated, character-laden delay* with a built-in reverb tail → **Ripley**
- Need a *vintage musical delay* with drive/wobble and easy ducking → **The Echo**
- Need *width, thickness, or analog chorus shimmer* → **Quartet**

---

## Ripley Space Delay

### Type / Role
A stereo delay built around a deep modulation matrix and an integrated reverb. Routes audio through a chain you can rearrange: **Input → Noise / Distortion / Digital / EQ (each routable) → Delay → Feedback Filter → Reverb → Ducker → Output.** Available as both a Reason Rack device and a DAW plugin.

### Best Uses
- Multi-tap, ping-pong, and offset-stereo delays with attitude
- Dub-style delays that mutate as they decay (Wobbler, modulated filter)
- Frozen ambiences and stutters via **Freeze**
- Send-effect washes that sit *behind* the source thanks to the **Ducker**
- Lo-fi character (Noise + Digital bitcrush + Distortion) on otherwise clean material
- Self-oscillating/runaway feedback as a sound design tool (with the Limiter on)

### Modes / Configurations
Ripley does not have hard "modes" — instead you mix and match:
- **Single delay** vs **Dual Delay** (independent L/R times)
- **Ping Pong** with adjustable Pan
- **Feedback filter**: **Band** (8 fixed bandpass filters with shifts) or **Hi-Lo** (single bandpass with Low/Hi cut)
- **Reverb routing**: **Serial** (delay → reverb) or **Parallel** (delay ‖ reverb)
- **Insertion routing** for Noise / Distortion / Digital / EQ — choose Input, Feedback, Delay Out, Space Out, or Output

### Key Parameters

**Delay**
- **Time** — 2–5000 ms, or 1/128–8/4 in Sync
- **Tap** — manual tempo entry
- **Sync** — host-tempo lock
- **Keep Pitch** — eliminates pitch-shift when you sweep Time
- **Multiply (1/2, x2)** — *always* re-pitches one octave, even with Keep Pitch on
- **Offset** — L/R time difference
- **Width** — stereo spread of repeats
- **Feedback** — 0–130%; 100% = unity (infinite); >100% = increasing distortion per repeat
- **Freeze** — locks current buffer for an infinite loop without new input
- **Wobbler** — random pitch wobble (tape emulation), independent of Keep Pitch

**Feedback Filter**
- *Band mode*: 8 bandpass filters w/ individual levels + Freq Shift + L/R Offset
- *Hi-Lo mode*: single bandpass, drag-to-set Low Cut / Hi Cut
- **Feedback Limiter** — tames runaway when overdriving filter bands or using the external feedback loop

**Reverb (Space)**
- **Amount, Decay, Size, Space Width**
- **Serial / Parallel** routing button

**Sound Shaping**
- **Noise**: Amount, Character, Hi End, Type selector, Stereo
- **Distortion**: Drive, Tone, Dry/Wet
- **Digital (bitcrusher)**: Rate Crush, Bit Crush
- **EQ**: Low shelf ±18 dB, parametric Mid (61 Hz–12.69 kHz, ±18 dB, Q), High shelf ±18 dB

**Output**
- **Dry/Wet** (set 100% Wet on a send)
- **Output Gain** (−Inf to +18.1 dB)
- **Ducker** — attenuates wet while input is present; great for letting vocals breathe before the tail blooms

**Modulation**
- **LFO 1 & 2** — Sine, triangle, pulse, random, slope, stepped + Beat Sync + Phase
- **Envelope Follower** — Source select (Input, Delay Out, Space Out, Freeze, Macro), Sens, Rise, Fall
- **Macro** button + knob
- **Modulation Matrix** — 3 buses, each "Source → Dest 1 → Dest 2 → Scale". Sources: LFO1/2, Env Follower, Macro Knob/Button, Constant, Ducker Follower, CV1/2 In. Almost every parameter is a destination.

### Sync Behavior
- **Sync** button locks Time and Offset to host tempo (1/128–8/4)
- LFOs have independent **Beat Sync**
- **Tap** is for rolling your own tempo when not synced

### EQ / Filter Shaping
- Dedicated **EQ** module (Low shelf, parametric Mid, High shelf) that you can place anywhere in the chain
- **Feedback Filter** is the character knob: Band mode for resonant rhythmic filtering per repeat; Hi-Lo for classic dub low/hi-pass darkening as repeats decay

### Common Workflows

**Dub delay**
1. Put Ripley on a send, Dry/Wet = 100% Wet
2. Sync on, Time = 1/4 dotted or 3/16, Feedback ≈ 60–80%
3. Feedback Filter = Hi-Lo, sweep Hi Cut down to darken repeats
4. Add a touch of **Wobbler** for tape feel
5. Optional: Distortion on Feedback insertion point for analog grit
6. Reverb in **Serial**, small Amount, medium Size, for a damp room around the repeats

**Atmospheric multi-tap pad**
1. Insert on a sustained pad
2. Dual Delay on, Time L = 3/8, Time R = 1/2; Width up
3. Feedback Filter = Band; modulate Freq Shift with LFO1 (slow sine, Beat Sync 1 bar)
4. Reverb in **Parallel**, large Size, long Decay
5. Ducker low so the pad always blooms

**Frozen stutter loop**
1. Set short Time (e.g. 1/16), feedback 100%
2. Punch **Freeze** on a beat — the buffer locks
3. Modulate Bit Crush + Rate Crush with Macro Knob for a glitch sweep
4. Drop the Freeze to release

### Pitfalls
- **Feedback >100% is on purpose** — but with the Feedback Limiter off, levels climb fast. Keep the Limiter armed unless you want chaos.
- **Multiply re-pitches by an octave regardless of Keep Pitch** — surprise pitch jumps if you automate it
- The external feedback loop (rear) bypasses the internal Feedback Filter limiter — be careful with external distortions there
- 100% Wet for sends; otherwise dry signal will phase against the channel's own dry path

> **Do this:** Use Ripley as a *send* and automate Macro/Freeze for performance moments.
> **Don't do this:** Put it as an insert at 100% Wet on a vocal main — you'll lose intelligibility instantly.

---

## RV7000 Mk II Advanced Reverb

### Type / Role
The flagship reverb in the Reason rack. Ten algorithms cover everything from spring tanks to convolution, plus a global EQ, a Gate, and a zero-latency **Convolution** engine that can load your own IRs (≈12 s max length).

### Best Uses
- Vocals: **Plate** for classic sheen; **Hall** for size; **Convolution** for realism
- Drums: **Room** and **Plate** for kits; **Reverse** for FX builds; **Multi Tap** for rhythmic ambience
- Master / mix bus: gentle **Hall** as a glue
- Guitar: **Spring** for amp-style splash
- Sound design: **Reverse**, **Echo**, **Multi Tap**, **Convolution**

### The Ten Algorithms

| # | Algorithm | Best for | Notable params |
|---|---|---|---|
| 1 | **Small Space** | Booths, closets, tight ambience | Size, Room Shape (4), Wall Irreg, LF Damp, Mod Rate/Amount, Predelay |
| 2 | **Room** | Drums, realistic interiors | Size, Diffusion, Room Shape (4), ER→Late, ER Level, Predelay, Mod Amount |
| 3 | **Hall** | Vocals, orchestral, master glue | Same params as Room with larger Size |
| 4 | **Arena** | Big stages, stadiums | Size, Diffusion, L/R Delay, Stereo Level, Mono Delay, Mono Level |
| 5 | **Plate** | Vocals (the classic), snare | LF Damp, Predelay, Decay |
| 6 | **Spring** | Guitar amp, surf, lo-fi | Length, Diffusion, Disp Freq, Disp Amount, LF Damp, Stereo on/off |
| 7 | **Echo** | Tempo-synced delay tail | Echo Time, Diffusion, Tempo Sync, LF Damp, Spread, Predelay |
| 8 | **Multi Tap** | Rhythmic ambience, 4 taps | Per-tap Delay/Level/Pan, Repeat Time, Diffusion, Tempo Sync |
| 9 | **Reverse** | Pre-vocal swells, builds | Length, Density (~50% saves CPU), Rev Dry/Wet, Tempo Sync |
| 10 | **Convolution** | IR sampling, real spaces | Sample Preset, Length, Size (semitones −12 to +12), 9 Stereo Modes, Predelay (negative masks transients), Gain |

### Universal Main-Panel Parameters
Across all algorithms:
- **Decay** — reverb length / echo feedback
- **HF Damp** — high-frequency decay rate (think: cloth on the walls)
- **HI EQ** — high-shelf treble of the wet signal
- **Dry/Wet** — balance

### EQ Section (wet only)
- **Low Gain / Low Freq** — low shelf
- **Param Gain / Param Freq / Param Q** — parametric mid
- (HI EQ lives on the main panel as a high shelf)

### Gate Section
Two trigger sources for dynamic reverb tails:

**Audio trigger**
- **Threshold**, **High Pass** (so kick rumble doesn't trigger), **Hold**, **Attack**, **Release**

**MIDI/CV trigger**
- Gate opens for the duration of a note or CV high

**Decay Mod** modulates the main Decay when the gate closes — this is what makes a real "gated reverb" sound, killing the tail rather than leaving it ringing.

### Sync Behavior
Tempo Sync is per-algorithm: available on **Echo**, **Multi Tap** (all delay/repeat times), and **Reverse** (Length). Other algorithms have time-based predelay only.

### EQ / Filter Shaping
- **HF Damp** + **HI EQ** are your primary "darken the tail" tools
- The dedicated wet **EQ** can carve mud (Low cut/shelf 200–400 Hz) or add air
- On Convolution and Spring, **LF Damp** does the heavy lifting on low-end buildup

### Common Workflows

**Lead vocal plate**
1. RV7000 Mk II on a send, Dry/Wet = 100% Wet
2. Algorithm = **Plate**, Decay 1.8–2.4 s, Predelay 20–40 ms
3. HF Damp ~30–50% to soften top
4. EQ: Low Gain −3 to −6 dB at 200–400 Hz; gentle high shelf +1–2 dB at 8 kHz
5. Optional: side-chain ducking on the send channel

**1980s gated reverb on snare**
1. RV7000 Mk II as **insert** on a parallel snare bus
2. Algorithm = **Hall** (or large **Room**), Decay ~1.6 s
3. Gate ON, Trig Source = Audio (or MIDI from snare)
4. Threshold so the gate opens on the snare hit
5. Hold ~150–200 ms, Release fast (~30 ms)
6. Decay Mod set so closing the gate kills the tail
7. Dry/Wet 100% Wet (it's parallel)

**Drum room / glue**
1. **Room**, Size medium, Decay 0.8–1.2 s
2. ER Level up for early reflection presence
3. Diffusion high for smooth tail
4. HF Damp 40% to keep cymbals from getting harsh

**Reverse swell into vocal phrase**
1. Algorithm = **Reverse** as **insert** (or send in pre-fader mode — see Pitfalls)
2. Length tempo-synced to 1/2 or 1/1
3. Density ~50% (CPU friendly)
4. Rev Dry/Wet leaning Wet on the FX track
5. Automate the send up just before the downbeat

**Realistic IR space**
1. Algorithm = **Convolution**, load IR
2. Predelay slightly negative if you want to "pre-mask" the transient
3. Stereo Mode: Stereo 75–100% for stereo sources, Mono for mono
4. Size in semitones for pitched space tricks (−1 to −2 = bigger space; +2 = tinier)

### Pitfalls
- **Reverse on a send**: dry signal leaks through unless you use the send in **pre-fader** mode or insert the device — otherwise you hear the original first, defeating the effect
- **Convolution + many instances** is the heaviest algorithm. Bus reverbs are your friend. Long IRs auto-truncate at ~12 s
- **Convolution patches** reference samples by path — moving projects between machines without the samples breaks the patch
- Convolution is **not true stereo** — every other algorithm is
- Tempo Sync only applies to Echo / Multi Tap / Reverse
- HF Damp at 100% can make the tail feel lifeless on bright sources — back off to 30–60%

> **Do this:** Use Hall and Plate as session-wide sends. Decide which is "long vocal" and which is "short drum" up front.
> **Don't do this:** Stack Convolution on every channel — sum to a bus.

### Send vs Insert
- **Send** for everything except **Reverse** (or use pre-fader send) and **Gate-as-insert-effect** scenarios where you want the gated dynamics on the wet alone
- **Insert** when you want EQ/Gate/Decay Mod to interact with that one source
- Save patches with `.RV7` extension; convolution patches don't embed the sample

---

## The Echo

### Type / Role
A musical, vintage-flavored stereo delay with three operational modes, four drive flavors, a resonant filter, an envelope wobble, and a built-in ducker. Less of a sound-design playground than Ripley, more of a *play-it-like-an-instrument* delay.

### Best Uses
- Vocal slap-back (single repeat, ~80–140 ms, no sync)
- Quarter-note dub delays with tube drive on the feedback
- Stutter / glitch / "drop the beat into a delay throw" via **Roll**
- One-shot delay throws via **Triggered** mode (press Trig only when you want repeats)
- Tape-style wow/flutter on synth lines (Wobble + LFO Amount)

### Modes (3)

| Mode | Behavior | Use when |
|---|---|---|
| **Normal** | Always processing input → output | Standard delay duties |
| **Triggered** | Dry only until **Trig** is pressed; then echo for that moment | Punching repeats on specific words / hits |
| **Roll** | Dry signal is suppressed while feedback rises and the wet is mixed in | Stutter / freeze effects; move the slider fully 0 → max, not in-between |

### Key Parameters

**Delay**
- **Time** — 1–1000 ms, or 1/128 to 1/2 when synced
- **Offset R** — right-channel offset for stereo
- **Keep Pitch** — pitch-stable Time changes
- **Sync** — tempo sync
- **Ping-Pong** — alternates L/R per repeat
- **Pan** — stereo width and starting side

**Feedback**
- **Feedback** — 100% = unity (infinite repeats)
- **Offset R** (bipolar) — independent right-channel feedback for "wandering" repeats
- **Diffusion Amount** — smear via additional repeats around the original
- **Diffusion Spread** — stereo width of the diffusion

**Color**
- **Drive** with four algorithms:
  - **LIM** — soft analog limiter
  - **OVDR** — analog-style overdrive
  - **DIST** — denser distortion
  - **TUBE** — tube emulation
- **Resonant Filter** — bandpass per repeat: **Freq** + **Reso**

**Modulation**
- **Env** (bipolar) — pitch bends repeats up or down
- **Wobble** — random tape-style pitch wobble
- **LFO Rate** + **LFO Amount** — pitch-modulates L/R independently

**Output**
- **Dry/Wet** — set Wet for Roll mode
- **Ducking** — attenuates wet under input, fades in during gaps

**Rear panel CV**: Trig (gate for Triggered mode), Roll, Delay Time, Filter Freq. **Breakout jacks** let you splice an external effect into the feedback loop (classic move: distortion increasing with each repeat).

### Sync Behavior
- **Sync** locks Time and Offset R to tempo, 1/128 to 1/2 (note Ripley goes to 8/4 — The Echo is shorter at the long end)
- The LFO is in Hz only — not tempo-synced

### EQ / Filter Shaping
- The **Resonant Filter** is per-repeat, so each repeat re-filters → naturally darkens or focuses the tail
- **Drive** colors each repeat; LIM is the most surgical, TUBE the most musical, DIST the most aggressive
- For broader EQ, put a separate EQ device after The Echo

### Common Workflows

**Vocal slap-back (Sun-Records style)**
1. The Echo as a send (or insert with low Wet)
2. Sync OFF, Time ≈ 90–130 ms, Feedback 0–10%
3. Drive = TUBE, low amount; Resonant Filter Freq mid, Reso low
4. Dry/Wet around 25–35% if insert, or 100% Wet on a send

**Dub quarter-note**
1. Send, Sync ON, Time = 1/4 (or 1/4 dotted)
2. Feedback ~60–75%
3. Diffusion Amount low–medium, Diffusion Spread up
4. Drive = OVDR, modest, with the breakout sending feedback through Scream 4 for character
5. Resonant Filter sweeping down via CV for the classic "darkening repeats"

**Roll stutter on a drum loop**
1. Insert, Mode = **Roll**, Dry/Wet = Wet
2. Time = 1/16 or 1/32, Sync ON
3. On the beat you want to freeze, slam the Roll slider 0 → max
4. Release fully back to 0 to let the loop continue

**Triggered ad-lib delays**
1. Insert on lead vocal, Mode = **Triggered**
2. Set delay to taste (1/8 dotted, ~50% feedback)
3. Map a controller key to **Trig**
4. Hit Trig only on phrases you want to throw

### Pitfalls
- **Roll mode** wants the slider to move *fully* — leaving it at 50% gives a confusing in-between state
- Drive on heavy DIST + high feedback = volume runaway. Use the channel meter, and consider a limiter after it
- The internal LFO is not synced — if you need rhythmic modulation, automate or use external CV
- Send setup needs Dry/Wet at 100% Wet — leaving it at 50% will phase against the channel's own dry path
- Mono-in/stereo-out: if you feed a mono signal, Ping-Pong + Offset R do the spatializing — but a true mono target chain will fold it back

> **Do this:** Pick The Echo for "musical, played" delay moves (slap, throws, stutters).
> **Don't do this:** Reach for The Echo when you actually want a reverb or a multi-tap atmospheric — that's RV7000 or Ripley.

---

## Quartet Chorus Ensemble

### Type / Role
A four-algorithm chorus / ensemble unit. Chiefly an **insert** effect for thickening, widening, and adding movement. Each algorithm has its own character — analog chorus, BBD ensemble, FFT spectral, and granular.

### Best Uses
- Lush analog chorus on Rhodes, clean guitar, pads (Chorus algorithm)
- Vintage string-machine / Juno-like ensemble (BBD)
- Spectral, "shimmery" widening on synths and vocals (FFT)
- Granular smearing for texture / sound design beds (Grain)

### Algorithms (4)

| Algorithm | What it does | Killer for |
|---|---|---|
| **Chorus** | Single delay-line chorus / flanger | Rhodes, clean guitar, simple thickening |
| **BBD** | Three parallel BBD delay lines, optional Noise Mod | String machines, vintage ensemble pads |
| **FFT** | FFT analysis + noise modulation of partials | Sparkle, shimmer, dense modern widening |
| **Grain** | Real-time grain extraction with cross-fading | Granular textures, drones, weird beds |

### Global Controls
- **Routing**: **Stereo** (L+R sum then process; mono input → stereo output) or **Dual Mono** (independent L and R)
- **Width**: mono → wide stereo, *can be set per algorithm*
- **Dry/Wet**: per-algorithm; even at 100% wet, *all chorus types still use some dry* — that's how chorusing works

### Per-Algorithm Parameters

**Chorus**
- **Delay** 1.00–30.00 ms — sets character (short = flange-y, long = chorus-y)
- **Mod Depth** — LFO depth on delay
- **Mod Rate** 0.10–5.00 Hz — LFO frequency
- **Feedback** — toward 100% gives flanger resonance; ~50% = gentle chorus

**BBD**
- **Delay** 1.00–30.00 ms — preset-scaled across 3 lines
- **Mod Depth**, **Mod Rate** 0.20–10.00 Hz
- **Noise Mod** — amplitude modulation with lowpass-filtered noise → "sparkle"

**FFT**
- **FFT Size** — 1 = fast, transient-friendly, ignores lows; 4 = accurate, slower, captures lows
- **Mod Depth** — noise modulation of partials
- **Frequency Range** (drag handles) — limits which bands get modulated

**Grain**
- **Phase** — random phase → "bubbly" cancellation effects
- **Size** — long = smooth, short = stuttery
- **Mod Depth** — random initial pitch of grains
- **Jitter** — random grain position
- **Density** — combines grain length / rate / overlap; high = fat, low = thin

**CV inputs (global):** Mod Depth CV, Width CV, Dry/Wet CV (bipolar with attenuators)

### Sync Behavior
None — the LFOs are in Hz, not synced to tempo. Use external CV/automation if you need tempo-locked motion.

### EQ / Filter Shaping
No dedicated EQ. For tone shaping put an EQ before/after Quartet (e.g., a high-pass before the chorus to keep low end dry, then EQ after for air).

### Common Workflows

**Lush chorus pad (Juno-style)**
1. Quartet as insert, Algorithm = **BBD**
2. Delay medium, Mod Depth ~40%, Mod Rate ~0.5 Hz
3. Noise Mod low–medium for sparkle
4. Width up to 80–100%
5. Dry/Wet ~50%

**Subtle Rhodes chorus**
1. Algorithm = **Chorus**
2. Delay 8–15 ms, Mod Depth 20–30%, Mod Rate 0.3–0.7 Hz, Feedback ~30%
3. Width 60–80%
4. Dry/Wet 35–45%

**Modern shimmer widener on a synth lead**
1. Algorithm = **FFT**, Size = 2
2. Frequency Range handles set above 800 Hz so lows stay tight
3. Mod Depth moderate
4. Width 100%, Dry/Wet 30–50%

**Granular texture bed**
1. Algorithm = **Grain**
2. Size large, Density high → thick smear
3. Jitter moderate, Mod Depth low (small random pitch)
4. Use as send so the dry remains intact

### Pitfalls
- **Mono-in / Stereo-out**: Stereo routing makes mono inputs come out stereo — but if your channel folds to mono later (busing), the width disappears
- **Chorus Feedback near 100%** flips the device into flanger territory — fine if intended, weird if you wanted gentle chorus
- **FFT Size = 4** is accurate but introduces latency on transient material — use 1 for percussive sources
- **Dual Mono** routing means L and R are independent — don't use it for mono sources expecting stereo output
- All algorithms still pass *some* dry signal even at 100% Wet (that's the chorus/ensemble effect itself working). For pure wet (e.g., fully detuned grain texture), use it as a send and disable the channel's own dry path if needed.

> **Do this:** Insert Quartet on the source whose width/thickness you want to commit to.
> **Don't do this:** Put Quartet on a stereo bus that already has multiple chorused elements — phasing and motion smear will fight.

---

## Send vs Insert: Cheat Sheet

| Device | Default placement | When to insert | When to send |
|---|---|---|---|
| **Ripley** | Send (Dry/Wet 100%) | When you want the device's coloration + Ducker tied to *one* source | Most cases — share across multiple channels |
| **RV7000 Mk II** | Send (Dry/Wet 100%) | **Reverse** algorithm; when using the Gate on a single source; convolution applied to one source | Plate/Hall/Room used across the mix; conserves CPU on Convolution |
| **The Echo** | Either | Triggered mode with controller mapping; Roll mode dry-suppression behavior; Drive coloration of a single source | Dub delay throws; vocal slap-back shared across BVs |
| **Quartet** | Insert | Almost always — chorus is a tone-shaping decision per source | Granular textures used as a bed across a group |

**Rules of thumb**
- 100% Wet on a send. Always.
- One reverb send is usually two: a short and a long.
- One delay send is usually one or two: a 1/4-note (or 1/8-dotted) main delay, and a slap/short.
- Inserts let modulation (env follower, gate, ducker) react to *that* source's transients — sends average across many.

---

## Recipe Index (Starting Points)

| Sound | Device | Settings |
|---|---|---|
| **1980s gated snare** | RV7000 Mk II | Hall, Decay 1.6 s, Gate ON (Audio), Hold 200 ms, Decay Mod ON |
| **Vocal plate** | RV7000 Mk II | Plate, Decay 2.0 s, Predelay 30 ms, HF Damp 40%, Low cut 250 Hz |
| **Drum room glue** | RV7000 Mk II | Room, Size medium, Decay 1.0 s, ER Level up, Diffusion high, HF Damp 40% |
| **Reverse swell into chorus** | RV7000 Mk II | Reverse (insert), Length 1/2 synced, Density 50%, Rev Dry/Wet wet |
| **IR ambience** | RV7000 Mk II | Convolution, custom IR, Stereo 75%, Predelay slightly negative |
| **Sun-Records slap** | The Echo | Normal, ~110 ms, Feedback 5%, TUBE drive low, Filter mid, Reso low |
| **Dub quarter** | The Echo | Sync 1/4, Feedback 70%, OVDR drive, Filter sweeping down via CV |
| **Stutter freeze** | The Echo | Roll mode, Sync 1/16, slam Roll 0→max on the beat |
| **Throwable repeat** | The Echo | Triggered mode, 1/8 dotted, ~50% feedback, Trig mapped to controller |
| **Dub-spacey send** | Ripley | Sync 1/4d, Feedback 75%, Filter Hi-Lo darkening, Wobbler low, Reverb Serial |
| **Frozen ambient stutter** | Ripley | Time 1/16, Feedback 100%, Freeze ON, automate Bit/Rate Crush via Macro |
| **Wide multi-tap pad** | Ripley | Dual Delay 3/8 + 1/2, Width up, Filter Band w/ LFO Freq Shift, Reverb Parallel |
| **Juno-ish chorus pad** | Quartet | BBD, Mod Depth 40%, Rate 0.5 Hz, Noise Mod low, Width 80% |
| **Rhodes chorus** | Quartet | Chorus, Delay 12 ms, Mod 25%, Rate 0.5 Hz, Feedback 30% |
| **Shimmer widener** | Quartet | FFT, Size 2, Range >800 Hz, Mod moderate, Width 100% |
| **Granular bed** | Quartet | Grain, large Size, high Density, moderate Jitter (use on send) |

---

## CPU & Practical Notes

- **Convolution** in RV7000 Mk II is the biggest CPU cost — *bus your reverb sends*
- **Reverse** in RV7000 with Density >50% takes more CPU than necessary; ~50% is the sweet spot
- **Ripley** is heavier than The Echo because of its modulation matrix and integrated reverb — use The Echo when you don't need the extras
- **Quartet** FFT and Grain are notably heavier than Chorus/BBD
- The Echo and Ripley both have **breakout/external feedback** routings for inserting other devices into the feedback loop — classic move for distortion/EQ that grows with each repeat

---

## Common Pitfalls Across All Four

1. **Feedback runaway** — Ripley goes to 130%, The Echo to 100% (unity). Watch meters; arm Ripley's Feedback Limiter; consider a brick-wall after them.
2. **Mono vs stereo** — Many of these create stereo from mono. If a downstream channel folds to mono, the width vanishes. Check your bussing.
3. **Send vs insert confusion** — 100% Wet on sends. Otherwise dry signal phases against the channel's own dry path.
4. **CPU on convolution** — Bus your reverbs. One Convolution send beats ten Convolution inserts.
5. **Sync mismatch** — The Echo tops out at 1/2; Ripley at 8/4. If you need very long synced delays, use Ripley.
6. **Reverse on a send** — needs pre-fader send mode or it gets defeated by the dry path.
7. **Quartet still has dry at 100% Wet** — that's the nature of chorus. Use a send if you truly need wet-only.
8. **Multiply on Ripley** *always* re-pitches, even with Keep Pitch on. Surprise octave jumps if automated.
