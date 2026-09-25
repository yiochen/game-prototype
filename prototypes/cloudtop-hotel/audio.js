// Quiet synthesized paper clicks: no network assets and no sound before explicit opt-in.
export function paperAudio() {
  let context, enabled = false;
  function tone(frequency, delay = 0, duration = .07) {
    if (!enabled || !context) return;
    const oscillator = context.createOscillator(), gain = context.createGain(), now = context.currentTime + delay;
    oscillator.type = 'triangle'; oscillator.frequency.setValueAtTime(frequency, now); oscillator.frequency.exponentialRampToValueAtTime(frequency * .6, now + duration);
    gain.gain.setValueAtTime(.018, now); gain.gain.exponentialRampToValueAtTime(.0001, now + duration);
    oscillator.connect(gain); gain.connect(context.destination); oscillator.start(now); oscillator.stop(now + duration);
    oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
  }
  return {
    toggle() { enabled = !enabled; if (enabled) { const Audio = window.AudioContext || window.webkitAudioContext; if (!Audio) { enabled = false; return enabled; } context ??= new Audio(); void context.resume(); } return enabled; },
    fold() { tone(560); },
    finish() { tone(523, 0, .18); tone(659, .12, .18); tone(784, .24, .3); },
    destroy() { void context?.close(); },
  };
}
