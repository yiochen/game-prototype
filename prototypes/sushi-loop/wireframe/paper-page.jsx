import React, { useId, useState } from 'react';
import { Target } from './common.jsx';
import './paper-page.css';

// The page and return corner are shared; each screen supplies its own contents.
export function PaperPage({ title, balance, background, children, className = '' }) {
  const [lifted, setLifted] = useState(false);
  const foldId = `paper-fold-${useId().replaceAll(':', '')}`;
  return <div className={`paper-page ${className} ${lifted ? 'paper-corner-lifted' : ''}`}>
    <div className="paper-restaurant-background" aria-hidden="true" inert>{background || <div className="paper-floor-preview"><span className="paper-entry-preview" /></div>}</div>
    <section className="paper-sheet" aria-label={`${title} page`}>
      <header className="paper-heading"><h2>{title}</h2>{balance}</header>
      <div className="paper-content">{children}</div>
    </section>
    <Target action="navigate" data={{story:'restaurant-live'}} className="paper-return" title="Return to restaurant" onPointerEnter={event => event.pointerType === 'mouse' && setLifted(true)} onPointerLeave={() => setLifted(false)} onPointerDown={() => setLifted(true)} onPointerUp={() => setLifted(false)} onPointerCancel={() => setLifted(false)}>
      <svg viewBox="0 0 72 72" aria-hidden="true"><defs><linearGradient id={foldId} x1="0" y1="1" x2="1" y2="0"><stop stopColor="#dce3e8"/><stop offset="1" stopColor="#f8fafb"/></linearGradient></defs><path d="M1 1 1 71 71 71Z" fill={`url(#${foldId})`} stroke="#96a6b2" strokeWidth="1"/><path d="M1 1 71 71" stroke="#bec9d1" strokeWidth="1"/></svg>
    </Target>
  </div>;
}
