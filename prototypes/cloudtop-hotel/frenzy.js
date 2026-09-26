// Presentation only: seamless paper rainbows travel behind the hotel. Keeping
// these transforms outside the canvas leaves the room animation cadence intact.
export function mountFrenzy(parent) {
  const layer = document.createElement('div');
  layer.className = 'frenzy-sky'; layer.setAttribute('aria-hidden', 'true');
  const colors = ['#fa647c', '#ffa451', '#ffe36b', '#9ddb77', '#5dd7ee', '#6d94f1', '#bc85ec'];
  const animations = [];
  let active = false, motion = true;
  for (let band = 0; band < 3; band++) {
    const ribbon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    ribbon.setAttribute('viewBox', '0 0 1600 380');
    ribbon.setAttribute('preserveAspectRatio', 'none');
    ribbon.classList.add('frenzy-rainbow'); ribbon.style.top = `${8 + band * 34}%`;
    for (const [i, color] of colors.entries()) {
      const path = document.createElementNS(ribbon.namespaceURI, 'path'), y = 70 + i * 24;
      // Each half is identical, including its tangent at the seam.
      path.setAttribute('d', `M0 ${y} C200 ${y - 95} 200 ${y - 95} 400 ${y} S600 ${y + 95} 800 ${y} C1000 ${y - 95} 1000 ${y - 95} 1200 ${y} S1400 ${y + 95} 1600 ${y}`);
      path.setAttribute('fill', 'none'); path.setAttribute('stroke', color); path.setAttribute('stroke-width', '25');
      ribbon.append(path);
    }
    layer.append(ribbon);
    const animation = ribbon.animate([{ transform: 'translateX(0)' }, { transform: 'translateX(-50%)' }], { duration: 14000 + band * 3500, iterations: Infinity, easing: 'linear', direction: band === 1 ? 'reverse' : 'normal' });
    animation.pause(); animation.currentTime = band * 3200 + 1200; animations.push(animation);
  }
  for (let i = 0; i < 24; i++) {
    const fleck = document.createElement('i'); fleck.className = 'frenzy-confetti';
    fleck.style.cssText = `left:${(i * 37 + 3) % 100}%;top:${(i * 19 + 5) % 100}%;background:${colors[i % colors.length]};rotate:${i * 43}deg`;
    layer.append(fleck);
    const animation = fleck.animate([
      { transform: 'translate(-12px,-18px) rotate(0deg)', opacity: .2 },
      { opacity: .85, offset: .3 },
      { transform: 'translate(24px,55px) rotate(130deg)', opacity: 0 },
    ], { duration: 3500 + i % 5 * 450, iterations: Infinity });
    animation.pause(); animation.currentTime = i * 173; animations.push(animation);
  }
  parent.append(layer);
  function sync() {
    parent.dataset.frenzy = String(active);
    for (const animation of animations) active && motion ? animation.play() : animation.pause();
  }
  sync();
  return {
    setActive(value) { if (active === value) return; active = value; sync(); },
    setMotion(value) { motion = value; sync(); },
    destroy() { animations.forEach(a => a.cancel()); layer.remove(); },
  };
}
