# Reason 13: Utility Effects
Based on Reason 13.4 documentation.

A practical reference for the small but essential "glue" devices in Reason 13: Sidechain Tool, Stereo Tool, Gain Tool, and the half-rack vintage-era effects (PEQ-2, COMP-01, D-11, ECF-42, CF-101, DDL-1, RV-7, PH-90, UN-16). These are the workhorses that make the rack actually mix-able — gain staging, M/S-style width tricks, sidechain key generation, and quick-and-dirty insert effects.

## Overview Table

| Device | Format | Role | Best at | Skip when |
|---|---|---|---|---|
| **Sidechain Tool** | Full rack | Pumping / ducking generator + sidechain compressor | Tempo-synced kick-pump, MIDI-triggered ducking, key signal for compressors that lack SC input | Surgical bus compression — use Master Bus Comp / MClass Comp |
| **Stereo Tool** | Full rack | Phase-safe stereo widener + comb-filter spectrum tweak | Widening mono synths, splaying high-end, mono check | True M/S surgery — use a third-party plugin (Stereo Tool is widener-first, no separate Mid/Side controls) |
| **Gain Tool** | Full rack | Gain stage, mixer, crossfader, panner, router | Combinator macros, automation, in-rack faders, Mute / Inv / Swap / Mono utilities | When you just need a trim — but it's still the cleanest option |
| **PEQ-2** | Half rack | 2-band parametric EQ | Quick tonal carving, CV-modulated frequency sweeps | Mastering EQ — use MClass Equalizer |
| **COMP-01** | Half rack | Auto-makeup compressor | Set-and-forget leveling on a single source | Sidechain compression, mix-bus glue |
| **D-11** | Half rack | Foldback distortion | Subtle warmth through to thrash | Tube/tape modeling — use Scream 4 |
| **ECF-42** | Half rack | Envelope-controlled multimode filter | Pattern-triggered filter sweeps with Matrix/RPG-8 | Smooth modulated sweeps without retrigger — use Thor filter |
| **CF-101** | Half rack | Chorus / flanger | Wide modulation, simple chorus | High-end vocal doubler — use UN-16 or third-party |
| **DDL-1** | Half rack | Mono delay with pan | Tempo-synced echoes, slap delay | Stereo ping-pong — use The Echo |
| **RV-7** | Half rack | Algorithmic reverb | Lo-fi character ambience, gated verbs | Convolution-grade space — use RV7000 MkII |
| **PH-90** | Half rack | 4-stage phaser | Sweeping pad / guitar phasing | Vintage analog phaser modeling — use third-party |
| **UN-16** | Half rack | Detuned-voice unison chorus | Synth thickening, supersaw-style spread | When you need traditional LFO chorus — use CF-101 |

> **Half rack vs full rack rule of thumb:** Half-racks are CPU-light, fast to dial in, and have the right "vibe" for retro tracks. Full-rack siblings (MClass series, RV7000 MkII, The Echo, Scream 4) are deeper, cleaner, and the right call for the mix bus or anything that demands precision. Half-racks shine on inserts inside Combinators where space and CPU matter.

---

## Sidechain Tool

A full-rack device that generates ducking curves *or* operates as a regular sidechain compressor. The "Swiss Army knife" for any place you'd reach for a side-chain compressor, plus a few you wouldn't.

### Three operating modes

| Mode | Trigger source | Behavior |
|---|---|---|
| **Auto Pump** | Sequencer tempo | Built-in ducking curve synced to a rate from 8 bars to 1/32 |
| **Trigger** | MIDI note, audio threshold, or CV | Ducking curve fires on each trigger event |
| **Sidechain** | External audio at SC input | Behaves as a traditional sidechain compressor |

### Ducking curve controls (Auto Pump and Trigger)

- **Attack / Hold / Release** — time of each curve segment
- **Attack Shape / Release Shape** — bend the curves from linear to exponential / log
- **Slide** — shifts the curve in time without changing its shape (useful when the pump feels late or early against the kick)
- **Ducking Amount** — how far down the curve attenuates (in dB)
- **Preset selector** — quick library of curve shapes
- **Visual editor** — drag the blue square handles in the display to reshape the curve

### Sidechain mode controls

- **Threshold**: -52 dB to 0 dB
- **Ratio**: 1:1 to ∞:1
- **Attack**: 1 ms to 1 s
- **Release**: 20 ms to 5.02 s
- **Gain (makeup)**: ±24 dB
- **Frequency band filter** — restricts compression to a specific band

### Key features

- **Band Mode** — only ducks a frequency range. Classic move: duck *only* the bass when the kick hits, leaving the rest of the mix intact.
- **Send Mode** — outputs only the processed signal so you can use it on an FX return.
- **Listen** button — solos the sidechain signal so you can hear what's keying the compressor.
- **Audio/MIDI switch** (Trigger mode) — pick whether incoming audio threshold or MIDI note events fire the curve.

### Connections

| Type | Jacks |
|---|---|
| Audio In | Main L/R, Sidechain L/R |
| Audio Out | Out L/R |
| CV In | Pump Amount, Attack, Attack Shape, Hold, Release, Release Shape, Band Freq, Trig CV |
| CV Out | Trig (gate), Hold (gate), End (gate), Curve Out (continuous, **negative**), Inverted (continuous, **positive**) |

> **Watch out:** Curve Out is *negative* CV, Inverted is *positive* CV. If you're patching the curve into a destination expecting positive modulation (most filter cutoff inputs, etc.), use the Inverted output.

### Quick recipes

> **Recipe — Classic four-on-the-floor pump (no kick routing required):**
> 1. Insert Sidechain Tool on the bass/pad/synth track.
> 2. Mode = Auto Pump, Rate = 1/4.
> 3. Ducking Amount ~ -8 to -12 dB.
> 4. Attack short, Release ~80% of the rate.
> 5. Tweak Slide if the pump sits ahead/behind the beat.

> **Recipe — Generate a sidechain key for a compressor that has none:**
> 1. Use Sidechain Tool in **Trigger mode** with the kick MIDI routed in (or audio at the SC input, threshold set).
> 2. Patch **Curve Out** (or **Inverted**, depending on polarity needed) to the target compressor's gain or threshold CV input.
> 3. Now any compressor in the rack — even one without a sidechain jack — can be ducked by the kick.

> **Recipe — Bass-only ducking under a kick:**
> 1. Sidechain Tool on the bass channel, **Sidechain mode**.
> 2. Route kick to the SC input (use a Spider Audio Splitter to copy the kick).
> 3. Enable **Band Mode**, set the band around 60–120 Hz.
> 4. Threshold tight, Ratio 4:1+. Result: only low-bass content ducks; pluck transients and mid-range body stay put.

> **Recipe — De-essing with the band filter:**
> 1. Sidechain mode, sidechain input fed from the same vocal (use a Spider Audio Splitter pre-fader).
> 2. Band Mode on, frequency 5–8 kHz.
> 3. Hit the **Listen** button while you tune the band — you should mostly hear the sibilants.
> 4. Set ratio 4:1+, attack ~3 ms, release ~80 ms.

### Common pitfalls

- **Slide drift** — When you change the Rate, Slide doesn't auto-rescale. Re-check it.
- **Auto Pump on busy material** — Auto Pump ignores the actual transients, so on a drum loop with shuffled hits the pump can feel mechanical. Switch to Trigger or Sidechain mode and key off the actual kick instead.
- **Polarity flip** — Patching Curve Out where Inverted is wanted causes "anti-pumping" (the destination *louder* on the beat). Always check both outs.
- **Forgetting Listen is on** — Listen is a monitoring solo. Disable it before you bounce.

---

## Stereo Tool

Phase-safe stereo widener built around mid/side-style processing. Despite the name and category, this is *primarily a widener* — there is no separate Mid Gain / Side Gain pair, and there are no Balance or M/S-encode/decode buttons. Don't reach for this expecting a third-party-style M/S surgical tool; do reach for it when you need to splay a synth, fatten a vocal, or mono-check a bus.

### Controls

| Control | What it does |
|---|---|
| **Widening** | Spread amount. 0% = original. Higher = wider. Phase-safe — works on mono *or* stereo input. |
| **Low Bypass** | Sets a frequency below which the widening is bypassed. Keeps lows mono and tight. |
| **Frequency Adjust** | Tunes the device's internal comb filter — shifts the spectral character of the stereo spread. Use to compensate when widening makes one side dull or honky. |
| **Mono** button | Forces the output to mono — perfect for mono-checking without unwiring the rack. |

### Connections

- **Audio In** — L and R. For mono sources, connect only to L.
- **Audio Out** — stereo L/R.
- **CV In** — Widening, Frequency Adjust. (No CV outputs.)

### Tricks and recipes

> **Recipe — Mono synth into wide stereo without phase issues:**
> 1. Patch the mono synth into the L input.
> 2. Stereo Tool after it.
> 3. Widening to taste (50–150% is the sweet spot).
> 4. Low Bypass to ~150–200 Hz so your kick/sub stays centered.

> **Recipe — High-end air on a vocal:**
> 1. Vocal -> Stereo Tool.
> 2. Low Bypass at 1–2 kHz so body and presence remain mono and stable.
> 3. Modest Widening (~20–40%) and a slight Frequency Adjust tweak for sheen.

> **Recipe — Stereo chorus from an LFO:**
> 1. Patch a triangle LFO (from Thor or PolyStep) into the **Frequency Adjust CV In**.
> 2. Low LFO rate (~0.3–1 Hz). The drifting comb-filter creates a chorus-like stereo movement on top of the widener.

> **Recipe — Mono check:**
> 1. Slap a Stereo Tool on the master out (or any bus you want to test).
> 2. Hit **Mono** to collapse the stereo image.
> 3. Anything that disappears or thins out is a phase-cancelation problem upstream.

### Common pitfalls

- **Bass widening = mud and disappearing kicks on big systems.** Always set Low Bypass for ≤ ~150 Hz on anything that includes sub content.
- **Stacking wideners.** Two Stereo Tools in series multiplies the smearing and sounds *worse*, not wider. Use one, late in the chain.
- **Mono incompatibility.** Aggressive widening can sound great in stereo and *evaporate* in mono. Always mono-check (use the Mono button on a copy / on the output).
- **Comb-filter coloration.** Frequency Adjust changes the *tone*, not just the width. Wide settings can dull the top end — re-check after big Widening moves.

---

## Gain Tool

The cleanest gain stage in Reason. Gain Tool is a Combinator-builder's best friend: a single device that can be a fader, a panner, a small mixer, an X-fader, or a router — without burning a mixer channel.

### Two axes: Input Mode and Output Mode

The device has an **Input Mode** and an **Output Mode** that you set independently.

#### Input Modes

| Mode | What goes in | What it does |
|---|---|---|
| **Gain** | Main L/R only | Single signal in, single signal out, with gain |
| **Mix** | Main L/R + Aux L/R | Two-channel mixer with separate gains |
| **X-Fade** | Main L/R + Aux L/R | Two channels with independent gains *and* a crossfader between them |

#### Output Modes

| Mode | What it does |
|---|---|
| **Width/Pan** | Stereo width + pan. Width is phase-safe (it operates on the channel difference). |
| **Dual Pan** | Pan L and R independently — lets you collapse / splay channels at the output |
| **Router** | Crossfade between **Main Out** and **Split Out** — used for parallel routing |

### Specs and quick reference

- **Gain range:** −∞ to +18.1 dB (0–800%)
- **Inputs:** Main L/R, Aux L/R
- **Outputs:** Main Out L/R, Split Out L/R
- **Front-panel utility buttons:** Mute, Inv L, Inv R, Swap L-R, Mono
- **Meters:** Output level meters reflect the active Output Mode
- **CV In:** Main Gain, Aux Gain, X-Fade, Width/Pan, Pan direction, Output Router (each with attenuator)

### Quick recipes

> **Recipe — Combinator fader macro:**
> 1. Inside a Combinator, insert Gain Tool on the output of the device chain.
> 2. Mode = Gain.
> 3. Right-click the Combinator's Rotary 1 -> Edit Mode -> assign to Gain Tool's Main Gain.
> 4. Now Rotary 1 is a real fader the Combinator presets can carry.

> **Recipe — Wet/dry crossfade for any effect:**
> 1. Send the dry signal to **Main In**.
> 2. Send the wet (post-FX) signal to **Aux In**.
> 3. Input Mode = **X-Fade**.
> 4. Automate the X-Fade slider for parallel-style wet/dry control.

> **Recipe — A/B reference switcher:**
> 1. Two mix-bus signals into Main and Aux.
> 2. Input Mode = X-Fade.
> 3. Bind X-Fade to a button macro: hard-left = A, hard-right = B. Instant A/B comparison.

> **Recipe — Parallel processing send:**
> 1. Output Mode = Router.
> 2. Main Out -> dry chain.
> 3. Split Out -> heavily processed parallel chain.
> 4. Crossfade or automate the Router CV to morph between dry-only and parallel.

> **Recipe — Quick polarity / mono-compat check:**
> 1. On the suspect track: drop a Gain Tool.
> 2. Hit **Inv L** while in stereo: if the track sounds louder/wider, it had phase issues already.
> 3. Hit **Mono**: if the level drops drastically, something is anti-phased upstream.

> **Recipe — Stereo channel swap on a bad print:**
> 1. Gain Tool inserted.
> 2. **Swap L-R** button. Done. (Saves a manual cable swap.)

### Common pitfalls

- **Gain Tool boosts to +18.1 dB / 800%.** That's plenty of headroom to clip downstream devices. Watch the meters — gain staging works downstream just like upstream.
- **Mute on Gain Tool ≠ track mute.** It mutes only the Gain Tool output. If automation is running on the parameters, those still update — useful for "soft mutes" but surprising if you forget.
- **Swap L-R is destructive in the rack-flow sense.** Anything downstream that assumed a particular channel orientation (a stereo delay with different feedback per side, for instance) will now be reversed.
- **Width/Pan width is *not* a Stereo Tool replacement.** It's mid/side-style on the channel difference and works inside the existing image; for actual *widening beyond the image*, use Stereo Tool.

---

## Half-Rack Effects

The half-rack devices are the original Reason 1.0–era effects: small footprint, light CPU, and a particular vintage character. They're grouped below by function.

> **Half-rack vs full-rack policy:**
> - Use **half-rack** for inserts inside Combinators, retro/lo-fi tracks, when you want the specific period-correct sound (DDL-1 has a sound, RV-7 has a sound), and when CPU matters because the patch has a lot of polyphony or instances.
> - Use **full-rack** (MClass series, The Echo, RV7000 MkII, Scream 4, Pulveriser) for the master bus, anything sitting in the spotlight, or when you need the deeper feature set (convolution IRs, multi-band, M/S).

### EQs

#### PEQ-2 — Two Band Parametric EQ

Two parametric EQ bands (A and B), each with Frequency, Q, and Gain. That's the entire device.

**Parameters per band:**
- **Frequency** — 31 Hz to 16 kHz
- **Q** — bandwidth (narrow ↔ wide)
- **Gain** — ±18 dB boost/cut

**CV In:** Freq 1, Freq 2 (CV-modulate either band's frequency)

**Use it for:**
- Quick problem-frequency notch (high Q, deep cut)
- Broad tone shaping when you don't need 4+ bands
- CV-modulated wahs and sweeps via the Freq CV inputs (run an LFO into Freq 1)

**Reach for MClass Equalizer instead when:** you need a high-pass/low-pass, shelves, more than 2 bands, or you're EQing the master bus.

> **Recipe — CV-modulated wah from PEQ-2:**
> 1. PEQ-2 inserted. Band A: Frequency ~600 Hz, Q narrow, Gain +12 dB.
> 2. LFO (from Thor or a Matrix Curve CV) into **Freq 1 CV** with attenuator at ~50%.
> 3. Tempo-sync the LFO. Result: synced wah without burning a filter device.

### Compressor / Dynamics

#### COMP-01 — Auto Make-up Gain Compressor

The classic Reason vintage compressor. Auto-makeup means there's no output gain knob — the device compensates for the gain reduction internally.

**Parameters:**
- **Ratio** — 1:1 to 16:1
- **Threshold**
- **Attack**
- **Release**
- **Gain meter** — shows reduction (or auto-makeup gain) in dB

**CV In:** None.

**Use it for:**
- "Set and forget" leveling on a single source (vocal, bass, lead synth)
- Adding a bit of weight/cohesion on a sub-mix bus
- Inside a Combinator where you want compression and don't have CPU/space for MClass

**Reach for MClass Compressor / Master Bus Comp instead when:** you need sidechain input, knee shape control, soft-knee mastering, or precise output gain.

> **Recipe — COMP-01 on a vocal:**
> 1. Ratio 4:1, Threshold so you're hitting -3 to -6 dB on the loudest words.
> 2. Attack medium (let consonants through), Release fast enough that it recovers between phrases.
> 3. If it's still uneven, *follow it with a second COMP-01* with low ratio (~2:1) and slower attack — series compression instead of one heavy stage.

### Modulation

#### CF-101 — Chorus / Flanger

Combined chorus and flanger. The shorter delay times = flanger character; longer = chorus.

**Parameters:**
- **Delay**
- **Feedback**
- **LFO Rate**
- **LFO Sync** (tempo sync on/off)
- **LFO Mod Amount**
- **Send Mode** (output wet only)

**CV In:** Delay, Rate

**Use it for:**
- Subtle stereo shimmer on synths and pads
- Flanging guitars (short Delay, high Feedback)
- A faux-vibrato when set with very low LFO Mod and slow Rate

#### PH-90 — Phaser

Four-stage phaser. The classic one for swept pads.

**Parameters:**
- **Frequency** — center of the notches
- **Split** — distance between notches
- **Width** — width of each notch
- **LFO Rate**
- **LFO Sync**
- **LFO Freq. Mod** — how deep the LFO sweeps the notch frequencies
- **Feedback**

**CV In:** Freq, Rate

**Use it for:**
- Pad and string sweeps
- Guitar phasing (insert mode)
- Combined with feedback for resonant, near-self-oscillation hisses

> **Recipe — Tempo-synced pad sweep:**
> 1. PH-90 on a pad.
> 2. LFO Sync on, Rate = 1/2 or 1 bar.
> 3. LFO Freq. Mod ~70%, Feedback ~30%.
> 4. Split and Width to taste — wider Split for a roomier sweep.

#### UN-16 — Unison

Detuned-voice chorus. Simulates 4, 8, or 16 detuned voices spread across the stereo field.

**Parameters:**
- **Voice Count** — 4 / 8 / 16
- **Detune** — how far apart the voices drift
- **Dry/Wet**

**CV In:** Detune

**Use it for:**
- Thickening mono synths (great in front of Stereo Tool for monstrous-wide leads)
- Faux-supersaw out of a single Subtractor
- Vocal doubling (low voice count, low detune)

> **Recipe — Subtractor into supersaw:**
> 1. Subtractor with a single saw, mono out.
> 2. UN-16 — 16 voices, Detune ~30%, Dry/Wet 100%.
> 3. (Optional) Stereo Tool after, Widening 50%, Low Bypass 200 Hz.

### Delay / Reverb

#### DDL-1 — Digital Delay Line

A mono delay with a pan control. The classic Reason delay sound — *it has a sound*. Slightly dark, period-correct.

**Parameters:**
- **Delay time** — note-based steps **or** milliseconds (switchable)
- **Unit** — Steps / MS toggle
- **Step length** — 1/16 or 1/8T (when in Steps mode)
- **Feedback**
- **Pan**
- **Wet/Dry**

**CV In:** Pan, Feedback

**Use it for:**
- Tempo-synced quarter / eighth-note echoes
- Slap delay on vocals (short MS, no feedback)
- Multiple DDL-1s in a Spider for ping-pong / rhythmic stacks
- Inside Combinators where The Echo is overkill

**Reach for The Echo instead when:** you want stereo, ducking, modulation, drive, filtering, or any of the modern delay tricks built into one device.

> **Recipe — Ping-pong from two DDL-1s:**
> 1. Spider Audio Splitter on the source.
> 2. Two DDL-1s in parallel. Both Pan opposite (hard L / hard R).
> 3. Cross-route their Feedback CV outs/ins manually if you want the classic ping-pong bounce, or just feed each one's wet output back to the other's input via a Spider Audio Merger.

#### RV-7 — Digital Reverb

The other "vintage" Reason device — RV-7 has a particular lo-fi character that's specifically why people still use it over RV7000 MkII.

**Algorithms:** Hall, Large Hall, Hall 2, Large Room, Medium Room, Small Room, Gated, Low Density, Stereo Echoes, Pan Room

**Parameters:**
- **Size**
- **Decay**
- **Damp**
- **Dry/Wet**

**CV In:** Decay

**Use it for:**
- Drum-machine tracks where you want the 1990s reverb sound
- Gated snare verbs (Gated algorithm)
- Sends inside a Combinator where RV7000 MkII is too heavy
- Lo-fi production where the "cheap" character is the point

**Reach for RV7000 MkII instead when:** you need convolution, EQ on the verb, gated/reverse modulation, or anything mastering-grade.

### Distortion / Filter

#### D-11 — Foldback Distortion

Tiny, single-knob-ish distortion. Foldback algorithm — instead of clipping, the wave folds back on itself.

**Parameters:**
- **Amount** — drive level
- **Foldback** — character / harshness of the fold

**CV In:** Amount

**Use it for:**
- Subtle saturation/grit (low Amount)
- All-out crunchy thrashing (high Amount + Foldback)
- A cheap tube-ish vibe on a snare or bass

**Reach for Scream 4 instead when:** you want tube/tape/distortion modeling, EQ-shaped distortion, body/scale controls, or a wider tonal palette.

#### ECF-42 — Envelope Controlled Filter

Multimode filter with a built-in ADSR envelope. *Designed to be used with pattern devices* like Matrix or RPG-8 — every gate triggers the envelope.

**Filter modes:** 24 dB/oct LP, 12 dB/oct LP, 12 dB/oct BP

**Filter parameters:**
- **Freq** — cutoff
- **Res** — resonance
- **Env Amt** — envelope amount over cutoff
- **Velocity** — velocity sensitivity into envelope amount

**Envelope (ADSR):** Attack, Decay, Sustain, Release

**CV/Gate In:** Freq, Decay, Res, Env Gate

**Use it for:**
- Pattern-locked filter sweeps with Matrix gate output -> ECF-42 Env Gate
- Ducking-style envelope effects on a pad
- Adding "talkiness" to a stable drone

**Reach for Thor's filters instead when:** you need notch / comb / formant filters, or you don't need retriggering.

> **Recipe — Pattern-triggered acid filter:**
> 1. Matrix's gate output -> ECF-42 **Env Gate**.
> 2. Mode = 24 dB LP, Freq low, Res high, Env Amt high.
> 3. ADSR: A=0, D=medium, S=0, R=short.
> 4. Each Matrix step now plucks the filter in classic 303-acid style.

---

## Cross-cutting Workflows

### Sidechain key for any compressor

The single most useful Sidechain Tool trick: it's a portable key signal generator.

1. Sidechain Tool in **Trigger** or **Sidechain** mode, fed from your kick (audio or MIDI).
2. **Curve Out** (negative) or **Inverted** (positive) -> the destination compressor's Threshold or Gain CV input.
3. Now MClass Compressor, COMP-01, or even a Thor amp envelope can be ducked by the kick — even if the device has no SC input.

### Stereo width pipeline

Stack devices in this order for a wide-but-mono-safe synth:

1. **UN-16** (mono in, mono out — multiplies voices)
2. **Stereo Tool** (Widening + Low Bypass at 150–200 Hz)
3. **Gain Tool** (Output Mode = Width/Pan, for fine width fine-tune and balance)
4. (Optional) **Stereo Tool** with Mono button on a parallel branch via Gain Tool Router for instant mono check

### Gain staging chain

Where to insert Gain Tool for predictable level management:

1. **First in chain** — trim the source so subsequent compressors/saturators get the level they expect.
2. **Last in chain** — make-up gain after lossy / heavy processing.
3. **Inside Combinators** — bound to a rotary, gives you a real Combinator-level fader.
4. **Mute / Inv / Swap / Mono buttons** — keep one Gain Tool unused as a "utility cell" on every drum bus for fast troubleshooting.

### Mono compatibility check

1. Drop a **Gain Tool** or **Stereo Tool** on the master bus.
2. Toggle **Mono**.
3. If anything you care about (lead, vocal, kick) drops in level or thins out, you have phase cancellation — go upstream and find the culprit.

---

## Common Pitfalls (Master List)

- **Phase issues from over-widening.** Stereo Tool / Gain Tool Width are phase-safe, but the *content* you put into them may not be (a stereo sample with already-correlated content). Always mono-check after big width moves.
- **Bass widening eating the kick.** Set Low Bypass on Stereo Tool to ≥ 150 Hz on anything sub-heavy.
- **Polarity flip on Sidechain Tool CV outs.** Curve Out is negative, Inverted is positive. Use the right one for the destination.
- **Forgetting Sidechain Tool's Listen.** Listen is a *monitoring* solo, not a routing solo. Disable before bouncing.
- **+18 dB on Gain Tool clipping downstream.** The clean +18 dB is real headroom — but it can clip the next device. Watch downstream meters.
- **Half-rack DDL-1 in mono.** DDL-1 is *mono*. If you want stereo delays, parallel two of them or use The Echo.
- **COMP-01 has no makeup knob.** Auto-makeup is on by default — you can't disable it. Don't go searching for the gain knob; if you need explicit makeup, use MClass Compressor or follow with a Gain Tool.
- **Stacking Stereo Tools.** Two in series = comb-filter smear, not extra width. Use one.
- **ECF-42 silence with no gate.** ECF-42's envelope is gate-triggered. With no gate the envelope sits at zero and the cutoff is flat at the Freq knob's value. If it sounds dead, route a gate to Env Gate (or set Env Amt = 0 and treat it as a static filter).
- **Auto Pump on syncopated beats.** Auto Pump is rate-based, not transient-based. Use Trigger or Sidechain mode when the source isn't a metronomic four-on-the-floor.
- **Spider CV polarity.** When splitting Sidechain Tool's CV out across multiple destinations, remember each split keeps the original polarity — so you may need both Curve Out *and* Inverted feeding different destinations through separate Spiders.

---

## Quick Reference Tables

### Sidechain Tool modes at a glance

| Mode | Use when... |
|---|---|
| Auto Pump | You want a synced pump on a non-rhythmic source (pad, bass) without routing the kick |
| Trigger | You want pump events on specific MIDI notes / audio threshold / CV |
| Sidechain | You're keying off a real audio source (the kick at the SC input) |

### Half-rack effects vs full-rack equivalents

| Half-rack | Full-rack equivalent | Switch up when... |
|---|---|---|
| PEQ-2 | MClass Equalizer | You need shelves, HP/LP, or 4+ bands |
| COMP-01 | MClass Compressor / Master Bus Comp | You need SC input, knee, output gain control |
| D-11 | Scream 4 | You want tube/tape modeling and EQ-shaped drive |
| ECF-42 | Thor (filter section) | You need notch/comb/formant or non-retriggered modulation |
| CF-101 | (no direct full-rack chorus; use UN-16 or third-party) | Simple cases stay on CF-101 |
| DDL-1 | The Echo | You want stereo, ducking, drive, modulation in one device |
| RV-7 | RV7000 MkII | You need convolution, EQ-on-verb, gated/reverse, or quality |
| PH-90 | (no full-rack phaser; use Pulveriser or third-party) | Stay on PH-90 unless modeling specific analog hardware |
| UN-16 | (no full-rack unison) | Stay on UN-16 |

### CV polarity cheat sheet (Sidechain Tool)

| Output | Polarity | Patch into... |
|---|---|---|
| Curve Out | Negative | Inverted-positive destinations (rare); patch through a CV inverter; or destinations that expect "duck" as negative |
| Inverted | Positive | Most filter cutoff CV ins, most amp/gain CV ins |
| Trig / Hold / End | Gate (0 or +) | Trigger envelopes, gate other devices, drive Matrix Reset, etc. |

---

## Final notes

These devices are deliberately small — the design intent is "rack glue you reach for without thinking." The secret to using them well is to commit to a *role* per instance: this Gain Tool is the fader, that one is the polarity-checker, that PEQ-2 is the surgical notch, this Sidechain Tool generates a key signal — and not let any one instance sprawl into doing five things at once. The half-rack effects in particular reward letting them be the simple thing they were designed to be; if a half-rack is fighting you, switch to the full-rack equivalent and stop pushing.
