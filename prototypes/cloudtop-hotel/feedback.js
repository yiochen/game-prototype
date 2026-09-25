// Transient presentation only. Cancel every animation/timer on replay, reduced
// motion, or disposal; none of these callbacks may commit a game action.
export function createFeedback(isReduced, paper) {
  const animations = new Set();
  let timer;
  const toast = document.getElementById('purchase-feedback');
  const coin = document.getElementById('coin-change');
  function animate(element, frames, options) {
    if (!element || isReduced()) return;
    const animation = element.animate(frames, options);
    animations.add(animation);
    animation.onfinish = () => { animations.delete(animation); animation.cancel(); };
  }
  function pulse(element) {
    animate(element, [{ transform: 'scale(1)' }, { transform: 'scale(1.16)', offset: .35 }, { transform: 'scale(1)' }], { duration: 300, easing: 'ease-out' });
  }
  function clear() {
    clearTimeout(timer); paper?.clear(document.querySelector('.hotel-app'));
    for (const animation of animations) { animation.onfinish = null; animation.cancel(); }
    animations.clear(); toast.hidden = true; coin.textContent = '';
  }
  return {
    pulse, clear,
    spend(price, refund = 0) {
      coin.textContent = `−${price}${refund ? ` / +${refund} back` : ''}`;
      animate(coin, [{ opacity: 1, transform: 'translateY(0)' }, { opacity: 1, offset: .65 }, { opacity: 0, transform: 'translateY(16px)' }], { duration: 1100, easing: 'ease-out' });
      pulse(document.getElementById('coins'));
    },
    announce(text) {
      clearTimeout(timer); toast.textContent = text; toast.hidden = false;
      paper?.unfold(toast,{axis:'y',duration:260});
      timer = setTimeout(() => { toast.hidden = true; }, 2400);
    },
    deal() {
      document.querySelectorAll('#offers .offer-card').forEach((card, i) => animate(card,
        [{ opacity: 0, translate: '0 12px' }, { opacity: 1, translate: '0 -2px', offset: .8 }, { opacity: 1, translate: '0 0' }],
        { duration: 240, delay: i * 55, easing: 'ease-out', fill: 'backwards' }));
    }
  };
}
