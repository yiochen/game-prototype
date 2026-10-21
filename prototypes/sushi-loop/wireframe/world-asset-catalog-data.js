// Issue #33 concept-review inventory, not gameplay or completed production assets.
export const worldAssetFamilies = [
  {
    "id": "W01",
    "name": "Restaurant floors",
    "items": "Plain cream tile, Blue wave, Checker; restrained matching repetition variants",
    "states": "Seamless square repetition; static alternative for any subtle flare",
    "panels": [
      4
    ]
  },
  {
    "id": "W02",
    "name": "Perimeter & entrances",
    "items": "Four-by-three-tile entrance backdrop, one-by-three-tile blank wood wall, wall middles/corners/end caps, plants, barrels, crates, lanterns, blank sign, subdued rocks, dock posts/rope",
    "states": "Three blank wall tiles, four-tile entrance, then blank walls; top three rows reserved; two-tile opening; uniform lighting",
    "panels": [
      5
    ]
  },
  {
    "id": "W03",
    "name": "Seats & furniture",
    "items": "Backless honey-wood stool, blue-seat cosmetic concept",
    "states": "N/E/S/W where visually needed; stable ground root and explicit seat socket; occupied composition",
    "panels": [
      6,
      17
    ]
  },
  {
    "id": "W04",
    "name": "Connected conveyors",
    "items": "Four directed straights, eight directed corners (two valid flows for each of four geometries), four facing start caps and four facing open/end caps",
    "states": "Running, frozen and scrubbed; touching strips, all compatible joins, closed loop and independent routes; dishes separate and allowed to remain stationary over moving deck",
    "panels": [
      8
    ]
  },
  {
    "id": "W05",
    "name": "Chef identities",
    "items": "Lena Brooks, Omar Haddad, Ama Mensah, Mateo Rivera, Noor Haddad, Dalia Farouk, Ellis Morgan, Rowan McLeod",
    "states": "Every identity N/E/S/W \u00d7 idle/inactive, work, completed-dish hold, load-to-facing-belt; hand/dish sockets; no invented walking or separate station",
    "panels": [
      1,
      17
    ]
  },
  {
    "id": "W06",
    "name": "Chef blackboards",
    "items": "Blank player-facing board at the front of the chef tile; recipe art is drawn dynamically",
    "states": "One readable player-facing surface; selected/idle and local recipe-change shake",
    "panels": [
      6
    ]
  },
  {
    "id": "W07",
    "name": "Customer identities",
    "items": "Current review identities Rosa, Ellis, Samir, June; four proposed looks, not a final progression roster",
    "states": "N/E/S/W \u00d7 walk, stand/wait, seated/wait, eat; sit/stand transitions, happy bounce, restless, puzzled, panic/slow wandering; arrive/leave reuse walk",
    "panels": [
      2,
      6,
      17
    ]
  },
  {
    "id": "W08",
    "name": "Dishes & world feedback",
    "items": "Salmon nigiri, Cucumber maki, Eel roll; dish-preference/timer, happy, puzzled and panic bubbles; coin icon",
    "states": "Matching held/belt/seat/bubble art, appearance/fade and happy transition, manually set circular timer fill, coin pop without amount",
    "panels": [
      3,
      2
    ]
  },
  {
    "id": "W09",
    "name": "Whole garbage clusters",
    "items": "Whole broken sofa, wrecked car, collapsed shelving with distinct supporting rubbish and separately declared integer-cell masks",
    "states": "Normal/highlighted, clearance scatter/fade and clean-floor reveal; never repeated per-cell debris stamps",
    "panels": [
      7
    ]
  },
  {
    "id": "W10",
    "name": "Dock & Workshop",
    "items": "Yellow sub, hut to its right, shared 3\u00d73 dock floor, entry pieces, patchwork cover and peek holes",
    "states": "Covered/uncovered, charging/ready, restrained ready headlight pulse; no charge calculation or UI timers",
    "panels": [
      9
    ]
  },
  {
    "id": "W11",
    "name": "Underwater modular terrain",
    "items": "Turquoise square floor; connected rock/canyon, shelf, reef and wreck modules; middles, edges, corners, ends; boulder and broken-column forms",
    "states": "Water static/scroll; integer-cell and half-width barriers, runs longer than viewport, continuous ship-sized gap; no invented mines/gates/spike mechanics",
    "panels": [
      11
    ]
  },
  {
    "id": "W12",
    "name": "Layered underwater scenery",
    "items": "Foreground rocks/coral/starfish; midground coral/kelp/ruin fragments; quieter background rocks, wreck and fish silhouettes; bubbles/light",
    "states": "Separate nonblocking metadata/layers; restrained ambient loops; keep actors/pickups/hazards readable",
    "panels": [
      12
    ]
  },
  {
    "id": "W13",
    "name": "Submarine & equipment",
    "items": "Recognizable yellow ship, hull panels, harpoon mount, collector inlet, baseline/upgraded appearance assemblies",
    "states": "Same dock/dive identity; clear upward overhead dive view, idle/travel, impact/protection; fixed bounds/pivot; no new stats/inertia/knockback",
    "panels": [
      10
    ]
  },
  {
    "id": "W14",
    "name": "Salvage & route features",
    "items": "Metal fragment variants, lateral current cues, boost/trail, portal rim/entry, safe bonus-passage scenery",
    "states": "Pickup shimmer/attraction/collection, current flow, boost glow/trail, portal idle/entry; presentation only",
    "panels": [
      14
    ]
  },
  {
    "id": "W15",
    "name": "Creature families",
    "items": "Eel and current generic fish example only; no invented final species list",
    "states": "Swim/aim, restless, hook, pursuit, caught pose/short world clip, escape; weaving/dash/pause gestures with stable hit silhouette",
    "panels": [
      13
    ]
  },
  {
    "id": "W16",
    "name": "Harpoon, cable & following strip",
    "items": "Separate projectile, ship/creature sockets, normal/taut/fraying/broken cable, faint vertical following strip",
    "states": "Launch/flight/hook, cable loops/break; open-ended vertical strip at creature x; no grace countdown, return arrow or resistance HUD",
    "panels": [
      15
    ]
  },
  {
    "id": "W17",
    "name": "World attack warnings",
    "items": "Reef fragments, swirls, lateral attack currents, amber diagonally hatched eel strip/lightning symbol, electrical discharge",
    "states": "Windup/active/recovery, composed safe following position; no damage, attack scheduling or new hazard mechanics",
    "panels": [
      16
    ]
  }
];

// View boxes into the original concept sheet, for review only; no production sprites are extracted.
export const conceptPanels = {
  "1": [
    14,
    78,
    459,
    362
  ],
  "2": [
    479,
    78,
    275,
    362
  ],
  "3": [
    762,
    78,
    252,
    362
  ],
  "4": [
    14,
    447,
    238,
    220
  ],
  "5": [
    260,
    447,
    255,
    220
  ],
  "6": [
    522,
    447,
    245,
    220
  ],
  "7": [
    774,
    447,
    240,
    220
  ],
  "8": [
    14,
    673,
    488,
    292
  ],
  "9": [
    509,
    673,
    254,
    292
  ],
  "10": [
    770,
    673,
    244,
    292
  ],
  "11": [
    14,
    970,
    481,
    308
  ],
  "12": [
    505,
    970,
    255,
    308
  ],
  "13": [
    772,
    970,
    242,
    308
  ],
  "14": [
    14,
    1283,
    263,
    228
  ],
  "15": [
    282,
    1283,
    257,
    228
  ],
  "16": [
    545,
    1283,
    244,
    228
  ],
  "17": [
    795,
    1283,
    219,
    228
  ]
};
