// Pouring rules for #62: tilt -> flow -> volume -> level, drips after release and grading.
// Pure and deterministic so tests and the review UI share them.

export function flowShare(tilt, pour) {
  if (tilt <= pour.deadZone) return 0;
  return ((Math.min(1, tilt) - pour.deadZone) / (1 - pour.deadZone)) ** pour.flowCurve;
}

export function createPour(cup, tea) {
  const { pour } = tea;
  const maxFlow = cup.targetVolume / pour.secondsToTargetAtMax;   // volume per second at full tilt
  const state = { volume: 0, spilled: 0, flow: 0, drip: 0, dripLeft: 0, wasFlowing: false, poured: false };

  // tilt: 0 (upright) .. 1 (end of arc). held: whether the player is still holding the control.
  function step(dt, tilt, held) {
    const share = held ? flowShare(tilt, pour) : 0;
    if (state.wasFlowing && share === 0) {
      // Stopping always leaves the same small trail of drops, whatever the flow was.
      state.dripLeft = cup.targetVolume * pour.dripShare;
    }
    state.wasFlowing = share > 0;
    let add = share * maxFlow * dt;
    state.drip = 0;
    if (!share && state.dripLeft > 0) {
      const d = Math.min(state.dripLeft, cup.targetVolume * pour.dripShare * dt / pour.dripSeconds);
      state.dripLeft -= d;
      state.drip = d / dt;
      add += d;
    }
    state.flow = share;
    if (add > 0) state.poured = true;
    state.volume += add;
    if (state.volume > cup.capacity) {
      state.spilled += state.volume - cup.capacity;
      state.volume = cup.capacity;
    }
    return state;
  }

  return { state, step, maxFlow, level: () => cup.levelFor(state.volume) };
}

// One chance per request: the serving ends once tea has flowed and the flow is back to zero
// (released, or tilted back past the dead zone) and the trailing drops have landed.
export function pourDone(state) {
  return state.poured && state.flow === 0 && state.dripLeft <= 0;
}

// Grade a finished serving. Bands are measured in interior height around the fill line.
export function gradePour(cup, state, tea) {
  const { grade } = tea;
  const level = cup.levelFor(state.volume);
  const offset = (level - cup.targetHeight) / cup.height;
  const fill = state.volume / cup.targetVolume;
  let id;
  if (state.spilled > 0) id = 'overflow';
  else if (Math.abs(offset) <= grade.idealBand) id = 'ideal';
  else if (Math.abs(offset) <= grade.goodBand) id = 'good';
  else if (offset < 0) id = 'under';
  else id = 'full';
  const qualifies = id === 'overflow' ? grade.overflowQualifies : fill >= grade.minQualifyingFill;
  return { id, offset, fill, qualifies };
}

// Final tip chance for a visit. Tea raises the chance once per visit; it never reaches certainty.
export function tipChance(visit, tea) {
  const { tip } = tea;
  if (visit.ateRequestedDish) return tip.requestedDish;
  if (!visit.teaGrade?.qualifies) return tip.base;
  return Math.min(0.95, tip.tea + (visit.teaGrade.id === 'ideal' ? tip.idealBonus : 0));
}
