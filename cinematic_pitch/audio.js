/**
 * AeroCPI Cinematic Pitch — Procedural Web Audio Sound Engine
 * Generates rich, cinematic, synthesized soundscapes and SFX using pure Web Audio API.
 * Zero external audio files required. Offline resilient.
 */

class CinematicAudioEngine {
  constructor() {
    this.ctx = null;
    this.masterGain = null;
    this.isMuted = false;
    this.volume = 0.65;
    this.isInitialized = false;
    this.droneNodes = null;
    this.isAudioEnabled = true;
  }

  init() {
    if (this.isInitialized) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return;
      this.ctx = new AudioContextClass();

      // Master Gain
      this.masterGain = this.ctx.createGain();
      this.masterGain.gain.setValueAtTime(this.isMuted ? 0 : this.volume, this.ctx.currentTime);
      this.masterGain.connect(this.ctx.destination);

      this.isInitialized = true;
      this.startAmbientSoundscape();
    } catch (e) {
      console.warn("Web Audio API init deferred/failed:", e);
    }
  }

  resume() {
    if (this.ctx && this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  setVolume(val) {
    this.volume = Math.max(0, Math.min(1, val));
    if (this.masterGain && this.ctx && !this.isMuted) {
      this.masterGain.gain.setTargetAtTime(this.volume, this.ctx.currentTime, 0.05);
    }
  }

  toggleMute() {
    this.isMuted = !this.isMuted;
    if (this.masterGain && this.ctx) {
      this.masterGain.gain.setTargetAtTime(this.isMuted ? 0 : this.volume, this.ctx.currentTime, 0.05);
    }
    return this.isMuted;
  }

  /**
   * Continuous Cinematic Deep Ambient Drone & Atmospheric Wind Shimmer
   */
  startAmbientSoundscape() {
    if (!this.ctx || this.droneNodes) return;

    const t = this.ctx.currentTime;

    // 1. Sub-bass fundamental (55 Hz - A1)
    const osc1 = this.ctx.createOscillator();
    osc1.type = 'sine';
    osc1.frequency.setValueAtTime(55, t);

    // 2. Detuned warmth oscillator (55.4 Hz)
    const osc2 = this.ctx.createOscillator();
    osc2.type = 'triangle';
    osc2.frequency.setValueAtTime(55.4, t);

    // Sub filter
    const subFilter = this.ctx.createBiquadFilter();
    subFilter.type = 'lowpass';
    subFilter.frequency.setValueAtTime(140, t);

    // LFO for slow breathing pulse
    const lfo = this.ctx.createOscillator();
    lfo.type = 'sine';
    lfo.frequency.setValueAtTime(0.12, t); // ~8 sec period

    const lfoGain = this.ctx.createGain();
    lfoGain.gain.setValueAtTime(30, t);
    lfo.connect(lfoGain);
    lfoGain.connect(subFilter.frequency);

    const droneGain = this.ctx.createGain();
    droneGain.gain.setValueAtTime(0.08, t);

    osc1.connect(subFilter);
    osc2.connect(subFilter);
    subFilter.connect(droneGain);
    droneGain.connect(this.masterGain);

    osc1.start();
    osc2.start();
    lfo.start();

    // 3. Pink noise cabin air resonance
    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      b3 = 0.86650 * b3 + white * 0.3104856;
      b4 = 0.55000 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.0168980;
      output[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.04;
      b6 = white * 0.115926;
    }

    const noiseSource = this.ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    const noiseFilter = this.ctx.createBiquadFilter();
    noiseFilter.type = 'bandpass';
    noiseFilter.frequency.setValueAtTime(380, t);
    noiseFilter.Q.setValueAtTime(1.8, t);

    const noiseGain = this.ctx.createGain();
    noiseGain.gain.setValueAtTime(0.035, t);

    noiseSource.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(this.masterGain);

    noiseSource.start();

    this.droneNodes = { osc1, osc2, lfo, droneGain, noiseSource, noiseGain };
  }

  /**
   * Sound Effect: Camera whoosh & aircraft fly-by
   */
  playWhoosh(intensity = 1.0) {
    if (!this.ctx || !this.isInitialized || this.isMuted) return;
    this.resume();

    const t = this.ctx.currentTime;
    const dur = 0.85 * intensity;

    const bufferSize = this.ctx.sampleRate * dur;
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = Math.random() * 2 - 1;
    }

    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(180, t);
    filter.frequency.exponentialRampToValueAtTime(1800, t + dur * 0.4);
    filter.frequency.exponentialRampToValueAtTime(120, t + dur);
    filter.Q.setValueAtTime(2.5, t);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.001, t);
    gain.gain.exponentialRampToValueAtTime(0.18 * intensity, t + dur * 0.35);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + dur);

    noise.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    noise.start(t);
    noise.stop(t + dur);
  }

  /**
   * Sound Effect: Metallic impact & shimmer for title reveals
   */
  playMetallicImpact() {
    if (!this.ctx || !this.isInitialized || this.isMuted) return;
    this.resume();

    const t = this.ctx.currentTime;

    // Sub thump
    const subOsc = this.ctx.createOscillator();
    subOsc.type = 'sine';
    subOsc.frequency.setValueAtTime(110, t);
    subOsc.frequency.exponentialRampToValueAtTime(32, t + 0.45);

    const subGain = this.ctx.createGain();
    subGain.gain.setValueAtTime(0.28, t);
    subGain.gain.exponentialRampToValueAtTime(0.0001, t + 0.6);

    subOsc.connect(subGain);
    subGain.connect(this.masterGain);
    subOsc.start(t);
    subOsc.stop(t + 0.6);

    // High metal bell partials (FM)
    const freqs = [587.33, 880, 1174.66, 1760, 2349.32];
    freqs.forEach((f, idx) => {
      const osc = this.ctx.createOscillator();
      osc.type = idx % 2 === 0 ? 'sine' : 'triangle';
      osc.frequency.setValueAtTime(f, t);

      const gain = this.ctx.createGain();
      const vol = 0.06 / (idx + 1);
      gain.gain.setValueAtTime(vol, t);
      gain.gain.exponentialRampToValueAtTime(0.00001, t + 1.2 + idx * 0.2);

      osc.connect(gain);
      gain.connect(this.masterGain);
      osc.start(t);
      osc.stop(t + 1.5);
    });
  }

  /**
   * Sound Effect: Discrete data ticks / quote ticker / chip entry
   */
  playDataTick(pitch = 1200) {
    if (!this.ctx || !this.isInitialized || this.isMuted) return;
    this.resume();

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(pitch, t);
    osc.frequency.exponentialRampToValueAtTime(pitch * 0.4, t + 0.04);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.04, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.045);

    osc.connect(gain);
    gain.connect(this.masterGain);

    osc.start(t);
    osc.stop(t + 0.05);
  }

  /**
   * Sound Effect: Hero Chord Pad for major milestone reveals (AeroCPI, Final Headline)
   */
  playHeroChord() {
    if (!this.ctx || !this.isInitialized || this.isMuted) return;
    this.resume();

    const t = this.ctx.currentTime;
    const notes = [146.83, 220.0, 261.63, 329.63, 440.0];

    notes.forEach((freq, idx) => {
      const osc = this.ctx.createOscillator();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, t);

      const filter = this.ctx.createBiquadFilter();
      filter.type = 'lowpass';
      filter.frequency.setValueAtTime(400, t);
      filter.frequency.exponentialRampToValueAtTime(2800, t + 0.6);
      filter.frequency.exponentialRampToValueAtTime(600, t + 3.0);

      const gain = this.ctx.createGain();
      gain.gain.setValueAtTime(0.001, t);
      gain.gain.linearRampToValueAtTime(0.07 / Math.sqrt(idx + 1), t + 0.4);
      gain.gain.exponentialRampToValueAtTime(0.0001, t + 3.2);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(this.masterGain);

      osc.start(t);
      osc.stop(t + 3.3);
    });
  }

  /**
   * Sound Effect: Laser data sweep for architecture line connections
   */
  playLaserSweep() {
    if (!this.ctx || !this.isInitialized || this.isMuted) return;
    this.resume();

    const t = this.ctx.currentTime;
    const osc = this.ctx.createOscillator();
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(320, t);
    osc.frequency.exponentialRampToValueAtTime(2400, t + 0.35);

    const filter = this.ctx.createBiquadFilter();
    filter.type = 'bandpass';
    filter.frequency.setValueAtTime(800, t);
    filter.frequency.exponentialRampToValueAtTime(3200, t + 0.35);
    filter.Q.setValueAtTime(3.0, t);

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.04, t);
    gain.gain.exponentialRampToValueAtTime(0.0001, t + 0.4);

    osc.connect(filter);
    filter.connect(gain);
    gain.connect(this.masterGain);

    osc.start(t);
    osc.stop(t + 0.4);
  }
}

// Global instance
window.cinematicAudio = new CinematicAudioEngine();
