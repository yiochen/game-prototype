// Quiet synthesized paper clicks: no network assets and no sound before explicit opt-in.
export function paperAudio() {
  let context, enabled = false;
  return {
    toggle() { enabled = !enabled; if (enabled) { const Audio = window.AudioContext || window.webkitAudioContext; if (!Audio) { enabled = false; return enabled; } context ??= new Audio(); void context.resume(); } return enabled; },
    fold() {
      if (!enabled || !context) return;
      const oscillator = context.createOscillator(), gain = context.createGain(), now = context.currentTime;
      oscillator.type = 'triangle'; oscillator.frequency.setValueAtTime(560, now); oscillator.frequency.exponentialRampToValueAtTime(220, now + .045);
      gain.gain.setValueAtTime(.022, now); gain.gain.exponentialRampToValueAtTime(.0001, now + .065);
      oscillator.connect(gain); gain.connect(context.destination); oscillator.start(now); oscillator.stop(now + .07);
      oscillator.onended = () => { oscillator.disconnect(); gain.disconnect(); };
    },
    destroy() { void context?.close(); },
  };
}
