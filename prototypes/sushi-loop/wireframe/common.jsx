import React from 'react';

export function Target({ children, action, className = '', disabled = false, data = {}, title = '', ...rest }) {
  const attributes = Object.fromEntries(Object.entries(data).map(([key, value]) => [`data-${key.replace(/[A-Z]/g, match => `-${match.toLowerCase()}`)}`, value]));
  return <button type="button" className={`tap-target ${className}`} data-action={action} {...attributes} disabled={disabled} aria-disabled={disabled || undefined} title={title || undefined} aria-label={title || undefined} {...rest}>{children}</button>;
}

const icons = {
  coin: <><circle cx="12" cy="12" r="8" /><path d="M14.5 8.5h-3a2 2 0 0 0 0 4h1a2 2 0 0 1 0 4h-3M12 6.5v11" /></>,
  salvage: <path d="m12 3 8 6-3 10H7L4 9zM4 9h16M12 3l-3 6 3 10 3-10z" />,
  edit: <path d="m4 16-1 5 5-1L20 8l-4-4zM13 7l4 4" />,
  staff: <><circle cx="9" cy="7" r="3" /><path d="M3 20v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6M19 20v-3a6 6 0 0 0-2-4" /></>,
  shop: <path d="M3 9h18l-2-6H5zM5 9v12h14V9M9 21v-7h6v7M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0" />,
  workshop: <path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7" />,
  submarine: <><rect x="3" y="8" width="17" height="11" rx="5" /><circle cx="9" cy="13.5" r="2" /><path d="M13 8V4h4M20 11h2v6h-2" /></>,
  'arrow-left': <path d="m10 5-7 7 7 7M3 12h18" />,
  'arrow-right': <path d="m14 5 7 7-7 7M3 12h18" />,
  close: <path d="m5 5 14 14M19 5 5 19" />,
  plus: <path d="M12 4v16M4 12h16" />,
  minus: <path d="M4 12h16" />,
  check: <path d="m4 12 5 5L20 6" />,
  lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" /></>,
  rotate: <path d="M4 11a8 8 0 1 1 2 7M4 4v7h7" />,
  trash: <path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7M14 10v7" />,
  pause: <path d="M8 5v14M16 5v14" />,
  play: <path d="m7 4 13 8-13 8z" />,
  harpoon: <path d="M4 20 19 5M12 5h7v7M4 15l5 5" />,
  floor: <path d="M3 3h18v18H3zM3 9h18M3 15h18M9 3v18M15 3v18" />,
  people: <><circle cx="12" cy="7" r="4" /><path d="M5 22v-4a7 7 0 0 1 14 0v4" /></>,
  layout: <path d="M3 3h8v8H3zM15 3h6v8h-6zM3 15h8v6H3zM15 15h6v6h-6z" />,
  info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6M12 7v1" /></>,
  comment: <path d="M4 4h16v13H9l-5 4V4M8 8h8M8 12h5" />,
};

export function Icon({ name, ...rest }) {
  return <svg className="wire-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...rest}>{icons[name] || icons.info}</svg>;
}

export function Money({ kind = 'coin', amount }) {
  return <span className="wire-money"><Icon name={kind === 'salvage' ? 'salvage' : 'coin'} /><span>{typeof amount === 'number' ? amount.toLocaleString('en-US') : amount}</span></span>;
}

export function Character({ name, kind = 'chef', ...rest }) {
  const seed = [...name].reduce((n, char) => n + char.charCodeAt(0), 0);
  const hair = seed % 3;
  const skin = ['#f5f6f7', '#dce2e7', '#aebbc7', '#8295a5'][seed % 4];
  return <svg className="wire-character" viewBox="0 0 48 62" width="48" height="62" role="img" aria-label={name} {...rest}><g stroke="#233345" strokeWidth="1.7" strokeLinejoin="round">
    <path d="M7 61V50q1-13 17-13t17 13v11" fill="#eef2f5" />
    <ellipse cx="24" cy="27" rx="12" ry="14" fill={skin} />
    {kind === 'chef' ? <><path d="M12 21V12q0-6 6-6 3-6 7-1 7-2 9 5v11" fill="white" /><path d="M12 21h22" /></> : hair === 0 ? <path d="M13 24q-2-15 11-15t12 15l-5-6-14 3z" fill="#677582" /> : hair === 1 ? <path d="M13 25q-5-18 11-18 17 2 12 18l-8-8z" fill="#8998a5" /> : <path d="M12 22q0-14 12-14t12 14" strokeWidth="6" />}
    <path d="M19 26v2M29 26v2M20 33q4 3 8 0" fill="none" />
    {seed % 2 === 1 && <path d="M15 25h8v5h-8zM25 25h8v5h-8zM23 27h2" fill="none" />}
    <path d="M18 42v17M30 42v17" />
  </g></svg>;
}
