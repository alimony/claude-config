# Reason 13: Acoustic, Vocal & Utility Instruments
Based on Reason 13.4 documentation.

This skill covers five Reason 13 devices that handle vocal pads, general-purpose multi-instrument coverage, tuned percussion, world textures, and routing MIDI to outboard hardware. These are the practical "fast results" devices: low setup overhead, ready-made sounds, and (in MIDI Out's case) a bridge to gear that lives outside Reason.

## Comparison Table

| Device | Type | Best for | Polyphony | Layered/Multi |
|--------|------|----------|-----------|----------------|
| Humana | Multi-sampled vocal ensemble (Soundiron source) | Vocal pads, choir beds, ah/oo backing, soloist colour | Not documented (treat as standard polyphonic synth) | Single instrument selectable from 16 voices; not multitimbral |
| ID8 | Preset sound module / general-purpose ROMpler | Sketching, MIDI file playback, scratch parts before committing to full instruments | Not documented; one sound at a time per instance | Single sound per instance from 9 categories x 4 sounds (36 + drum kits) |
| Klang | Multi-sampled tuned percussion (Soundiron source) | Bell/mallet hooks, music-box motifs, melodic perc layers | Not documented | Single instrument selectable from 10 percussion sources |
| Pangea | Multi-sampled world instruments (Soundiron source) | Ethnic/world flavours, organic textures, hybrid acoustic layers | Not documented | Single instrument selectable from ~11 world sources |
| MIDI Out | MIDI router (no audio engine of its own) | Driving outboard synths, hardware modules, external soft synths | N/A — relies on the receiving instrument | One MIDI port + one channel per instance; multiple instances for multi-channel rigs |

Cross-references in this file:
- Humana, Klang, and Pangea share an almost identical filter/amp/delay/reverb topology and CV layout — once you learn one, you know the others.
- ID8 is the odd one out: minimal panel, two parameter knobs, no dedicated CV mod inputs documented.
- MIDI Out is purely a routing device — pair it with the same external rig you would otherwise patch via a hardware sequencer.

A common pattern across the three Soundiron-sourced instruments (Humana, Klang, Pangea): **CV connections are NOT stored in their patches.** If you build CV routings, wrap the device in a Combinator and save the Combi patch.

---

## Humana Vocal Ensemble

### Type & role
Humana is a multi-sampled vocal synthesiser. It loads dry solo vocals or wet ensemble choir samples (all from Soundiron) and plays them back chromatically with the standard Reason filter/envelope/delay/reverb chain bolted on.

It is **not** a vocal synthesiser in the Vocaloid sense — there is no phoneme engine. Vowels are baked into the samples, so "Ah" and "Oo" are selected by switching instrument, not by morphing.

### Sound categories (16 instruments)

Ensemble (recorded with stereo stage mics in a large hall, wet):
- Mars ah, Mars oo (male, sustained and staccato variants)
- Venus ah, Venus oo (female, sustained and staccato variants)
- Mercury ah (boys' choir)

Solo voices (close mic, mono, dry studio):
- Female Soprano ah
- Female Alto ah
- Male Tenor ah
- Male Bass ah
- Female ah (Francesca Genco)
- Female ah 2 (Linda Strawberry)
- Male ah (Brian Lane)

### Performance controls

Pitch / tuning panel:
- Pitch Bend wheel — range adjustable up to +/-12 semitones (1 octave) in 1-semitone steps.
- Oct (octave): five-octave range (+/-2 octaves around the source).
- Semi: +/-12 semitones (two octaves of fine transposition, one each way).
- Fine: +/-50 cents.
- S. Start (sample start): shifts playback start point up to ~150 ms forward — useful for trimming attack noise or skipping into the middle of a vowel.

Mod Wheel routings (3 assignable, bipolar around 12 o'clock):
- S. Start — modulate sample start position with the wheel.
- F. Freq — modulate filter cutoff.
- Level — modulate master volume.

Velocity:
- Filter Vel (0-100%) — velocity to filter cutoff.
- Amp Vel (0-100%) — velocity to amplitude.

### Filter / amp / FX
The same template as Klang and Pangea:
- Filter types: LP 12 dB/oct, HP 12 dB/oct, BP 6 dB/oct, Comb.
- Cutoff: 20 Hz to 25 kHz; Reso, Env amount, Vel amount, Kbd track (0% = constant, 100% = 1 semitone per key).
- Filter ADSR.
- Amp ADSR + master volume (cap +12 dB).
- Delay: Time, Feedback, Sync, Ping Pong (alternates L/R, doubles delay tempo), Damp, Amount (send-style return).
- Reverb: Time (size), Pre-Delay 0-200 ms, Hi Damp, Lo Damp, Amount (send-style return).

### CV / MIDI
Sequencer Control: CV (pitch), Gate (note on/off + velocity), Pitch Bend CV, Mod Wheel CV.
Modulation CV inputs: Filter Cutoff, Resonance, Master Volume.
Audio: stereo out, auto-routed to first free Mix Channel.

CV routings are **not** saved in Humana patches — wrap in a Combinator if you need them persistent.

### Common workflows

Lush wet pad bed:
1. Load a Mars ah or Venus ah ensemble.
2. Amp Attack ~300-600 ms, Release ~1-2 s.
3. Filter LP, cutoff ~3 kHz, Reso low, Env on a slow Attack to "open" each note.
4. Reverb Time long, Pre-Delay 30-60 ms, Hi Damp moderate, Amount pushed.
5. Mod wheel mapped to Level for swelling phrasing.

Solo lead emulation:
1. Pick a solo (e.g. Female ah Genco).
2. Set Amp Vel to ~50-70% so dynamics track playing.
3. Map Mod Wheel to F. Freq for vowel-shape brightness.
4. Slight Fine detune (+/-3-7 cents) layered with a second Humana for ensemble illusion.

Phrase tightening:
- Use S. Start to skip past breathy attacks for snappier, punchier vocal stabs.

### Pitfalls
- Loading larger ensemble instruments takes a moment as the sample is paged into RAM — switch sounds during prep, not during playback.
- Mod wheel modulation is hard-clamped: it cannot push cutoff outside 20 Hz - 25 kHz, sample start outside 0-150 ms, or master volume above +12 dB.
- "Phrasing" is sample-driven — you can't reshape vowels mid-note. Plan note lengths around the underlying sustains; very short notes can sound clipped, very long notes loop or sit static.
- Sustain is a level, not a time, parameter. If you want choir-style perpetual sustain, set Sustain to 100% and Release long.
- Transposing voices far outside their natural range produces obvious artefacts — sometimes desirable as a creative effect, often unflattering for "real choir" parts.

### Quick recipe — "ambient choir bed"
1. Instrument: Mars ah.
2. Amp ADSR: A 600 ms / D 0 / S 100 / R 1500 ms.
3. Filter LP 12 dB, Cutoff 4 kHz, Reso 0, Kbd 50%.
4. Reverb on, Time long, Pre-Delay 50 ms, Hi Damp moderate, Amount strong.
5. Mod Wheel -> Level (for wave-in dynamics).
6. Wrap in a Combinator if you intend to feed it CV from a Matrix or LFO.

---

## ID8 Instrument Device

### Type & role
ID8 is Reason's small, fast, "preset sound module." It is the device that gets created automatically when you import a Standard MIDI File, and it's the right tool whenever you want a usable sound *now* — full Reason-grade synths (Europa, Reason etc.) come later when the song has shape.

Treat ID8 like a General-MIDI-style ROMpler: 9 categories, 4 sounds each, plus drum kits. No deep editing, no patch browser, two parameter knobs.

### Sound categories
1. **Piano** — Grand piano, upright piano, dance piano, vibes.
2. **Electric Piano** — Two classic EPs, FM digital piano, Clav.
3. **Organ** — Two tonewheel organs, transistor organ, pump organ.
4. **Guitar** — Acoustic steel string, clean electric, jazz semi-acoustic, dulcimer.
5. **Bass** — Fingered bass, picked bass, acoustic upright, synth bass.
6. **Strings** — Orchestral strings, arco strings, small string section, choir.
7. **Brass-Wind** — Fat Brass, Brass Section, French Horns, Flute.
8. **Synth** — Two mono leads, two poly pads (one fast attack, one slow attack).
9. **Drums** — Four drum kit combinations, each containing 53-65 instruments.

### Performance controls
- **Two assignable Parameter knobs** per sound — what they do depends on the loaded sound (it is intentionally not deeply editable).
- Pitch Bend: fixed at +/-2 semitones across all sounds.
- Mod Wheel: vibrato on most sounds; on the Drums category it controls the lowpass cutoff for the electronic kits.
- Sustain pedal, expression (volume), aftertouch and breath control are all supported.

Sounds are multi-sampled with multiple velocity layers. Some categories swap articulation at the top of the velocity range:
- Bass sounds add glissando at highest velocity.
- Arco strings flip to pizzicato at top velocity.

So velocity does double duty: dynamics + articulation switching. Plan layering carefully.

### CPU / quality trade-off
The documentation does not call out an explicit "low/high quality" toggle for ID8. Practical guidance:
- ID8 is the cheapest "sounds OK" device in Reason; lean on it for sketches.
- When polyphony or layered velocity articulation matters, swap to a dedicated device (NN-XT, Reason synths) — ID8 is intentionally stripped-down and not a final-mix instrument for most genres.
- For drum work especially, treat ID8 as a placeholder and graduate to Kong / Drum Sequencer / NN-XT for finals.

### Common workflows

Sketch from a MIDI file:
1. Drag a Standard MIDI File into Reason — each track gets its own ID8.
2. Re-assign each ID8 to the closest matching category/sound.
3. Tweak the two Parameter knobs and Mod Wheel for vibrato/movement.
4. Use this as your scratch arrangement; replace track-by-track with full devices once the structure is locked.

Fast scratch keys / bass while songwriting:
1. Insert ID8.
2. Choose Piano > Grand or Electric Piano > Classic EP.
3. Bind Mod Wheel to vibrato for expressivity.
4. Record the part; only when committed swap in a fuller device.

Editing & saving:
- ID8 parameter edits **save with the song automatically** — you don't get an explicit patch browser.
- To preserve a particular ID8 setup as a reusable patch, drop it inside a Combinator and save the Combi patch.

### Pitfalls
- No traditional patch storage — the only "patch" is via Combinator wrapping.
- Velocity-switched articulations bite when you don't expect them. If a bass line suddenly slides at fortissimo, that's the high-velocity glissando layer firing; pull velocities down or quantise dynamics.
- Pitch Bend range is **fixed** at +/-2 semitones — not adjustable from the panel. Heavy bend phrasing is a job for another instrument.
- The Drums Mod Wheel mapping (electronic kit LPF) is non-obvious; if the kit suddenly goes muffled, check the wheel.
- ID8 is shallow on purpose. Don't fight it — if you need real sound design, use the right device.

### Quick recipe — "10-minute sketch arrangement"
1. Drums: ID8 > Drums kit 1 (acoustic). Quantise.
2. Bass: ID8 > Bass > Fingered. Cap velocities <120 to avoid glissando flips.
3. Keys: ID8 > Electric Piano > Classic EP1.
4. Pad: ID8 > Synth > Slow-attack pad.
5. Lead: ID8 > Synth > Mono lead. Mod Wheel for vibrato.
6. Commit to the arrangement; replace each ID8 with a full instrument at mix time.

---

## Klang Tuned Percussion

### Type & role
Klang is a multi-sampled tuned-percussion instrument. Same engine philosophy as Humana and Pangea (Soundiron sources, Reason's standard filter/amp/delay/reverb), but with mallet/bell/struck-pitch sources.

Use Klang whenever you want a melodic line played on bells, kalimba, music box, glockenspiel, or experimental tuned drums — without loading a full sample library.

### Sound categories (10 instruments)
1. **Alto Glockenspiel** — hard mallets, large hall, slight ambience.
2. **Bamblong** — Indonesian bamboo log drum, rubber mallets, dry studio.
3. **Circle Bells Mallet** (Blossom Bells) — rubber mallets, dry studio.
4. **Cylindrum** — experimental tubulum (plastic piping), rubber paddles.
5. **Imbibaphones** — wine glasses, rubber mallets, dry studio.
6. **Kalimba** — African thumb piano, dry studio.
7. **Music Box** — mechanical music box, dry studio.
8. **Noah Bells** — Indian bells, fingertip strikes, slightly wet hall.
9. **Steel Tones** — hank/propane drum, felt mallets, room recording.
10. **Whale Drum** — African wooden slit drum, rubber mallets, dry studio.

### Performance controls

Pitch / tuning panel (identical layout to Humana):
- Pitch Bend wheel range +/-12 semitones in 1-semitone steps.
- Oct +/-2, Semi +/-12, Fine +/-50 cents.
- S. Start (sample start) — note that the audible result depends heavily on the source: shifting past the attack of a music box can hide its "click," or past a kalimba pluck to skip the thumb-noise.

Mod Wheel routings (bipolar around 12 o'clock):
- S. Start, F. Freq, Level — same three destinations as Humana.

Velocity:
- Filter Vel and Amp Vel each 0-100%.

### Filter / amp / FX
Identical to Humana and Pangea — Filter (LP 12, HP 12, BP 6, Comb), Filter ADSR with Env/Vel/Kbd track, Amp ADSR, master volume +12 dB cap, send-style Delay (Time/Feedback/Sync/Ping Pong/Damp/Amount), Reverb (Time/Pre-Delay 0-200 ms/Hi Damp/Lo Damp/Amount).

### CV / MIDI
Sequencer Control: CV pitch, Gate (note + velocity), Pitch Bend CV, Mod Wheel CV.
Modulation CV: Filter Cutoff, Resonance, Master Volume.
Audio: stereo out auto-routed to first free Mix Channel.

CV connections are **not stored** in Klang patches — Combinator them.

### Envelope shaping for percussion
Documentation calls out two useful presets:
- **Piano-like decay**: Attack 0, Decay medium, Sustain 0, Release short. Note dies away naturally.
- **Organ-like sustain**: Attack 0, Decay 0, Sustain 100%, Release short — held notes stay loud (good for sustaining the resonant tail of a bell beyond its natural decay).

Sustain is a *level*, not a time, parameter. This catches people out.

### Common workflows

Tuned-percussion lead line:
1. Pick Alto Glockenspiel or Music Box.
2. Amp ADSR: A 0, D 600 ms, S 0, R 200 ms (let the strike ring out naturally).
3. Filter off (or LP very high) — keep transient detail.
4. Reverb medium-long Time, Pre-Delay 30 ms, Hi Damp moderate, Amount pushed.
5. Add Delay synced to 1/8 dotted, Ping Pong on, Feedback ~30%, Damp medium for a "Lonely Trousers" cinematic.

Layered melodic perc bed:
- Two Klangs in a Combinator.
- Klang A: Kalimba dry, low octave.
- Klang B: Imbibaphones, an octave or fifth above.
- Pan slight L/R; offset Fine tuning by +/-5 cents for shimmer.

Sound-design "broken music box":
- Music Box source.
- Pitch wheel range 12 semitones; record large bend gestures.
- S. Start fully cranked to skip into different parts of the strike.
- Comb filter, mod wheel to F. Freq.

### Pitfalls
- Sustain-as-level confusion (see above) — most percussion sounds want Sustain 0.
- Sample-start modulation is hard-bounded by the source's S. Start range (0-150 ms).
- Send-style FX leak: turning Amount up *after* a hit is played can reveal previously-buffered tails — useful for dub-style throws, surprising if you didn't intend it.
- Long transposes outside natural range introduce sample stretching artefacts. With percussion this is much more obvious than with vocals — tune carefully.
- CV not stored in patches — Combinator if needed.
- Loading a fresh percussion instrument takes a brief moment for sample paging.

### Quick recipe — "music box motif"
1. Instrument: Music Box.
2. Amp ADSR: A 0 / D 700 ms / S 0 / R 300 ms.
3. Filter off.
4. Delay on, Sync on, Time 1/8 dotted, Feedback 35%, Ping Pong on, Damp ~50%, Amount low.
5. Reverb on, Time medium-long, Pre-Delay 25 ms, Hi Damp medium, Amount moderate.
6. Mod Wheel -> F. Freq for tonal variation between phrases.

---

## Pangea World Instruments

### Type & role
Pangea is a multi-sampled "world instruments" device — rare strings, organs, flutes, struck and plucked oddities from around the globe, all sourced from Soundiron and recorded faithfully. Same engine as Humana and Klang.

Use Pangea when you want an organic, unfamiliar acoustic colour — to layer behind a synth pad, to lead a folk-flavoured melody, or to add character to an otherwise sterile arrangement.

### Sound categories (~11 instruments)

Strings:
- **Acoustic Saz** — Turkish electro-acoustic 5-string.
- **Bizarre Sitar** — Indian 8-string, character-rich.
- **Harp Guitar** — custom Brad Hoyt design.
- **Zitherette** — 8-string fretless zither.

Keyboard / percussive:
- **Kinderklavier** — German toy steel-tine piano.
- **Struck Grand Piano** — strings struck with a metal hammer (so not a regular piano voicing — more dulcimer-like).
- **Lakeside Pipe Organ** — church pipe organ.
- **Traveler Organ** — antique mechanically-operated organ.

Wind / reed:
- **Little Wooden Flutes** — Native American walnut, 6-hole.
- **Little Pump Reeds** — Indian pumped reed (harmonium-relative).

Percussion:
- **Angklung** — Indonesian 18-piece tuned bamboo rattle.

### Performance controls
Identical layout to Humana and Klang:
- Pitch Bend wheel +/-12 semitones (1-semitone steps).
- Oct +/-2, Semi +/-12, Fine +/-50 cents (1-cent steps).
- S. Start adjustable per source.
- Mod Wheel destinations (bipolar): S. Start, F. Freq, Level.
- Filter Vel and Amp Vel 0-100%.

### Filter / amp / FX
Same template — LP 12 / HP 12 / BP 6 / Comb, Filter ADSR with Env/Vel/Kbd track, Amp ADSR, master volume capped +12 dB, send-style Delay (Time/Feedback/Sync/Ping Pong/Damp/Amount), Reverb (Time/Pre-Delay 0-200 ms/Hi Damp/Lo Damp/Amount).

### CV / MIDI
Sequencer Control: CV pitch, Gate, Pitch Bend CV, Mod Wheel CV.
Modulation CV: Filter Cutoff, Resonance, Master Volume.
Audio: stereo out, auto-routed to first free Mix Channel.

CV connections are **not stored** in Pangea patches — Combinator if needed.

### Common workflows

Folk-style lead line:
1. Acoustic Saz or Bizarre Sitar.
2. Amp ADSR matched to the source (saz: short A/short R; sitar: A 0, long R for sympathetic-string ring).
3. Filter LP, Cutoff high, Reso low — preserve top end.
4. Reverb Time medium, Pre-Delay 20-40 ms, Hi Damp moderate, Amount low-medium.
5. Mod Wheel -> F. Freq for expressive timbral movement.

World percussion bed:
- Angklung as the main rhythmic timbre.
- Octave-double in a second Pangea instance for a wider stack.
- Light Delay synced 1/16, low feedback, Ping Pong on.

Hybrid acoustic-electronic pad:
- Layer Lakeside Pipe Organ in Combinator with a sustained synth pad (e.g. ID8 slow pad or Europa).
- Use organ for body, synth for shimmer; balance via Combi level controls.

Articulation note:
Pangea, like Humana and Klang, doesn't have a real-time articulation switcher (legato/staccato/etc.). Articulation comes from velocity layers and the source recording. Use velocity ranges deliberately to vary tone.

### Pitfalls
- Same Mod Wheel hard limits as the rest: cutoff 20 Hz - 25 kHz, sample start 0-150 ms, master volume +12 dB.
- Aggressive transposition produces obvious sample-stretch artefacts, especially on bowed/plucked sources. Stay within ~+/-7 semitones of the natural range for naturalism; go wild deliberately for sound design.
- CV routings are **not** in the patch — Combinator them.
- Loading time depends on source size. The bigger string instruments may take a moment to page into RAM.
- Send-style Delay/Reverb tails can leak after the note ends if you raise Amount mid-playback — useful for dubby moves, surprising if accidental.
- Some instruments (e.g. Struck Grand Piano) sound nothing like their name suggests — listen first, don't assume.

### Quick recipe — "ethnic atmospheric layer"
1. Instrument: Bizarre Sitar.
2. Amp ADSR: A 0 / D 1200 ms / S 60 / R 1500 ms (let sympathetic strings ring).
3. Filter LP, Cutoff ~6 kHz, Reso 0, Kbd 30%.
4. Delay on, Sync on, Time 1/4 dotted, Feedback 40%, Ping Pong on, Damp medium, Amount low.
5. Reverb long Time, Pre-Delay 30 ms, Hi Damp medium, Lo Damp light, Amount strong.
6. Mod Wheel -> F. Freq.

---

## MIDI Out Device

### Type & role
The MIDI Out Device is **not** an instrument — it produces no sound. It's a routing module that takes MIDI from Reason's sequencer and sends it to an external MIDI destination (a hardware synth, a hardware drum machine, a soft synth running outside Reason, etc.). The audio comes back into Reason via an audio track on your interface.

Use it as the bridge between Reason and any gear that lives outside the rack.

### Hardware setup checklist
- A MIDI interface installed on the computer.
- External instrument MIDI In <- computer MIDI interface MIDI Out.
- External instrument MIDI Out -> computer MIDI In (only required if you want to capture controller data sent by the external device).
- External instrument audio outs -> audio interface inputs.
- An Audio Track in Reason with the right input and Monitor enabled.

Critical: set the external instrument to **MIDI Local Off** if it's also acting as your master keyboard. Otherwise keys you press will play locally *and* be re-sent through Reason, doubling notes.

### Front-panel controls
- **MIDI Port** selector — choose the MIDI output port (whatever your interface presents).
- **MIDI Channel** — up/down arrows to set the channel the external instrument is listening on.
- **Pitch bend / Mod wheel** — these send standard MIDI messages; their audible effect depends entirely on how the external instrument is programmed.
- **Program** section — On button, up/down arrows to pick program number. Sends program change on song load and is automatable for sound-switching mid-song.
- **CC display / Offset knob** — drag the display to choose a CC number; the Offset knob sends/automates that CC.
- **CV IN section (8 inputs)** — On button enables CV-to-MIDI-CC conversion (more below).

### Bank Select
There is no dedicated Bank Select control. To bank-switch:
1. Automate MIDI CC #0 (Bank Select MSB) and/or CC #32 (Bank Select LSB).
2. Immediately follow with a Program Change.

Important: **Reason only sends MIDI CC data when values actually change.** If you want to re-send the same CC value, you have to nudge it to a different value first.

### CC automation — three ways to record it
1. **From the MIDI Out Device itself** — drag the CC display to pick a CC number, hit record, ride the Offset knob.
2. **Remote Control mapping** — right-click the Offset knob, "Edit Remote Override Mapping," wiggle a hardware controller's knob/slider; that physical control now drives that CC for that device.
3. **From the external instrument's own panel** — go to Preferences > MIDI, add the external instrument as a "MIDI Control Keyboard," enable MIDI Local Off on the instrument, disable MIDI thru, then physical knob movement on the instrument is captured into Reason as automation.

### CV-to-MIDI CC conversion
The 8 CV inputs let you drive MIDI CCs from anywhere in the rack (LFO, Matrix, envelopes, modulation):
1. Enable CV IN section.
2. Pick a CV IN pair to configure.
3. Drag to choose the target MIDI CC# (0-119).
4. **Scale** knob — adjusts modulation range (effectively 0-0 up to 0-127).
5. **Offset** knob — fixed offset on top of the modulation.

Bipolar CV catch:
- Negative CV values are **truncated to zero**.
- To preserve the full bipolar swing, set Scale to half and Offset to half — this maps -127..+127 CV into 0..127 CC linearly.

### Connections (rear)
Sequencer Control inputs: CV (pitch), Gate (note + velocity), Pitch Bend CV, Mod Wheel CV.
8 CV inputs for the CV-to-CC conversion section.
No audio outputs — audio comes from the external instrument into a separate audio track.

### Common workflows

Driving a hardware synth on channel 1:
1. Insert MIDI Out Device.
2. Set MIDI Port to your interface, Channel to 1.
3. Plug a MIDI clip in front of the device track.
4. Create an Audio Track for the synth's audio inputs; enable Monitor.
5. Record-arm the MIDI Out track and play; the synth speaks back through the audio track.

Multiple hardware modules:
- Use one MIDI Out Device per module/channel.
- Keep audio tracks per module so you can mix independently.
- If a single device has multiple MIDI channels (multitimbral), use multiple MIDI Out Devices on the same port, different channels.

Latency-compensating a hardware track via ReGroove:
1. Assign a ReGroove Mixer channel to the MIDI Out Device track.
2. Enable the metronome / Click in the sequencer.
3. Turn the Slide knob counter-clockwise (negative slide) until the external instrument's audio aligns with the click.
4. Be aware: Slide is **tempo-dependent** — it shifts in ticks, not absolute milliseconds. Re-tune Slide if the song tempo changes.
5. Make sure your audio recording arm-in begins **before** the first note clip starts, otherwise the negative slide pulls notes into a region that isn't being recorded.

Recording the external synth's audio:
1. Mix carefully — leave roughly 12 dB headroom on the audio input meter to avoid clipping.
2. Monitor the external synth externally (e.g. through your interface's direct monitor) to avoid latency-induced phasing on playback.
3. After recording the audio pass, **mute the MIDI Out track during playback** to prevent re-triggering the synth on top of the recorded audio.

### Pitfalls

Hanging notes:
- If a note gets stuck on the external instrument, hit `[!]` on the keyboard or use **Options > MIDI: Send All Notes OFF**.

MIDI feedback loops:
- Do **not** let the controlled instrument echo MIDI back into Reason via local thru / soft thru. You'll get notes ping-ponging.

Latency:
- Reason cannot auto-compensate MIDI latency through external interfaces and instruments. You compensate manually via:
  - ReGroove Slide (preferred, real-time and reversible).
  - Nudging clips earlier on the timeline.
- Latency varies by interface, MIDI port, and the receiving instrument's own engine latency. Measure with a click track.

Clock / timing:
- The documentation does not detail explicit MIDI Clock send settings on the device itself. For tempo-locking external gear, consult Preferences > MIDI / Sync. Treat MIDI Out Device as event delivery (notes/CC/PC), not as a master clock source by itself.

CC value caching:
- Reason only sends CC when values change. To force a repeat send, briefly modulate to a different value first.

Truncated bipolar CV:
- Negative CV becomes zero unless you Scale/Offset. Forgetting this gives you "half a modulation."

Program Change timing:
- External instruments may take a moment to load the new sound. Place automation points slightly **before** the desired sound change to allow the instrument to finish loading by the time notes arrive.

### Quick recipe — "external synth as a Reason instrument"
1. Wire the synth: MIDI in/out, audio out into the interface.
2. Set the synth to MIDI Local Off (if it's also your controller).
3. Insert MIDI Out Device. Pick MIDI Port; set Channel to match the synth.
4. Optional: pick a Program number; turn Program "On."
5. Create an Audio Track for the synth's audio; arm Monitor.
6. Play / record MIDI on the MIDI Out track.
7. Add a ReGroove Mixer slide on the MIDI Out track, dial in by ear against the click, lock it in.
8. Audio-print the part: record the audio track while playing the MIDI; afterwards mute the MIDI Out track for mixdown.

---

## Cross-device tips

- **Combinator everything you care about.** The Soundiron-based instruments (Humana, Klang, Pangea) all drop their CV connections when patches change. ID8 has no real patch storage. MIDI Out's Remote mappings live with the song, but a Combinator wrapper makes it portable.
- **Same engine, same pitfalls.** Humana, Klang, and Pangea share filter, amp, delay, reverb, mod wheel layout, and CV inputs. A patch idea in one usually translates directly to the other two.
- **Velocity does articulation work.** ID8 has explicit velocity-switched articulations (bass glissando, arco-to-pizzicato). The sampled instruments (Humana, Klang, Pangea) have multi-velocity layers that change tone, not articulation. Plan velocity ranges deliberately.
- **Send-style FX leak.** All three sampled instruments use send-style Delay and Reverb. Raising Amount after notes play exposes buffered tails — useful, sometimes surprising.
- **External vs. internal latency.** ID8/Humana/Klang/Pangea play in-rack with no extra latency beyond Reason's audio engine. MIDI Out adds external interface + instrument latency, which only manual ReGroove Slide / clip nudging can correct.
- **Sketch fast, finish properly.** ID8 is for sketches. Once a song is committed, replace ID8 instruments with full devices (Reason synths, NN-XT, Kong) and move scratch vocals, perc, and world parts to the proper specialised devices (Humana, Klang, Pangea).
