# Reason 13: Distortion, Voice & Amp Effects
Based on Reason 13.4 documentation.

This skill covers Reason's character/distortion/voice family: Audiomatic Retro
Transformer, BV512 Vocoder, Neptune Pitch Adjuster + Voice Synth, Scream 4
Sound Destruction Unit, and Softube Amps (Guitar + Bass). These devices share
no signal model — Audiomatic is preset-driven character, BV512 is filterbank
analysis/resynthesis, Neptune is pitch detection + correction + harmony,
Scream is multi-algorithm distortion + body resonator, Softube Amps are amp +
cab modelling — but they all sit in the same "color and aggression" tier of
the rack.

## Comparison table

| Device | Type | Best for | Special routing |
|---|---|---|---|
| Audiomatic Retro Transformer | Preset-based character / lo-fi | Drums, full mixes, tracks needing instant vibe (Vinyl, Tape, VHS, Radio) | Insert only; CV on Transform & Dry/Wet |
| BV512 Vocoder | Vocoder (4/8/16/32/FFT bands) + graphic EQ | Classic vocoder vocals, talking synths, rhythmic modulation, FFT EQ | Two audio inputs: Carrier (synth) + Modulator (voice/drums) |
| Neptune | Mono pitch corrector + pitch shifter + polyphonic Voice Synth | Vocal tuning, formant gender shift, robot voice, MIDI-driven harmonies | MIDI route to Pitch Adjust OR Voice Synth; separate Voice Synth outs |
| Scream 4 | 10-mode distortion + 3-band Cut EQ + Body resonator | Drum smashing, bass grit, lo-fi crush, auto-wah body, lead destruction | Stereo insert; Auto CV out from envelope follower |
| Softube Amp | Guitar amp + cab modelling | DI guitar reamping, clean Twang, British Crunch, Rock, high-gain Lead | Mono-in / stereo-out insert; pre/amp/cab/post chain on the track |
| Softube Bass Amp | Bass amp + cab modelling | DI bass reamping, Modern punch, Vintage grit, sub emphasis | Same as Softube Amp; Ultra Lo/Hi shelf buttons |

Quick mental model:

- Need character without thinking? Audiomatic.
- Need a robot/talking synth? BV512.
- Need pitch fixed or harmony stacked? Neptune.
- Need things broken? Scream 4.
- Need a real guitar tone from a DI? Softube Amps.

---

## Audiomatic Retro Transformer

### Role
Rack Extension insert effect, preset-first design. Each preset is a chain of
hidden parameters; the Transform knob morphs through that chain. Inspired by
the Hipstamatic photo app — the point is "pick a look, dial it in" rather
than tweak 30 knobs.

### Front panel controls
- **Gain** (-INF to +12 dB) — input trim. Pushing it interacts strongly with
  presets that have built-in compression (Tape especially) and can become a
  distortion amount control.
- **Transform** — morph control. Not a wet/dry, not a depth — it modulates
  several hidden parameters at once and the meaning is entirely
  preset-dependent.
- **Dry/Wet** — parallel blend between unprocessed and transformed signal.
  Subtlety lives below 50%.
- **Volume** (-INF to +12 dB) — output makeup, especially needed if you
  pushed Gain.

### The 16 presets
Organized roughly by intensity. Row 1 is subtle, row 4 is destructive.

| Row | Presets |
|---|---|
| Subtle | Tape, Hi-Fi, Bright, Bottom |
| Moderate | Spread, Radio, VHS, Vinyl |
| Pronounced | MP3, Psyche, Cracked, Gadget |
| Extreme | Circuit, Wash, PVC, Eerie |

Character cheat sheet:

- **Tape** — analog tape recorder; saturation + slight wow.
- **Hi-Fi** — 70s/80s loudness-curve EQ flavor.
- **Bright** — high boost, bass tucked.
- **Bottom** — low-end thickening and tightening.
- **Spread** — stereo width with frequency shift.
- **Radio** — transistor radio bandlimiting.
- **VHS** — VHS camera mic character.
- **Vinyl** — surface noise, crackle, vinyl artifacts.
- **MP3** — bad-encoder swirl/aliasing.
- **Psyche** — psychedelic mod sweep.
- **Cracked** — blown speaker / heavy distortion.
- **Gadget** — hollow, robotic.
- **Circuit** — circuit-bend feel with bit-crushing.
- **Wash** — textural smear, experimental.
- **PVC** — sci-fi color.
- **Eerie** — waterphone-style atmosphere.

### CV
- **Transform CV** — bipolar; modulates Transform within the preset's defined
  range.
- **Dry/Wet CV** — bipolar; centered = manual setting respected.

### Audio I/O
Input L&R (mono goes to L); Output L&R. Internal stereo behavior depends on
preset (some presets are dual-mono, some genuinely stereo).

### Recipe — instant tape on a drum bus
1. Insert Audiomatic on the drum bus.
2. Select **Tape**.
3. Transform around 11 o'clock for warmth, 2 o'clock for visible compression.
4. Dry/Wet ~70% wet.
5. If transients flatten too much, drop Gain ~3 dB.

### Recipe — broken-radio interlude vocal
1. Insert Audiomatic on a vocal duplicate (parallel channel).
2. Select **Radio**.
3. Transform 100%.
4. Automate Dry/Wet from 0% to 100% over the bar before drop.

### Recipe — vinyl-noise atmosphere
1. Insert on the master or a duplicate of the mix.
2. Select **Vinyl** or **VHS**.
3. Keep Transform below 30% so noise sits under the music.
4. Use Dry/Wet to bring the artifact bed in/out.

### Do this
- **Do** use Audiomatic as the *last* tonal step on a track when you can't
  decide what's missing — pick a preset, walk away.
- **Do** insert it on a parallel mixer channel when you want to EQ/compress
  the effect signal independently.
- **Do** automate Transform for cheap risers and falls.

### Don't do this
- **Don't** stack heavy presets (Cracked, Circuit, PVC) on a full mix without
  checking the master meter — Tape preset specifically can drive into
  unwanted clip very fast.
- **Don't** reach for Audiomatic when you actually want surgical control;
  Scream 4 or BV512 EQ mode is more appropriate.
- **Don't** trust Transform to mean the same thing across two presets — it
  doesn't.

---

## BV512 Vocoder

### Role
Filterbank vocoder with a configurable number of bands, plus a graphic EQ
mode that reuses the same filterbank without the modulator path. Two audio
inputs: a **Carrier** (the thing you want to *hear*, usually a synth) and a
**Modulator** (the thing whose spectrum *shapes* the carrier, usually a
voice).

### Modes
- **Vocoder mode** — analyzes Modulator, applies its envelope/spectrum to
  Carrier, outputs the result.
- **Equalizer mode** — Modulator is ignored; Carrier passes through the
  filterbank as a manual-band graphic EQ (the lower display becomes a
  click-and-drag EQ).

### Band counts
- **4, 8, 16, 32** — conventional logarithmic filterbank. More bands = more
  intelligible but more "characterful." Fewer bands = vintage robotic feel.
- **FFT (512)** — Fast Fourier Transform analysis with linear band spacing.
  Crystal-clear speech, ~20 ms of latency, audible artifacts on extreme
  boost/cut, and unsuitable for transient material.

### Front panel
- **Bypass / On / Off** — three-state.
- **Band switch** — 4 / 8 / 16 / 32 / FFT.
- **Vocoder / Equalizer** mode switch.
- **Attack** — global envelope-follower attack on all bands.
- **Decay** — global envelope-follower release.
- **Shift** — moves carrier filters up/down in frequency relative to
  modulator (creates pitched/formant-shifted character).
- **HF Emph** — extra brightness on the carrier path.
- **Dry/Wet** — blend between modulator (often a clean voice) and the vocoded
  output. Useful for getting consonant clarity back.
- **Hold** — freezes current spectrum; can be triggered by MIDI/CV or a
  damper pedal for stutter/freeze effects.
- **Level meters** — separate meters for Carrier and Modulator.

### Lower display
Two stacked rows:

- **Top row (read-only):** modulator spectrum visualization — what the voice
  is doing right now.
- **Bottom row (interactive):** click/drag bars to set per-band gain. In EQ
  mode this *is* your EQ. In vocoder mode it's a per-band trim that biases
  the result.

### Routing — vocoder pattern (the daft-punk pattern)

This is the routing pattern you use 95% of the time:

1. Create the **Carrier synth** first (e.g. Subtractor with a bright sawtooth
   and slow/no filter envelope, sustained).
2. With the Carrier synth selected, **create BV512** — Reason auto-wires
   Carrier → BV512 input → mixer.
3. Flip the rack (Tab) and patch your **Modulator** (voice mic, vocal track,
   drum loop) into the BV512's **Modulator input**.
4. Front panel: Vocoder mode, 16 bands as a starting point.
5. Play MIDI on the carrier synth while audio plays/sings into the
   modulator.

The carrier provides *pitch and harmonics*. The modulator provides *time-
varying spectral shape*. Without modulator activity (silence), the output is
silent — the vocoder is gating the carrier through the modulator's envelope.

### Per-band CV
Every band exposes:
- A **band level CV out** — envelope-follower per band, useful as a
  sidechain/modulation source for other devices.
- A **band level CV in** — overrides that band's gain.
- A **Shift CV in** — modulate frequency shift over time.
- A **Hold gate in** — automate the freeze.

This makes BV512 a multi-band envelope follower as well as a vocoder.

### Mini-tutorial — classic vocal vocoder

Goal: a thick, intelligible "talking synth" line.

1. **Carrier:** Subtractor or Thor with detuned saws + square, polyphonic,
   filter wide open, slow attack, sustained envelope, HF Emphasis-friendly
   (don't pre-darken it). No filter modulation over time.
2. Insert **BV512** on the Subtractor output (or create BV512 with the synth
   selected — auto-wires).
3. Patch the **vocal track's audio out into BV512's Modulator input** on the
   back panel.
4. Front panel: **Vocoder, 16 bands**, Attack ~0–10 ms, Decay ~30–80 ms, HF
   Emph around 50%, Shift = 0.
5. Record/play a vocal phrase while playing chords on the carrier MIDI track.
6. If consonants are mush, raise Dry/Wet toward modulator (let some real
   voice through) or switch to **FFT mode** for clarity.
7. If it sounds thin: lower band count to 8, raise HF Emph.

### Mini-tutorial — FFT mode as a clean graphic EQ

1. Single audio source into the Carrier input.
2. **Equalizer mode**, **FFT (512)** band count.
3. With every bar at 0 dB the signal is bypassed cleanly.
4. Click-drag bars in the lower display to shape.
5. Avoid drastic boosts; FFT artifacts get audible above ~+10 dB.

### Recipe — rhythmic gate from drums
1. Drums into Modulator.
2. Sustained pad into Carrier.
3. 8 or 16 bands, fast Attack and Decay.
4. Result: pad chops in the rhythm of the drums, with each band gated by the
   matching drum frequency content.

### Recipe — vocoder reverb
1. Send a noise source to Carrier (e.g. Subtractor noise osc, sustained).
2. Drum bus into Modulator via aux send.
3. Long Decay (~500 ms+).
4. Result: drums shape a noise tail — a spectral reverb.

### Recipe — cross-patched bands (frequency inversion)
1. Patch band 1 OUT → band 16 IN, band 2 → band 15, etc. on the back.
2. Modulator low frequencies now drive carrier high bands and vice versa.
3. Useful for alien voice effects.

### Pitfalls
- **Consonant clarity** — fricatives ("s", "sh", "f") have weak harmonic
  content; the vocoder gates the carrier almost off during them. Fix by
  blending dry vocal via Dry/Wet, by using FFT mode, or by routing the
  modulator's HF separately to the output.
- **Carrier with envelope decay** — if your carrier dies, the output dies.
  Use sustained patches, fast attack, no filter envelope decay.
- **FFT latency** — ~20 ms. Don't use FFT on drums or as a real-time monitor
  on a singer tracking themselves.
- **Conventional bands aren't transparent** — even at flat band settings,
  4/8/16/32-band modes color the sound (phase). Use FFT for "clean."
- **Linear FFT spacing** — bands cluster in HF; bass control is coarse.
- **Carrier needs harmonics** — sine wave carrier produces near-silence;
  needs sawtooth/square/noise content for the vocoder to filter.

### Do this
- **Do** start with 16 bands and a sawtooth pad for the prototypical sound.
- **Do** use Hold + a Matrix gate for stutter/freeze.
- **Do** route per-band CV outs to filters or amp envelopes for spectral
  modulation outside the vocoder.

### Don't do this
- **Don't** use FFT mode for drum vocoding.
- **Don't** expect vocoded vocals to be intelligible without dry-vocal
  blending in dense mixes.
- **Don't** build a carrier with strong filter modulation; the vocoder will
  fight the filter sweep.

---

## Neptune Pitch Adjuster and Voice Synth

### Role
"A combined monophonic vocal pitch corrector, pitch shifter and polyphonic
voice synth." Insert or send effect. Designed for vocals but works on any
monophonic source (single instruments, speech). Two distinct engines inside
one device:

1. **Pitch Adjust + Transpose + Formant** — the *mono* engine that processes
   the input audio.
2. **Voice Synth** — the *poly* engine that resynthesizes the input pitch
   onto MIDI notes for harmony stacks. It has its own internal formant
   correction and ignores the Pitch Adjust/Transpose/Formant section.

### Pitch Adjust section
- **Correction Speed** — slow = transparent / natural; fast = robotic
  snapping. ~12 o'clock is "ideal in most situations" for natural correction.
- **Scale + Root Key** — pick a scale (Chromatic, Major, Natural Minor,
  Harmonic Minor, Dorian, Mixolydian) and root, or click target notes on the
  on-screen keyboard for a custom scale. The scale defines which target
  notes the algorithm snaps to.
- **Catch Zone** — ±20 to ±600 cents (default ±100). Defines how far off a
  note the input can be before the corrector decides which target to snap
  to. Wider catch zone = more aggressive coverage; narrow catch zone = only
  near-misses get caught.
- **Preserve Expression** — how much vibrato survives a fast Correction
  Speed. Min = no vibrato. Max = full original vibrato. The compromise knob
  for "tuned but human."

### Scale Memory
Four automatable slots store {Root, Scale, Catch Zone}. Switch between them
mid-song.

### Transpose
Independent ±12 semitone shift, ±50 cent fine tune. Works whether or not
Pitch Adjust is enabled. Works on non-pitched material too.

### Formant section
Formants = the resonant fingerprint of a voice (approximate vocal-tract
filter). Naive pitch shifting moves formants too, producing chipmunk/giant
artifacts.

- **Shift knob** — ±1 octave. **At 12 o'clock, formants are locked to the
  input** and don't move with pitch shifts (this is what you usually want for
  natural shifted vocals). Counterclockwise = lower formants (deeper / more
  male). Clockwise = higher formants (more soprano / "female").
- **Important:** Voice Synth has its own built-in formant correction and is
  *not* affected by the Formant section.

### Voice Synth mode
With MIDI routed to Voice Synth, incoming notes generate polyphonic
harmonies whose pitch tracks MIDI but whose timbre tracks the input voice.
Pitch Adjust, Transpose, and Formant are all bypassed for this engine —
Voice Synth lives parallel to them. Has its own dedicated stereo output for
processing harmonies separately on a mixer channel.

### MIDI routing
Two destinations on the device:
- **MIDI → Pitch Adjust** — incoming MIDI notes act as pitch targets, *
  bypassing the Scale/Root settings*. Monophonic.
- **MIDI → Voice Synth** — incoming MIDI plays harmony voices.

Both destinations respond to Pitch Bend and Vibrato (Mod Wheel).

### Pitch Bend & Vibrato
Front-panel wheels and CV inputs. Bend Range up to ±12 semitones. Vibrato
Rate is independent of host tempo.

### Output mixing
Two faders:
- **Pitched Signal** — Pitch Adjust / Transpose / Formant output.
- **Voice Synth** — harmony output, routable to main outs or to dedicated
  Voice Synth outputs.

### Input characteristic buttons
- **Low Freq** — accurate detection below ~44 Hz (deep male voice / bass
  instruments) at the cost of latency (longer cycles to lock pitch).
- **Wide Vibrato** — pitch detector ignores vibrato in the input so heavy
  vibrato singers don't confuse the algorithm.
- **Live Mode** — minimum latency for live monitoring; trades audio quality
  for speed.

### CV
- Inputs: Note, Gate, Bend, Vibrato, Formant.
- Outputs: Pitch CV (tracks adjusted pitch), Amplitude CV (envelope
  follower).

Note CV requires an accompanying Gate to actually drive pitch (same model as
synth voice gating).

### Common workflows

#### Vocal tuning (the main use)
1. Insert Neptune on the vocal track.
2. Set **Root + Scale** to the song key.
3. Correction Speed near 12 o'clock.
4. Preserve Expression around 50–70% (taste).
5. Enable Formant section, Shift = 0 (lock formants to input).
6. Watch the display: **yellow** line = input pitch, **green** = target,
   **orange** = distance.

#### Robot/T-Pain effect
1. Correction Speed all the way fast.
2. Preserve Expression at 0.
3. Pick a tight scale matching the song.
4. Result: hard pitch snapping, no vibrato.

#### MIDI-driven melody rewrite
1. Route MIDI to **Pitch Adjust**.
2. Play target notes from a MIDI clip; Neptune snaps the vocal to those
   notes regardless of original pitch.
3. Mono only — chords don't work here.

#### Backing harmonies (Voice Synth)
1. Route MIDI to **Voice Synth**.
2. Play harmony notes (polyphonic).
3. Break out **Voice Synth outputs** to a separate mixer channel and process
   independently (reverb, EQ, panning).
4. Lead vocal stays on Pitched Signal output.

#### Octave dub as a send effect
1. Disable Pitch Adjust.
2. Transpose +12 (or -12).
3. Use Formant Shift to taste so the doubled voice sounds natural.
4. Send-only: original vocal stays clean, duplicate plays an octave away.

#### Gender shift / formant only
1. Disable Pitch Adjust.
2. Transpose = 0.
3. Formant Shift counterclockwise for deeper, clockwise for higher.
4. Pitch unchanged, vocal-tract size changes.

#### Pitch-shifting non-pitched material (drums, speech)
1. Disable Pitch Adjust (no pitch to detect cleanly anyway).
2. Use Transpose + Formant to creatively shift.

### Recipe — natural correction "feels real"
- Correction Speed ~11–1 o'clock.
- Preserve Expression ~60%.
- Catch Zone ±100 cents (default).
- Formant on, Shift = 0.

### Recipe — hard tune
- Correction Speed at max.
- Preserve Expression at 0.
- Tight scale with only chord tones enabled on the keyboard.
- Catch Zone wide.

### Pitfalls
- **Stepped artifacts on fast passages** — fast Correction Speed produces
  visible "stairs" on quick runs. Slow it down or reduce Catch Zone.
- **Formant smear on big transpositions** — beyond a few semitones, formant
  correction gets weird. Always engage the Formant section for serious
  transposition.
- **Low-frequency latency** — Low Freq mode increases latency. Don't enable
  it for normal female/tenor vocals.
- **Wide vibrato fights detection** — singers with heavy vibrato confuse the
  detector unless you turn on Wide Vibrato mode.
- **Voice Synth ignores Formant section** — if you want to tweak Voice Synth
  formants, you can't; it has its own internal correction.
- **Polyphonic source = unpredictable** — chord/strum input, complex
  inharmonic sounds, dense polyphony — pitch detection won't track
  reliably. Neptune is a *monophonic* corrector by design.
- **Note CV without Gate** — pitch control won't engage; you must drive Gate
  alongside Note.

### Do this
- **Do** set the right Root + Scale before tweaking speed.
- **Do** use Formant section, Shift = 0 for transparent pitch shifts.
- **Do** route Voice Synth out to its own mixer channel so harmonies don't
  step on the lead.
- **Do** automate Scale Memory slots if the song modulates.

### Don't do this
- **Don't** crank Correction Speed by default — slow is more natural.
- **Don't** stack Pitch Adjust *and* Voice Synth assuming they share params;
  Voice Synth ignores the rest of the device.
- **Don't** feed Neptune polyphonic guitar/piano and expect tracking.

---

## Scream 4 Sound Destruction Unit

### Role
Stereo in/out distortion + tone-shaping insert effect. Three independent,
separately bypassable sections in series:

1. **Damage** — 10 distortion algorithms.
2. **Cut** — 3-band EQ (post-Damage).
3. **Body** — resonant body / cabinet / formant simulator with envelope
   follower.

### Damage controls
- **Damage button** — section on/off.
- **Damage Control knob** — input gain into the algorithm. *This is the
  amount knob.* Lowering it changes the *character* of the distortion, not
  just the level — so use Master to balance output, not Damage Control.
- **Damage Type** — one of 10 algorithms (below).
- **P1 / P2** — two parameter knobs whose meaning depends on the algorithm.

### The 10 Damage modes

| # | Mode | Sound | P1 | P2 |
|---|---|---|---|---|
| 1 | **Overdrive** | Analog, dynamic-responsive, soft crunch | Tone (CW = brighter) | Presence (high-mid lift) |
| 2 | **Distortion** | Denser, thicker, more constant character | Tone | Presence |
| 3 | **Fuzz** | Bright fuzz; punchy at low Damage too | Tone | Presence |
| 4 | **Tube** | Tube amp character | Contour (HP-like tone) | Bias (asymmetric clip when extreme) |
| 5 | **Tape** | Soft tape clipping + built-in compression | Speed (CW = brighter, faster tape) | Compression ratio |
| 6 | **Feedback** | Distortion in a feedback loop, unpredictable | Size (loop length) | Frequency (which overtones resonate) |
| 7 | **Modulate** | Self-multiplication + filter; ringing/resonant | Ring (filter Q) | Frequency (filter cutoff) |
| 8 | **Warp** | Distorts and multiplies signal with itself | Sharpness (low = soft, high = harsh) | Bias (re-introduces fundamental) |
| 9 | **Digital** | Bitcrusher + sample rate reduction | Resolution (CW = full, CCW = 1-bit) | Sample rate reduction |
| 10 | **Scream** | Fuzz preceded by resonant bandpass | Tone (CW = brighter) | Filter frequency (high Q, wah-friendly) |

Algorithm picking guide:

- Subtle bus warmth → **Tape**.
- Guitar-like drive → **Overdrive** or **Tube**.
- Cab-replacement-style aggression on bass → **Distortion** or **Tube**.
- Lo-fi / vintage digital → **Digital**.
- Ring/metallic body → **Modulate** or **Warp**.
- Wah/talking lead → **Scream** with P2 modulated.
- Risers/hits → **Feedback** (use carefully).
- Bright fuzz lead → **Fuzz**.

### Cut section (EQ)
- **Cut button** — on/off.
- **Lo / Mid / Hi** sliders — each ±18 dB shelving/peak. Sits *after* Damage,
  so it shapes the distorted tone, not the dry input.

### Body section
Resonant filter body / cabinet simulator with envelope follower.

- **Body button** — on/off.
- **Body Type** — A through E, five different formant/cab character models.
- **Reso** — resonance amount (more CW = ringier).
- **Scale** — emulated body size. **Inverted: CW = smaller body**, CCW =
  larger.
- **Auto** — envelope-follower amount applied to Scale. Higher input level
  shrinks the body (raises the resonance), great for auto-wah.

Body Type B is the canonical "wah" voicing.

### Master Level
Output trim. Doesn't affect the distortion character — use Master, not
Damage Control, to manage output level.

### CV
- **CV In:** Damage Control, P1, P2, Scale.
- **CV Out:** Auto (the envelope follower) — useful as a sidechain to filter
  other devices.

### Recipe — drum bus crunch
1. Damage on, **Tube**, Damage Control ~30%.
2. P1 (Contour) ~50%, P2 (Bias) ~30% for slightly asymmetric edge.
3. Cut: small Lo cut (-2), small Hi boost (+1).
4. Body off.
5. Master to taste.

### Recipe — bass distortion that still has lows
1. Damage on, **Distortion**, Damage Control ~50%.
2. P1 Tone ~70%, P2 Presence ~50%.
3. Cut: Lo at 0 (don't lose lows), Mid +2 for grind.
4. Body off (otherwise low end thins out via the resonant filter).
5. Parallel-blend with the dry bass on the mixer for definition.

### Recipe — auto-wah on a clav
1. Damage off.
2. Body on, Type **B**, Reso ~70%, Scale ~50%, Auto ~70%.
3. Louder notes shrink the body and brighten — instant envelope wah.

### Recipe — lo-fi 8-bit
1. Damage on, **Digital**.
2. P1 Resolution at ~30% (low bits), P2 Sample rate reduction ~40%.
3. Cut: Hi -3 to tame aliasing.
4. Body off.

### Recipe — unstable feedback hit
1. Damage on, **Feedback**.
2. P1 Size mid, P2 Frequency tweak until it sings.
3. Automate Damage Control from 0 to 80% as a riser, then drop.
4. Always have a safety limiter downstream — feedback can run away.

### Pitfalls
- **Damage Control vs Master** — lowering Damage Control changes character.
  Always trim with Master.
- **Feedback runaway** — Mode 6 can self-oscillate; use a limiter, save
  before automating.
- **Body kills bass** — bandpass-style Body with low Scale (= big body) +
  high Reso can hollow out low end. Bypass Body for bass tracks unless you
  want that.
- **Overdrive vs Distortion confusion** — Overdrive *responds to dynamics*
  (cleaner on quiet passages), Distortion is *constant*. Pick based on
  whether you want the source's dynamics audible.
- **Audio clip indicator** — only the Reason Hardware Interface output
  indicates true clip; intermediate Master Level red doesn't always mean
  internal clip.
- **CV-modulated P1/P2** — meaning depends on algorithm, so changing Damage
  Type while CV is patched produces unexpected sweeps. Re-check P1/P2 after
  switching modes.

### Do this
- **Do** put Scream on a parallel send if you want grit + clarity.
- **Do** automate Damage Type for transitions (the algorithm shifts are
  audible).
- **Do** use the Auto CV out to sidechain a filter elsewhere — Scream is a
  solid envelope follower.

### Don't do this
- **Don't** rely on Damage Control as a volume knob.
- **Don't** leave Feedback mode on a stem at high P1/P2 unattended.
- **Don't** use Body on bass without checking the low-end balance.

---

## Softube Amps (Guitar Amp + Bass Amp)

### Role
Amp + cabinet modelling. Two devices ship: **Softube Amp** (guitar) and
**Softube Bass Amp**. Use them as inserts on a DI'd guitar/bass track. They
let you monitor a usable amp tone during tracking and re-shape it freely
later (reamping in software).

### Softube Amp (Guitar) — amp models
- **Twang** — clean American (Fender-style), country/blues territory.
- **Crunch** — British 60s; clean to crunch with clarity (Vox/JTM-style
  voicing).
- **Rock** — warm tube distortion, classic rock midrange.
- **Lead** — high-gain, sustained leads, power chords.

### Softube Amp — cab models
- **Bright** — 2x12 with on-axis dynamic mic.
- **Room** — 2x12 with off-axis mic + stereo room ambience.
- **Fat** — 4x12 with German condenser; full body.
- **Tight** — 4x12 with large-diaphragm dynamic; mids scooped.

### Softube Amp — controls
- **Gate** threshold — input noise gate.
- **Boost** — switchable extra crunch/gain stage in front.
- **Gain** — input/preamp gain.
- **Poweramp Gain** — power section drive (separate from preamp; classic
  master-volume-style sag).
- **Bass / Mid / Treble** — tone stack.
- **Master Volume** — output.

### Softube Bass Amp — amp models
- **Modern** — contemporary tube, clarity and punch.
- **Vintage** — dark, gritty, cuts through dense mixes.

### Softube Bass Amp — cab models
- **Dark** — 8x10 classic, on-axis large-membrane dynamic.
- **Bright** — British 4x12 off-axis.
- **Room** — 4x10 with condenser at distance.

### Softube Bass Amp — controls
- **Drive** — input gain.
- **Bass / Middle / Treble** with selectable Mid Frequency voicing.
- **Ultra Lo / Ultra Hi** buttons — extreme shelf emphasis switches.
- **Master Volume** — output.

### Audio I/O
Stereo in/out. Mono input on Left only still produces stereo output (cabs
have stereo character, especially the Room cabs). CV inputs let you
automate gain and volume params.

### Mini-tutorial — guitar signal chain

The pragmatic chain on a guitar audio track:

```
DI guitar input
  -> [pre-effects: tuner, comp, gate, wah/octave/pitch]
  -> [Softube Amp (amp model + cab model integrated)]
  -> [post-effects: time-based — delay, reverb, modulation]
  -> Mix bus
```

Notes:

1. **Pre-effects (in front of the amp)** — dynamics and pitch-domain effects
   go *before* the amp so the amp distorts the processed signal: comp, gate,
   wah, octaver, fuzz pedal sims, EQ used to shape what hits the amp.
2. **Amp + Cab** — Softube Amp internally bundles amp and cab; pick both on
   the device. There is no separate "cab loader" device required.
3. **Post-effects (after the amp)** — time-based effects sound natural after
   the cab: delay (RV-7000 / DDL-1), reverb, chorus/flanger/phaser if you
   want a "wet" sound rather than driven modulation, stereo widening.

### Mini-tutorial — DI reamping workflow

1. **Track DI clean.** Record the unprocessed DI guitar to an audio track
   with no insert (or with a transparent monitor amp on a parallel monitor
   send).
2. While tracking, monitor through Softube Amp on a *parallel mixer
   channel*, so the recorded audio file stays clean.
3. After tracking, **insert Softube Amp on the DI track** (or on a duplicate
   track for parallel) — now you can change amp model, cab, gain, EQ
   independently of the take.
4. Try multiple amps: duplicate the audio track, put Twang on one and Lead
   on another, blend on the mixer for "two-amp" sound.

### Mini-tutorial — clean Twang
1. Amp = **Twang**, Cab = **Bright**.
2. Gain ~30%, Poweramp Gain ~40%, Master to taste.
3. Bass ~50%, Mid ~60%, Treble ~55%.
4. Boost off, Gate off (clean tones don't need it).
5. Add slap-back delay post-amp.

### Mini-tutorial — British crunch
1. Amp = **Crunch**, Cab = **Fat** or **Room**.
2. Gain ~55%, Poweramp Gain ~50%.
3. Bass ~45%, Mid ~70%, Treble ~50%.
4. Boost optional for solo lift.
5. Light plate reverb post-amp.

### Mini-tutorial — high-gain Lead
1. Amp = **Lead**, Cab = **Tight**.
2. Gain ~80%, Poweramp Gain ~60%, Boost on.
3. Gate threshold raised to kill noise floor.
4. Bass ~40% (don't let it fart out), Mid ~30% (scoop for that tight chunk),
   Treble ~60%.
5. Master to taste; expect a lot of compression in the model.
6. Add tape delay post-amp at ~1/8 dotted, low feedback.

### Mini-tutorial — bass Modern punch
1. Bass Amp = **Modern**, Cab = **Bright**.
2. Drive ~30% (clean) or ~60% (gritty).
3. Bass ~55%, Middle ~60% with mid frequency tuned to where the bass needs
   focus, Treble ~50%.
4. Ultra Hi on for finger noise/string definition; Ultra Lo on if you want
   sub heft.
5. Master to taste.

### Mini-tutorial — bass Vintage grit
1. Bass Amp = **Vintage**, Cab = **Dark**.
2. Drive ~70%.
3. Bass ~50%, Middle ~70%, Treble ~40%.
4. Ultra Lo off (Vintage + Dark already has heft, don't double up).

### Pitfalls
- **Amp + Cab phase / double-cab** — the Softube Amp ships amp *and* cab
  together as one model. Don't add a second cab IR/sim downstream — you'll
  get phasey, smeared tone.
- **Ice-pick treble** — the Lead model with bright cabs and high Treble can
  fatigue ears. Pull Treble back, check on multiple speakers.
- **Mud at low gain on high-gain amps** — running Lead at low Gain doesn't
  make it sound clean, it makes it sound undefined. For clean, switch
  models, don't lower gain on a high-gain amp.
- **Mono input → stereo cab** — the cab adds stereo image; if you sum to
  mono later, expect comb filtering. Decide early.
- **Tracking with effects baked in** — if you record through Softube Amp
  *committed*, you lose the reamping freedom. Track DI; monitor through
  Softube; commit only when you're sure.
- **Gate too aggressive** — chops sustained notes/feedback. Lower threshold
  or disable for clean tones.
- **Master Volume is post-cab** — does not interact with poweramp drive.
  Use Poweramp Gain for sag, not Master.

### Do this
- **Do** track clean DI, reamp with Softube Amp on the track.
- **Do** duplicate the DI track to layer two amp models.
- **Do** put time-based effects (delay/reverb) *after* the amp.
- **Do** put dynamics/wah/pitch *before* the amp.

### Don't do this
- **Don't** stack a second cab IR after Softube Amp.
- **Don't** print the amp tone unless you've committed to it for the mix.
- **Don't** use the Lead model and pull gain down to get clean — change the
  amp model.

---

## Quick decision recap

- "Make this drum loop sound like 1985" → **Audiomatic — VHS or Vinyl**.
- "Make a synth pad talk a vocal phrase" → **BV512 vocoder, 16 bands**.
- "Tune this vocal naturally" → **Neptune, slow speed, scale + root, Formant
  on**.
- "Make these drums sound destroyed" → **Scream 4, Tube or Tape on the bus,
  Master to recover level**.
- "I have a DI guitar, give me a Marshall" → **Softube Amp, Crunch + Fat**.
- "I want a robot voice" → **Neptune fast speed, Preserve Expression 0** (or
  **BV512 with a saw carrier** for a different flavor).
- "Auto-wah" → **Scream 4 Body section, Type B, high Auto**.
- "Stereo cab on bass" → **Softube Bass Amp, Modern + Bright, Ultra Hi on**.

When in doubt: Audiomatic for vibe, Scream for damage, BV512 for talking,
Neptune for tuning, Softube for guitar/bass tone.
