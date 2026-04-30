# Reason Skills

Based on Reason 13.4 documentation.
Generated from https://docs.reasonstudios.com/reason13/ on 2026-04-30.

Reason is the music production environment from Reason Studios — a virtual rack of instruments, effects, and routing utilities, paired with a sequencer and SSL-style mixer. These skills synthesize the full Reason 13.4 Operation Manual into practical "how to do it properly" guidance.

## Available Skills

| Skill | Topics Covered | Lines |
|-------|---------------|-------|
| [introduction-basics](./introduction-basics.md) | Authorization, Demo Mode, three-area paradigm (Mixer/Rack/Sequencer), conventions, modifier keys, on-screen piano | 249 |
| [audio-fundamentals](./audio-fundamentals.md) | Sample rate, bit depth, drivers (ASIO/Core Audio), buffer/latency tuning, Hardware Interface, gain staging | 200 |
| [sequencer](./sequencer.md) | Tracks/lanes/clips, transport, recording, comping, audio editing, note + automation editing, Blocks | 712 |
| [rack-and-devices](./rack-and-devices.md) | Rack model, creating/reordering devices, Players, Rack Extensions, VST plugins, native vs RE vs VST | 592 |
| [sounds-browser-files](./sounds-browser-files.md) | Browser, patches, ReFills, song files, self-contained vs referenced, audio import/export, sampling | 558 |
| [routing-mixing](./routing-mixing.md) | Cables (audio + CV), Main Mixer, sends/groups, delay compensation, Hardware Interface | 548 |
| [performance-midi](./performance-midi.md) | ReGroove, Remote (controller mapping), MIDI Clock + Ableton Link sync, performance optimization | 608 |
| [synthesizers](./synthesizers.md) | Subtractor, Thor, Malström, Europa, Polytone, Monotone — architecture, modulation, patch recipes | 643 |
| [samplers-loop-players](./samplers-loop-players.md) | Dr.Octo Rex, Grain, Mimic, NN-XT, NN-19, Radical Piano — sample editing, key zones, granular, REX | 639 |
| [drum-instruments](./drum-instruments.md) | Kong (16 pads, multi-engine), Redrum (10-channel pattern), Rytmik (modern drum machine) | 472 |
| [acoustic-vocal-instruments](./acoustic-vocal-instruments.md) | Humana, ID8, Klang, Pangea, MIDI Out (external hardware) | 485 |
| [effects-dynamics-eq](./effects-dynamics-eq.md) | Channel Dynamics, Channel EQ, Master Bus Compressor, M-Class chain (EQ/Imager/Comp/Maximizer) | 694 |
| [effects-modulation-filter](./effects-modulation-filter.md) | Alligator, Pulveriser, Sweeper, Synchronous — gates, filters, rhythmic modulation | 624 |
| [effects-delay-reverb](./effects-delay-reverb.md) | Ripley, RV7000 Mk II (10 algorithms), The Echo, Quartet — delays, reverbs, chorus | 499 |
| [effects-distortion-voice](./effects-distortion-voice.md) | Audiomatic, BV512 vocoder, Neptune (pitch/voice synth), Scream 4, Softube Amps | 766 |
| [effects-utility](./effects-utility.md) | Sidechain Tool, Stereo Tool, Gain Tool, all 9 half-rack effects (PEQ-2, COMP-01, D-11, etc.) | 553 |
| [utility-routing-devices](./utility-routing-devices.md) | Combinator, Line Mixer 6:2, Matrix, Mixer 14:2, Pulsar Dual LFO, RPG-8 arpeggiator | 556 |
| [reference-shortcuts](./reference-shortcuts.md) | Menu reference, Preferences dialogs, complete keyboard shortcut cheat sheet | 646 |

## How to Use

Reference individual skills in your project's CLAUDE.md:

    @~/.claude/skills/reason/{topic}.md

Or reference this index to see what's available:

    @~/.claude/skills/reason/index.md

## Where to Start

- **New to Reason?** Read `introduction-basics.md` and `rack-and-devices.md` first — they teach the mental model (rack + sequencer + mixer, signal flow top-to-bottom, cables = signal path).
- **Recording / arranging?** `sequencer.md` covers the whole sequencer; `audio-fundamentals.md` for setting up your interface.
- **Sound design?** Pick from `synthesizers.md`, `samplers-loop-players.md`, or `drum-instruments.md` depending on the source.
- **Mixing?** `routing-mixing.md` for the Main Mixer and cabling, then dig into the four `effects-*.md` files for specific processors.
- **Macros / control / arpeggios?** `utility-routing-devices.md` for Combinator, Matrix, RPG-8, Pulsar.
- **Quick lookup of a shortcut?** `reference-shortcuts.md`.

## Coverage

- Total documentation pages read: 76
- Skill files created: 18
- Total lines: 10,044
- Pages failed: 0

## Source

All skill files were synthesized from the official Reason 13.4 Operation Manual at:
https://docs.reasonstudios.com/reason13/
