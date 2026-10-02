export const BALANCE = {
  width: 400, height: 500, beeRadius: 13, flowerRadius: 28,
  pullMax: 96, pullMin: 10, launchPower: 5.5, friction: 0.16,
  restitution: 0.97, maxFlight: 6, stopSpeed: 28, step: 1 / 120,
};
// Every garden can be completed in three or fewer launches. Par awards a medal;
// exceeding it never ends a run or removes flowers already pollinated.
export const GARDENS = [
  { name: 'Good morning', par: 3, home: [200, 415], flowers: [[200, 170], [92, 285], [310, 275]], drops: [[130, 150, 28], [275, 375, 27]], wind: [0, 0] },
  { name: 'Dewdrop detour', par: 3, home: [78, 415], flowers: [[82, 145], [300, 240], [305, 100]], drops: [[195, 295, 35], [193, 110, 27]], wind: [0, 0] },
  { name: 'A little breeze', par: 3, home: [200, 425], flowers: [[90, 165], [310, 215], [190, 80]], drops: [[155, 280, 32], [280, 110, 28]], wind: [17, -2] },
  { name: 'The lily lounge', par: 3, home: [320, 425], flowers: [[75, 105], [80, 335], [290, 135]], drops: [[185, 240, 37], [180, 95, 27], [300, 305, 27]], wind: [-9, 0] },
  { name: 'Golden hour', par: 3, home: [195, 420], flowers: [[67, 215], [322, 210], [200, 80]], drops: [[122, 330, 28], [277, 328, 28], [200, 205, 33]], wind: [0, -12] },
];
export const LESSONS = [
  { name: 'A little stretch', par: 1, home: [200, 370], flowers: [[200, 180]], drops: [], wind: [0, 0] },
  { name: 'Dewdrops bounce!', par: 1, home: [100, 370], flowers: [[100, 450]], drops: [[100, 175, 34]], wind: [0, 0] },
];
