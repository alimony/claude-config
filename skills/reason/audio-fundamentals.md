# Reason 13: Audio Fundamentals
Based on Reason 13.4 documentation.

This skill teaches you how to configure and work with audio in Reason 13: drivers, sample rate, buffer size, the Hardware Interface device, gain staging, and clip handling.

## Core Concepts

### Sample Rate
- **Supported:** All standard rates from 44.1 kHz to 192 kHz.
- **Common choices:**
  - 44.1 kHz - audio CD standard, lowest CPU cost.
  - 48 kHz - video/broadcast standard.
  - 88.2 / 96 kHz - high-resolution recording, typical "pro" choice.
  - 176.4 / 192 kHz - mastering / archival; expensive in CPU.
- **Below 44.1 kHz:** not recommended (audio quality degrades).
- **Higher rate = higher CPU and hardware load,** and increases latency despite buffer settings.
- **Mixed rates in one song:** Reason auto-converts imported audio that doesn't match the hardware sample rate. A real-time conversion plays immediately, then a higher-quality version is calculated in the background (look for the CALC indicator).

### Bit Depth (Resolution)
- Reason supports **16-bit, 20-bit, and 24-bit** for input and output audio.
- Recording resolution is determined by your **audio interface** - a 24-bit card records 24-bit.
- **Internal processing:** 32-bit floating-point for all DSP, with **64-bit summing** in the Main Mixer Master Section. Internal headroom is effectively unlimited.

### Audio Drivers
- **Windows: ASIO is required** for proper performance.
  - MME ~ 160 ms latency. DirectX ~ 40 ms. Both unusable for tracking.
- **macOS: Core Audio** (built into the OS).
- Always **use the latest driver** for your hardware interface.
- Drivers are selected in **Preferences > Audio**.

### Buffer Size and Latency
- Smaller buffer = lower latency but higher DSP load and risk of crackles/dropouts.
- Larger buffer = more headroom and stability but more latency.
- A good interface with ASIO/Core Audio can hit **2-3 ms** round trip.

#### Buffer Size vs. Latency (rule-of-thumb at 44.1 kHz)
| Buffer (samples) | Approx. latency one-way | Use case |
|------------------|-------------------------|----------|
| 32 - 64          | 0.7 - 1.5 ms            | Tracking soft synths / live monitoring (needs strong CPU + interface) |
| 128              | ~2.9 ms                 | Tracking, light mixing |
| 256              | ~5.8 ms                 | Tracking with moderate plugin load - good default |
| 512              | ~11.6 ms                | Mixing with heavy plugins |
| 1024             | ~23 ms                  | Mixing / mastering, max plugin headroom |
| 2048             | ~46 ms                  | Bouncing, stem rendering |

#### Common Sample Rates
| Sample Rate | Use case | Notes |
|-------------|----------|-------|
| 44.1 kHz    | CD, music release | Lowest CPU |
| 48 kHz      | Video/broadcast | Match project deliverable |
| 88.2 kHz    | High-res music, integer multiple of 44.1 | Easier to convert back to 44.1 |
| 96 kHz      | High-res music/film | Common "pro" rate |
| 176.4/192 kHz | Mastering, archival | Heavy on CPU; rarely needed |

### Audio Interfaces
- Conversion is handled by an internal sound card or external USB/Thunderbolt interface.
- Sound quality depends on **frequency range, response, bit depth, signal-to-noise ratio, and distortion**.
- Reason's docs explicitly state: *"if you are serious about sound, choose your audio hardware carefully."*

## Audio Preferences (Edit/Reason menu > Preferences > Audio)

| Setting | What it does |
|---------|--------------|
| **Audio Card Driver** | Selects ASIO (Windows) or Core Audio (macOS) device. |
| **Sample Rate** | Dropdown of rates supported by the selected hardware. |
| **Buffer Size** | Slider/spin control - drives latency vs. DSP trade-off. |
| **Max Audio Threads** | Cap on threads used for multi-core rendering. Default = number of physical CPU cores (performance cores on Apple Silicon M1-M4). Lower it to leave headroom for other apps or VSTs. |
| **Render audio using audio card buffer size setting** | When ON, internal processing uses the full buffer size - more efficient for DSP-heavy VSTs/mastering. When OFF, internal batches are fixed at 64 samples - keeps short latency for feedback routings and CV connections. **Old songs using feedback/CV may sound different with this ON.** |
| **Master Tune** | Global tuning for Reason's sound sources (default A=440 Hz). Affects Tuner, Redrum, Dr. Octo Rex, etc. **Does NOT affect audio tracks or VST plugins.** |

## The Hardware Interface Device

Always pinned at the **top of the rack**. This is the bridge between Reason's internal mixer/devices and your physical I/O.

- **64 input + 64 output sockets**, each with meter and indicator.
- 16 I/O pairs visible by default; click **More Audio** to access the other 48.
- Press **Tab** to flip the rack and see the rear (manual patching).
- Click **Big Meter** for a detailed level meter with channel select and clip reset.

### Indicator Colors
| Color  | Meaning |
|--------|---------|
| Green  | Active and connected |
| Yellow | Available but unconnected |
| Red    | Connected but unavailable (your hardware doesn't support that I/O) |

### Default Routing
- A new Song auto-connects the **Main Mixer Master Section to outputs 1-2** of the Hardware Interface. Leave it that way unless you have a reason to change it.

## How-To Patterns

### Setting Up the Audio Interface
1. Plug in your interface and install the **latest driver**.
2. **Edit (Win) or Reason (macOS) > Preferences > Audio**.
3. Pick the **Audio Card Driver** (ASIO device on Windows, Core Audio device on macOS).
4. Set **Sample Rate** to match your project deliverable (44.1/48 kHz typical).
5. Set **Buffer Size** based on the activity (see next section).
6. Confirm green indicators on the Hardware Interface for the I/O you expect.

### Choosing Buffer Size
- **Tracking (recording vocals/instruments through soft synths/effects):** 64-256 samples.
- **General editing/arrangement:** 256-512 samples.
- **Mixing with heavy plugin chains:** 512-1024 samples.
- **Mastering / final bounce:** 1024-2048 samples.
- If you hear crackles or see DSP overload, **double the buffer**.

### Choosing Sample Rate
- Match the **delivery target** (music = 44.1 kHz, video = 48 kHz).
- Only go to 88.2/96 kHz if your interface and CPU can handle it AND there's a sonic reason.
- Don't mix rates within a song unless necessary - let Reason convert imports automatically (the CALC indicator shows it's working in the background).

### Recording Audio (Inputs)
- **You do NOT need to patch cables to the Hardware Interface's Audio In jacks** - audio inputs are routed automatically.
- In the **sequencer Track List**, pick the input from the **Audio Input dropdown** on the audio track.
- Set record level on the **hardware/preamp**, not in Reason. Reason cannot adjust input gain.

### Routing Outputs
- For multi-output workflows (cue mixes, hardware inserts, monitor speakers + headphones): patch from a device's rear outputs to specific Hardware Interface outputs.
- Example: route the Main Mixer **Control Room Outputs** to a different output pair to feed a separate monitor path.
- Use the **Big Meter** or per-socket meters on the Hardware Interface to see which physical output is doing what.

### Monitoring
- Reason routes monitoring **through software** by default - latency = round-trip through the buffer.
- For ultra-low-latency tracking (vocals, guitar amp sims at low buffers): use your interface's **direct/zero-latency hardware monitoring** if Reason's plugin monitoring lags. (Reason's docs don't go deep on this; configure it on the interface itself.)

## Best Practices

### Gain Staging
- **Internal levels are floating-point with virtually unlimited headroom.** Channel meters going into the red on individual devices is **NOT actual clipping** - it's only an issue at the Hardware Interface's output (where conversion to the audio interface's bit depth happens).
- **Watch the Audio In and Audio Out meters on the Transport Panel** and the Master Section meters - those reflect real, audible clipping.
- Keep some headroom on the Master Section (peaks below 0 dBFS) so external D/A conversion stays clean.
- For internal sampling/resampling from rack devices, set the **Output Level on the source device**.

### Clipping - Where to Fix It
| Clipping at... | Fix at... |
|----------------|-----------|
| **Audio In** (recording from outside)   | Lower input gain on the **hardware/preamp**. Reason cannot adjust input level. |
| **Internal sample/source device**        | Lower the **Output Level on the source device**. |
| **Audio Out** (playback)                 | Lower the **master level** on the Mixer/device feeding the Hardware Interface. Or insert an **MClass Maximizer** as the last effect on the Master Section. |

### Performance
- Use a **quad-core Intel i7 / equivalent AMD / Apple Silicon** at minimum; more cores = more headroom.
- **4 GB RAM minimum**; more is strongly recommended.
- Close background apps that fight for CPU/disk during tracking.
- Cap **Max Audio Threads** if other apps need CPU.
- Enable **Render audio using audio card buffer size setting** for DSP-heavy plugin chains during mixing/mastering.

## Common Pitfalls

### "I have crackles/dropouts during playback"
- Buffer is too small for the project's plugin load. **Increase buffer** (e.g., 256 -> 512 or 1024).
- Older driver. **Update to the latest driver.**
- Background tasks hogging CPU/disk. Quit them.
- Sample rate too high for the system. Drop to 48 or 44.1 kHz.

### "I have noticeable latency when monitoring through Reason"
- Buffer is too large for tracking. **Drop to 64-256 samples** during recording, raise it back for mixing.
- Wrong driver on Windows (MME/DirectX adds 40-160 ms). **Switch to ASIO.**
- Use the interface's **direct hardware monitoring** if software monitoring is still too slow.

### "Audio Out clip indicator lights up but I can't find the source"
- Master is too hot. Pull down the Master Section fader.
- The metronome **click can flash the clip LED** without actual distortion. Disable click to verify.
- Master Section clip indicators only work correctly if **nothing is patched between the Master Section and Hardware Interface**.

### "Imported audio sounds wrong / pitched / muddled"
- Source file is at a different sample rate. Reason converts automatically, but **wait for the CALC indicator to finish** for the high-quality version.
- For permanent matching, render/bounce after the CALC pass completes.

### "VST/external instrument is out of tune"
- **Master Tune does NOT affect VST plugins or audio tracks** - tune within the plugin or use a tuning utility.

### "Old song now sounds different"
- Likely caused by **Render audio using audio card buffer size setting** being toggled. Songs using **feedback routings or CV** are sensitive to this. Try unchecking it for legacy projects.

## Do This / Don't Do This

**Do:**
- Use ASIO (Win) or Core Audio (macOS).
- Match sample rate to your delivery format.
- Use small buffers for tracking, large buffers for mixing.
- Set record level at the hardware/preamp.
- Keep Master Section peaks below 0 dBFS.
- Update interface drivers regularly.

**Don't:**
- Don't run MME/DirectX drivers for serious work.
- Don't use sample rates below 44.1 kHz.
- Don't worry about device/channel meters going red internally - only Hardware Interface clipping matters.
- Don't patch cables to Hardware Interface Audio In jacks for sequencer tracks - use the track's Audio Input dropdown.
- Don't fight clipping with the master fader if a Maximizer is the right tool.
- Don't assume Master Tune affects VSTs - it doesn't.

## Key Relationships

- **Buffer Size <-> Latency <-> DSP Load:** smaller buffer = lower latency = higher DSP risk. Always a three-way trade.
- **Sample Rate <-> CPU + Latency:** higher rate adds CPU AND latency.
- **Hardware Interface device <-> physical I/O:** indicators (green/yellow/red) reveal capability mismatches.
- **Internal floating-point processing <-> Hardware Interface output:** hot internal levels are fine; only the Hardware Interface output matters for audible clipping.
- **Audio Preferences <-> Real-Time Performance:** every change here flows directly to recording/playback behavior. Re-tune for the task at hand (tracking vs. mixing vs. bouncing).
