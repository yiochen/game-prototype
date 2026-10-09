import React, { useEffect, useRef, useState } from 'react';
import { Target, Icon, Character, Money } from './common.jsx';
import './applicants.css';

function ResumeFact({ label, children }) {
  return <div className="resume-fact"><dt>{label}</dt><dd>{children}</dd></div>;
}

// A browse gesture changes the visible résumé only. Hiring is an explicit action.
export function ResumeDeck({ candidates, full = false }) {
  const [index, setIndex] = useState(0), [offset, setOffset] = useState(0);
  const [entryDirection, setEntryDirection] = useState(1);
  const drag = useRef(null), previousIds = useRef(candidates.map(candidate => candidate.id));
  const ids = candidates.map(candidate => candidate.id).join('|');
  const visibleIndex = Math.min(index, Math.max(0, candidates.length - 1));
  const candidate = candidates[visibleIndex];
  useEffect(() => {
    const nextIds = candidates.map(item => item.id);
    const isReplacement = nextIds.length && !nextIds.some(id => previousIds.current.includes(id));
    setIndex(current => isReplacement ? 0 : Math.min(current, Math.max(0, candidates.length - 1)));
    setOffset(0);
    drag.current = null;
    previousIds.current = nextIds;
  }, [ids]);

  function browse(direction) {
    const next = Math.max(0, Math.min(candidates.length - 1, visibleIndex + direction));
    setEntryDirection(direction);
    setIndex(next);
    setOffset(0);
  }
  function startDrag(event) {
    if (!event.isPrimary || event.button !== 0 || event.target.closest('button')) return;
    drag.current = { pointer: event.pointerId, x: event.clientX, y: event.clientY, distance: 0, horizontal: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function moveDrag(event) {
    const gesture = drag.current;
    if (!gesture || gesture.pointer !== event.pointerId) return;
    const x = event.clientX - gesture.x, y = event.clientY - gesture.y;
    if (!gesture.horizontal && Math.abs(y) > 10 && Math.abs(y) > Math.abs(x)) {
      drag.current = null;
      setOffset(0);
      event.currentTarget.releasePointerCapture(event.pointerId);
      return;
    }
    if (Math.abs(x) > 8) gesture.horizontal = true;
    gesture.distance = x;
    const beyondEdge = (x > 0 && visibleIndex === 0) || (x < 0 && visibleIndex === candidates.length - 1);
    setOffset(beyondEdge ? x * .22 : x);
  }
  function endDrag(event) {
    const gesture = drag.current;
    if (!gesture || gesture.pointer !== event.pointerId) return;
    drag.current = null;
    if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId);
    const threshold = Math.max(48, event.currentTarget.clientWidth * .18);
    if (gesture.horizontal && Math.abs(gesture.distance) >= threshold) browse(gesture.distance < 0 ? 1 : -1);
    else setOffset(0);
  }
  return <section className="resume-deck" aria-label="Applicant résumés" onKeyDown={event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      browse(event.key === 'ArrowRight' ? 1 : -1);
    }
  }}>
    <div className="resume-stack">
      {candidate ? <article key={candidate.id} className={`paper-resume ${offset ? 'resume-dragging' : ''}`} tabIndex={0} aria-label={`${candidate.name} résumé`} data-resume-id={candidate.id}
        style={{ '--resume-drag': `${offset}px`, '--resume-tilt': `${offset / 35}deg`, '--resume-enter': `${entryDirection * 18}px` }}
        onPointerDown={startDrag} onPointerMove={moveDrag} onPointerUp={endDrag} onPointerCancel={event => { drag.current = null; setOffset(0); if (event.currentTarget.hasPointerCapture(event.pointerId)) event.currentTarget.releasePointerCapture(event.pointerId); }}>
        <div className="resume-heading"><Character name={candidate.name}/><div><p className="resume-eyebrow">Application</p><h3>{candidate.name}</h3><p className="resume-role">{candidate.role}</p></div></div>
        <p className="resume-background">{candidate.background}</p>
        <span className="resume-trait">{candidate.trait}</span>
        <dl className="resume-facts"><ResumeFact label="Cooking speed">{candidate.speed}</ResumeFact><ResumeFact label="Growth">{candidate.growth}</ResumeFact><ResumeFact label="Maximum level">Lv {candidate.ceiling}</ResumeFact><ResumeFact label="Highest tier">{candidate.tier}</ResumeFact></dl>
        <div className="resume-hire"><Target action="hire" className="primary-action" disabled={full} data={{ value: candidate.id }} title={full ? 'Roster is full' : `Hire ${candidate.name}`}>Hire <Money kind="coins" amount={candidate.cost}/></Target></div>
      </article> : <div className="paper-resume empty-resume" role="status"><Icon name="people"/><h3>No applications left</h3></div>}
    </div>
    <nav className="resume-pagination" aria-label="Browse applicants">
      <button type="button" className="tap-target resume-page-button" aria-label="Previous applicant" disabled={!candidate || visibleIndex === 0} onClick={() => browse(-1)}><Icon name="arrow-left"/></button>
      <span aria-live="polite" aria-atomic="true">{candidate ? `${visibleIndex + 1} / ${candidates.length}` : '0 / 0'}</span>
      <button type="button" className="tap-target resume-page-button" aria-label="Next applicant" disabled={!candidate || visibleIndex === candidates.length - 1} onClick={() => browse(1)}><Icon name="arrow-right"/></button>
    </nav>
  </section>;
}
