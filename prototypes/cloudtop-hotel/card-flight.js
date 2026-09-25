import './card-flight.css';

// Read the actual four projected corners, including the common tray plane,
// hover lift and any card slant. A bounding rectangle alone loses perspective.
function projectedCardTransform(source, width, height) {
  const style = getComputedStyle(source);
  const borderX = parseFloat(style.borderLeftWidth) || 0;
  const borderY = parseFloat(style.borderTopWidth) || 0;
  const corners = [[0,0],[width,0],[width,height],[0,height]].map(([x,y]) => {
    const point = document.createElement('span');
    Object.assign(point.style, { position: 'absolute', left: `${x-borderX}px`, top: `${y-borderY}px`, width: '0', height: '0', pointerEvents: 'none' });
    source.append(point);
    const rect = point.getBoundingClientRect();
    point.remove();
    return { x: rect.x, y: rect.y };
  });
  const [a,b,c,d] = corners;
  const dx1 = b.x-c.x, dx2 = d.x-c.x, dx3 = a.x-b.x+c.x-d.x;
  const dy1 = b.y-c.y, dy2 = d.y-c.y, dy3 = a.y-b.y+c.y-d.y;
  const denominator = dx1*dy2-dx2*dy1;
  const g = denominator ? (dx3*dy2-dx2*dy3)/denominator : 0;
  const h = denominator ? (dx1*dy3-dx3*dy1)/denominator : 0;
  const projection = new DOMMatrix([
    (b.x-a.x+g*b.x)/width, (b.y-a.y+g*b.y)/width, 0, g/width,
    (d.x-a.x+h*d.x)/height, (d.y-a.y+h*d.y)/height, 0, h/height,
    0,0,1,0, a.x,a.y,0,1
  ]);
  // Flight uses a center origin for its inflation, so compensate for that
  // origin around the corner-based projection before Web Animations takes over.
  return new DOMMatrix().translate(-width/2,-height/2).multiply(projection).translate(width/2,height/2).toString();
}

// The purchase stays pending until onBurst. Resetting a game cancels it instead;
// revealing or reducing motion finishes it, applying that callback exactly once.
export function createCardFlight() {
  let current = null, destroyed = false;

  function stopAnimations(flight) {
    for (const animation of flight.animations) {
      animation.onfinish = null;
      animation.cancel();
    }
    flight.animations.clear();
  }

  function clean(flight) {
    stopAnimations(flight);
    flight.overlay.remove();
    flight.source?.classList.remove('card-flight-source');
    if (current === flight) current = null;
  }

  function burstCallback(flight) {
    if (current !== flight || flight.applied) return;
    flight.applied = true;
    try { flight.onBurst?.({ x: flight.x + flight.width / 2, y: flight.y + flight.height / 2 }); }
    catch (error) { clean(flight); throw error; }
  }

  function complete(flight) {
    if (current !== flight) return;
    clean(flight);
    flight.onComplete?.();
  }

  function animate(flight, element, frames, options, after) {
    if (current !== flight) return;
    const animation = element.animate(frames, { fill: 'forwards', ...options });
    flight.animations.add(animation);
    // Use the event callback instead of .finished, whose promise rejects on reset.
    animation.onfinish = () => {
      if (current !== flight) return;
      after?.();
    };
  }

  function cloneCard(source) {
    const clone = source.cloneNode(true);
    clone.classList.remove('card-flight-source');
    clone.classList.add('card-flight-card');
    clone.removeAttribute('id');
    clone.removeAttribute('data-folding');
    for (const rig of clone.querySelectorAll('.paper-fold-rig')) rig.remove();
    clone.removeAttribute('aria-label');
    clone.removeAttribute('title');
    clone.removeAttribute('disabled');
    clone.setAttribute('aria-hidden', 'true');
    clone.inert = true;
    for (const child of clone.querySelectorAll('[id]')) child.removeAttribute('id');
    for (const child of clone.querySelectorAll('button,a,input,[tabindex]')) child.tabIndex = -1;
    return clone;
  }

  function burst(flight) {
    if (current !== flight) return;
    const { overlay, card, width, height, x, y, scale } = flight;
    overlay.dataset.phase = 'burst';
    card.style.visibility = 'hidden';
    const centerX = x + width / 2, centerY = y + height / 2;
    const ring = document.createElement('span');
    ring.className = 'card-flight-ring';
    Object.assign(ring.style, { left: `${centerX}px`, top: `${centerY}px`, width: `${width * scale * .75}px`, height: `${height * scale * .75}px` });
    overlay.append(ring);
    animate(flight, ring, [
      { transform: 'translate(-50%,-50%) scale(.5)', opacity: 1 },
      { transform: 'translate(-50%,-50%) scale(1.75)', opacity: 0 }
    ], { duration: 330, easing: 'cubic-bezier(.15,.7,.2,1)' });

    // Eight actual pieces of the selected card preserve its artwork and paper
    // edges as it bursts, rather than replacing it with unrelated confetti.
    const edges = [[0, 0], [50, 0], [100, 0], [100, 50], [100, 100], [50, 100], [0, 100], [0, 50]];
    edges.forEach(([ax, ay], index) => {
      const [bx, by] = edges[(index + 1) % edges.length];
      const angle = Math.atan2((ay + by) / 2 - 50, (ax + bx) / 2 - 50);
      const distance = Math.min(innerWidth, innerHeight) * .14 + (index % 3) * 12;
      const piece = cloneCard(card);
      piece.classList.add('card-flight-fragment');
      Object.assign(piece.style, { left: `${x}px`, top: `${y}px`, width: `${width}px`, height: `${height}px`, visibility: 'visible', clipPath: `polygon(50% 50%,${ax}% ${ay}%,${bx}% ${by}%)` });
      overlay.append(piece);
      const dx = Math.cos(angle) * distance, dy = Math.sin(angle) * distance;
      animate(flight, piece, [
        { transform: `scale(${scale * 1.13}) rotate(0deg)`, opacity: 1, offset: 0 },
        { transform: `translate(${dx * .8}px,${dy * .8}px) scale(${scale * .65}) rotate(${index % 2 ? 28 : -28}deg)`, opacity: 1, offset: .45 },
        { transform: `translate(${dx}px,${dy + 25}px) scale(${scale * .22}) rotate(${index % 2 ? 65 : -65}deg)`, opacity: 0, offset: 1 }
      ], { duration: 350 + (index % 3) * 25, easing: 'cubic-bezier(.12,.67,.22,1)' });
    });

    for (let i = 0; i < 10; i++) {
      const spark = document.createElement('span'), angle = i * Math.PI / 5;
      const reach = Math.min(innerWidth, innerHeight) * .22;
      spark.className = `card-flight-spark${i % 2 ? ' paper' : ''}`;
      Object.assign(spark.style, { left: `${centerX}px`, top: `${centerY}px`, '--spark-turn': `${i * 36}deg` });
      overlay.append(spark);
      animate(flight, spark, [
        { transform: `translate(-50%,-50%) rotate(${i * 36}deg) scale(.25)`, opacity: 0 },
        { transform: `translate(calc(-50% + ${Math.cos(angle) * reach * .7}px),calc(-50% + ${Math.sin(angle) * reach * .7}px)) rotate(${i * 48}deg) scale(1)`, opacity: 1, offset: .3 },
        { transform: `translate(calc(-50% + ${Math.cos(angle) * reach}px),calc(-50% + ${Math.sin(angle) * reach + 15}px)) rotate(${i * 65}deg) scale(.35)`, opacity: 0 }
      ], { duration: 420, easing: 'cubic-bezier(.15,.65,.25,1)' }, i === 9 ? () => complete(flight) : undefined);
    }
    burstCallback(flight);
  }

  function finish() {
    const flight = current;
    if (!flight) return;
    burstCallback(flight);
    complete(flight);
  }

  function cancel() { if (current) clean(current); }

  function play(source, { onBurst, onComplete } = {}) {
    if (destroyed) return;
    cancel();
    const rect = source?.getBoundingClientRect();
    if (!rect?.width || !rect.height) { onBurst?.(); onComplete?.(); return; }
    const overlay = document.createElement('div');
    overlay.className = 'card-flight';
    overlay.dataset.phase = 'flight';
    overlay.setAttribute('aria-hidden', 'true');
    overlay.inert = true;
    const card = cloneCard(source), width = source.offsetWidth || rect.width, height = source.offsetHeight || rect.height;
    const scale = Math.min(1.35, innerWidth * .57 / width, innerHeight * .46 / height);
    const x = (innerWidth - width) / 2, y = (innerHeight - height) / 2;
    const style = getComputedStyle(source), slant = parseFloat(style.getPropertyValue('--slant')) || 0;
    const fromX = rect.left + (rect.width - width) / 2;
    const fromTransform = projectedCardTransform(source, width, height);
    Object.assign(card.style, { width: `${width}px`, height: `${height}px`, padding: style.padding, '--card-edge': style.getPropertyValue('--card-edge') });
    overlay.style.setProperty('--burst-paper', style.getPropertyValue('--card-edge') || '#edc981');
    overlay.append(card); document.body.append(overlay);
    source.classList.add('card-flight-source');
    const flight = { overlay, source, card, width, height, x, y, scale, onBurst, onComplete, applied: false, animations: new Set() };
    current = flight;
    const center = `translate3d(${x}px,${y}px,0) scale(${scale})`;
    animate(flight, card, [
      { transform: fromTransform, offset: 0 },
      { transform: `translate3d(${x + (fromX - x) * .08}px,${y - 14}px,0) perspective(900px) rotateX(-5deg) rotate(${-slant * .7}deg) scale(${scale * 1.025})`, offset: .82 },
      { transform: center, offset: 1 }
    ], { duration: 300, easing: 'cubic-bezier(.16,.78,.22,1)' }, () => {
      overlay.dataset.phase = 'inflate';
      animate(flight, card, [
        { transform: center, borderRadius: '8px', filter: 'brightness(1)' },
        { transform: `${center} scale(.94,1.045)`, borderRadius: '18px', filter: 'brightness(1.03)', offset: .27 },
        { transform: `${center} scale(1.15,1.13)`, borderRadius: '32px', filter: 'brightness(1.2)', offset: .88 },
        { transform: `${center} scale(1.18,1.16)`, borderRadius: '38px', filter: 'brightness(1.35)' }
      ], { duration: 110, easing: 'cubic-bezier(.4,0,.8,.3)' }, () => burst(flight));
    });
    return { finish: () => { if (current === flight) finish(); }, cancel: () => { if (current === flight) cancel(); } };
  }

  return { play, finish, cancel, destroy: () => { cancel(); destroyed = true; }, get active() { return Boolean(current); } };
}
