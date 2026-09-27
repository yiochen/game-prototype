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

export const assetManifest = Object.entries(ART).map(([key, source]) => ({ key, url: `data:image/svg+xml;base64,${btoa(source)}` }));
