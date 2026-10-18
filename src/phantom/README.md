# Phantom Sound Lab

A self-contained interactive explanation of timing cues and spatial ambiguity. Built with AI assistance; the geometry and cited psychoacoustic research are established work.

Open index.html manually or serve it with a static web server. JavaScript updates the diagrams. The page makes no app network requests, loads no external assets and collects no data. User-clicked primary-source links navigate to external sites, which receive the visitor’s request and IP address. The page requests no referrer on those navigations. The hosting provider may have its own logs.

Audio starts muted. Optional playback needs an amplitude adjustment and an explicit Play press, has a 0.04 digital-peak limit and finite duration, and resets to silence on tab hiding. Idle playback requests suspension of the audio context; page exit requests closure. Playback stops independently of these best-effort cleanup requests. Forced mute stops immediately, so an interruption transient remains possible and is not acoustically tested. Use low device volume. No acoustic calibration or listening evaluation is claimed.

## Model and limits

Two unobstructed point receivers are 0.18 m apart, c = 343 m/s. Positive delay means right receiver earlier. At world 30°/150° both delays are 262.4 μs before a turn; a 20° yaw yields 91.1/402.0 μs. This is not an individualized HRTF or a promise of externalized perception.

Two nonparallel yaw poses constrain horizontal components and, for a stationary unit direction with known calibration, elevation magnitude. Above/below sign remains ambiguous. A moving alternative at 150 + 2 × yaw degrees matches the fixed 30° source at each static pose. This does not solve retarded-time moving acoustics or Doppler. Noise, wrong pose sign and calibration-scale examples expose further assumptions.

The rigid-sphere companion omits pinnae, torso, room and headphone correction. Its unwrapped phase delay is not a pulse-onset or human delay measurement. Unknown common source spectra cancel in an interaural ratio, but detectability is not established.

## Reproduce

Requires Python 3.10+ and Node.js 18+ on the host. The verifier checks these minimum versions. No package dependencies or installation:

```sh
python3 -B scripts/verify.py
```

This builds index.html and runs existing numerical/signal checks, a deliberately small DOM/WebAudio mock, finite-series checks and bounded synthetic counterexamples. Results go only to results/. Seeds and parameters are explicit. No browser, audio device or person is involved in verification. Real rendering, device channel order, sound pressure, physical phones and assistive technology remain unverified.

This educational module includes its implementation, source references and model checks. No paper PDFs or third-party figures are bundled.

See SOURCES.md for primary attribution. No third-party paper text, datasets or media are redistributed. No express open-source reuse license is selected; follow the collection's COPYRIGHT.txt policy. No new license grant is implied.
