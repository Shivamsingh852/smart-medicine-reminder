let audioContext;

function getAudioContext() {
  if (typeof window === 'undefined') return null;
  audioContext ||= new window.AudioContext();
  return audioContext;
}

export function unlockRingtone() {
  const context = getAudioContext();
  if (context?.state === 'suspended') context.resume();
}

function playTone(context, frequency, startTime, duration) {
  const oscillator = context.createOscillator();
  const gain = context.createGain();
  oscillator.type = 'sine';
  oscillator.frequency.setValueAtTime(frequency, startTime);
  gain.gain.setValueAtTime(0.0001, startTime);
  gain.gain.exponentialRampToValueAtTime(0.18, startTime + 0.02);
  gain.gain.exponentialRampToValueAtTime(0.0001, startTime + duration);
  oscillator.connect(gain);
  gain.connect(context.destination);
  oscillator.start(startTime);
  oscillator.stop(startTime + duration);
}

export function playMedicineRingtone() {
  const context = getAudioContext();
  if (!context) return;

  context.resume().then(() => {
    const start = context.currentTime;
    [0, 0.28, 0.56, 1.12, 1.4, 1.68].forEach((offset) => {
      playTone(context, offset < 1 ? 880 : 1046.5, start + offset, 0.18);
    });
  });
}