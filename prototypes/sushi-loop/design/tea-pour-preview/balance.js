// Tuning for the #62 tea request and pouring review. Rules live in cups.js / pour.js.
export const TEA = {
  request: {
    patienceSeconds: 10,      // godot/content/tips.json tea.request_seconds
    pulseFraction: 0.3,       // gentle pulse once this share of patience remains
    perVisit: 1,              // requests allowed per customer visit
    maxSimultaneous: 2,       // pending requests across the restaurant
    autoEverySeconds: 9,      // ambient request roll in this preview (0 = only the buttons)
  },
  pour: {
    maxTiltDegrees: 58,       // teapot tilt at the end of the control arc
    deadZone: 0.12,           // share of the arc that only lifts the pot (no flow)
    flowCurve: 1.6,           // flow = ((tilt - deadZone) / (1 - deadZone)) ^ flowCurve
    secondsToTargetAtMax: 2.2, // full-tilt time to the fill line; sets each cup's max flow
    dripShare: 0.025,         // trailing drops after release, as a share of the target volume
    dripSeconds: 0.35,
    returnSeconds: 0.14,      // pot springs upright on release
  },
  grade: {                    // bands are shares of the cup's interior height around the fill line
    idealBand: 0.03,
    goodBand: 0.085,
    minQualifyingFill: 0.4,   // below this share of the target volume, tea gives no tip bonus
    overflowQualifies: true,  // overflow still counts as served (reduced feedback only)
  },
  tip: {                      // final tip chances per visit (godot/content/tips.json)
    base: 0.05,
    tea: 0.2,
    idealBonus: 0.05,         // proposed extra for an ideal pour; still never a guaranteed tip
    requestedDish: 0.5,
  },
  service: {
    mealSeconds: 5,
    gapSeconds: 1.4,
    sipSeconds: 1.8,
    happySeconds: 2.2,        // happy bubble after eating the requested dish; a tea bubble waits for it
    requestedDishChance: 0.3, // preview only: share of dishes that are the guest's requested one
    teaAfterHappyChance: 0.6, // preview only: ambient tea request right after the happy bubble
    dishPrice: [4, 9],
  },
};
