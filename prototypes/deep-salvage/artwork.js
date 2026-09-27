const svg = (width, height, body) => `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">${body}</svg>`;

export const ART = {
  submarine: svg(240, 130, `<g stroke="#163e4b" stroke-width="5" stroke-linejoin="round">
    <path d="M52 76 22 45 13 47l8 33-5 29 15 2 25-20" fill="#eea837"/>
    <path d="M110 32V14q0-6 8-6h25v13h-20v18" fill="#eeb53c"/>
    <rect x="135" y="7" width="15" height="16" rx="5" fill="#ffe38a"/>
    <path d="M85 100v18l33-13m26-6 10 16 20-16" fill="#d68a29"/>
    <path d="M57 36q39-23 112-7 41 6 43 36-2 40-53 44H76q-39-3-38-36 0-24 19-37" fill="#f8c545"/>
    <path d="M60 91q70 23 145-15-5 29-50 30H76q-17-1-25-10" fill="#eaa536" stroke="none"/>
    <path d="M65 44q45-18 94-9" fill="none" stroke="#ffe9a1" stroke-width="8" stroke-linecap="round"/>
    <path d="M155 29q-22 40 0 78" fill="none" stroke="#bb8229" stroke-width="4"/>
    <ellipse cx="170" cy="64" rx="25" ry="31" fill="#4aa6b3"/>
    <ellipse cx="173" cy="61" rx="17" ry="23" fill="#98e2dc" stroke="none"/>
    <path d="m165 48 11-3" stroke="white" stroke-width="5" stroke-linecap="round"/>
    <circle cx="79" cy="66" r="16" fill="#267688"/><circle cx="79" cy="66" r="10" fill="#9ce7e0" stroke="none"/>
    <circle cx="119" cy="63" r="15" fill="#267688"/><circle cx="119" cy="63" r="9" fill="#9ce7e0" stroke="none"/>
    <path d="m74 61 5-3m34 1 6-3" stroke="white" stroke-width="3" stroke-linecap="round"/>
    <path d="M192 55h29v11h-30m-2 13h34v11h-41" fill="#7caaa9"/>
    <rect x="213" y="51" width="12" height="19" rx="3" fill="#dce7c3"/><rect x="218" y="75" width="12" height="18" rx="3" fill="#dce7c3"/>
    <path d="M43 62H30v27h15" fill="#548993"/>
    <path d="M28 76v-22m0 23v24" stroke="#aacac1" stroke-width="8" stroke-linecap="round"/>
    <path d="M58 47v8m0 30v6m80-48v6m0 34v6" stroke="#986321" stroke-width="3"/>
  </g>`),
  scout: svg(120, 110, `<g stroke="#27364f" stroke-width="5" stroke-linejoin="round" stroke-linecap="round">
    <path d="m32 66-17 15-6 20 16-13 16-9m45-14 18 15 7 19-18-13-17-8M43 76l-4 24 15-17m14-6 12 23-1-29" fill="#8569bb"/>
    <path d="M57 26 50 12m17 13 9-13" fill="none"/><circle cx="49" cy="10" r="5" fill="#efacd9"/>
    <ellipse cx="61" cy="52" rx="39" ry="30" fill="#9982cf"/><path d="M27 60q35 28 69-4-8 27-38 28-25-1-31-24" fill="#6e55a9" stroke="none"/>
    <path d="M36 37q16-13 34-7" stroke="#d2c0f5" stroke-width="6" fill="none"/>
    <circle cx="62" cy="52" r="18" fill="#503966"/><circle cx="62" cy="52" r="10" fill="#f59bcf" stroke="none"/><circle cx="60" cy="49" r="4" fill="#ffe5ec" stroke="none"/>
    <path d="m24 48-9-6m84 2 9-6"/><circle cx="83" cy="38" r="3" fill="#e8d8ee" stroke="none"/>
  </g>`),
  crab: svg(150, 130, `<g stroke="#453844" stroke-width="5" stroke-linejoin="round" stroke-linecap="round">
    <path d="m37 75-22 10L6 116l24-19 15-13m66-9 21 11 11 29-24-16-17-14M55 93l-9 25 22-18m21-4 15 22-2-29" fill="#c26761"/>
    <path d="M64 25V10h23v14" fill="#ef9a7c"/>
    <path d="M27 52Q38 19 77 23q44 0 52 34l-7 30q-10 20-45 20T26 83Z" fill="#ee8f77"/>
    <path d="M28 73q44 33 98-3-2 35-50 36-42-1-48-33" fill="#c66863" stroke="none"/>
    <path d="m41 43 14-9m20-2 24 9" stroke="#ffc8a0" stroke-width="7"/>
    <path d="M73 25v10m41 14 7 12M35 60l-6 5" stroke="#a65358"/>
    <circle cx="76" cy="65" r="26" fill="#9b525b"/><circle cx="76" cy="65" r="16" fill="#ffcf76"/><circle cx="73" cy="61" r="7" fill="#fff2b5" stroke="none"/>
  </g>`),
};

// Distinct silhouettes make enemy roles readable at phone scale.
const creature = body => svg(120, 110, `<g stroke="#253a4c" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">${body}</g>`);
Object.assign(ART, {
  swarm: ART.scout.replaceAll('#9982cf', '#c99adb').replaceAll('#6e55a9', '#9157a2'),
  warden: ART.crab.replaceAll('#ee8f77', '#7eacca').replaceAll('#c66863', '#487692').replaceAll('#ffcf76', '#a9eeff'),
  dart: creature('<path d="m105 55-46-29-5 17L9 55l45 12 5 17z" fill="#e8cb61"/><path d="m56 39 22-25-3 29m-19 28 22 25-3-29" fill="#83c9a8"/><path d="M18 55h35" stroke="#faffc0" stroke-width="7"/><circle cx="72" cy="55" r="11" fill="#405866"/><circle cx="70" cy="55" r="5" fill="#ffecb2"/>'),
  bulwark: creature('<path d="M17 29h76l16 26-12 35H23L9 60z" fill="#738597"/><path d="M30 20h46l17 17H22z" fill="#b5bdc0"/><path d="m18 33 23 24-15 24m66-48L70 57l15 24" fill="#465b77"/><path d="M39 37h34v40H39z" fill="#dfad64"/><path d="M44 45h24v24H44z" fill="#334451"/><path d="M47 55h18" stroke="#ffedaa" stroke-width="6"/><path d="M22 91v10m19-10v10m38-10v10m18-10v10"/>'),
  sniper: creature('<path d="m66 35 39-20-4 39 6 36-37-16" fill="#a575aa"/><ellipse cx="72" cy="55" rx="29" ry="27" fill="#cf9abc"/><path d="M7 46h62v18H7z" fill="#adbec5"/><path d="M6 43h15v24H6z" fill="#f1d09c"/><circle cx="76" cy="52" r="12" fill="#4d425e"/><circle cx="73" cy="51" r="5" fill="#ffe5a8"/><path d="m78 29 8-18m-10 69 9 17"/>'),
  leech: creature('<path d="M106 49q-25-30-47-14T14 49q-10 25 19 37 31 7 41-19t32-18" fill="#84bfce"/><path d="M99 45Q76 36 69 58T37 76" fill="none" stroke="#dbf5ae" stroke-width="9"/><ellipse cx="25" cy="59" rx="17" ry="21" fill="#465d82"/><path d="m25 45-9 15h10l-3 13 11-18H24z" fill="#ffe990" stroke-width="2"/><path d="m68 33 5-18 10 18m-28 48 7 17 8-20" fill="#52899c"/>'),
  mender: creature('<path d="M24 52q36-64 72 0z" fill="#86d6ae"/><path d="M24 53h72v15H24z" fill="#d4f1c0"/><path d="M33 70q-13 17 0 30m17-30q15 17 0 30m20-30q-15 17 0 30m17-30q13 17 0 30" fill="none" stroke="#81c8b6" stroke-width="7"/><circle cx="60" cy="46" r="17" fill="#337b75"/><path d="M60 36v20M50 46h20" stroke="#dffff0" stroke-width="6"/>'),
  bomber: creature('<path d="M52 20V7h16v13M19 46 7 37m94 9 12-9M27 82l-10 15m76-15 10 15" stroke="#e2b985" stroke-width="7"/><circle cx="60" cy="57" r="37" fill="#e9956f"/><path d="M31 31 89 84m0-53L31 84" stroke="#8f4f57" stroke-width="11"/><circle cx="60" cy="57" r="21" fill="#f8d18b"/><path d="m60 41 15 27H45z" fill="#834b56"/><path d="M60 49v8m0 6v1" stroke="#ffe9be"/>'),
});

export const assetManifest = Object.entries(ART).map(([key, source]) => ({ key, url: `data:image/svg+xml;base64,${btoa(source)}` }));
