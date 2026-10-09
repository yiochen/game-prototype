import React, { useRef, useState } from 'react';
import { Target, Icon, Character } from './common.jsx';
import { roster, chefAssigned } from './fixtures.js';
import { PaginatedTray } from './inventory-tray.jsx';
import './staff-tray.css';

function dropAt(element, x, y) {
  const scene = element.closest('.phone-scene, .roster-example');
  const viewport = scene?.querySelector('[data-pan-scroll]');
  const panel = viewport?.querySelector('[data-floor-panel="0"].cleared');
  const tray = element.querySelector('.roster-tray');
  if (!viewport || !panel || !tray) return null;
  const visible = viewport.getBoundingClientRect();
  const floor = panel.getBoundingClientRect();
  const trayTop = tray.getBoundingClientRect().top;
  const hit = document.elementFromPoint(x, y);
  if (x < Math.max(floor.left + 6, visible.left) || x > Math.min(floor.right, visible.right)
    || y < Math.max(floor.top + 100, visible.top) || y >= Math.min(floor.bottom - 6, trayTop)
    || hit?.closest('button, .customer-entry')) return null;
  return { panel: 0, x: (x - floor.left) / floor.width, y: (y - floor.top) / floor.height };
}

// Presentation-only roster. The parent owns the mock assignment through the bubbling event.
export function RosterTray({ state = {}, embedded = false }) {
  const chefs = roster(state);
  const [drag, setDrag] = useState(null);
  const container = useRef(null);
  const pointer = useRef(null);
  const suppressClick = useRef(false);

  function start(event, chef) {
    if (event.button !== 0 || !event.isPrimary) return;
    suppressClick.current = false;
    pointer.current = { id: event.pointerId, chef, x: event.clientX, y: event.clientY, dragging: false };
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  function move(event) {
    const current = pointer.current;
    if (!current || current.id !== event.pointerId) return;
    if (!current.dragging && Math.hypot(event.clientX - current.x, event.clientY - current.y) < 8) return;
    current.dragging = true;
    event.preventDefault();
    const bounds = container.current.getBoundingClientRect();
    setDrag({ chef: current.chef, x: event.clientX - bounds.left, y: event.clientY - bounds.top,
      valid: Boolean(dropAt(container.current, event.clientX, event.clientY)) });
  }
  function finish(event, canceled = false) {
    const current = pointer.current;
    if (!current || current.id !== event.pointerId) return;
    pointer.current = null;
    setDrag(null);
    if (!current.dragging) return;
    suppressClick.current = true;
    event.preventDefault();
    event.stopPropagation();
    const position = !canceled && dropAt(container.current, event.clientX, event.clientY);
    if (position) container.current.dispatchEvent(new CustomEvent('sushi-roster-place', {
      bubbles: true, detail: { chefId: current.chef.id, position },
    }));
  }
  function click(event) {
    if (!suppressClick.current) return;
    suppressClick.current = false;
    event.preventDefault();
    event.stopPropagation();
  }

  return <div className={`roster-tray-shell ${embedded ? 'roster-tray-embedded' : ''}`} ref={container} data-roster-tray>
    <section className="roster-tray" aria-label="Staff roster">
      <header className="roster-tray-header"><h2>Staff <small className="roster-count">{chefs.length} / 4</small></h2>
        <Target action="navigate" data={{ story: 'staff-applicants' }} className="roster-applicants"><Icon name="staff" /><span>Applicants</span></Target>
        {!embedded && <Target action="navigate" data={{ story: 'restaurant-live' }} className="roster-close" title="Close staff tray"><Icon name="close" /></Target>}
      </header>
      <PaginatedTray items={chefs} pageSize={3} label="Staff" className="roster-pagination" itemsClassName="roster-profiles" renderItem={chef => <Target key={chef.id}
          action="navigate" data={{ story: 'staff-detail', value: chef.id }}
          title={`Inspect ${chef.name}`} className={`roster-profile ${drag?.chef.id === chef.id ? 'roster-profile-dragging' : ''}`}
          onPointerDown={event => start(event, chef)} onPointerMove={move}
          onPointerUp={finish} onPointerCancel={event => finish(event, true)}
          onLostPointerCapture={event => finish(event, true)} onClick={click}>
          <Character name={chef.name} />
          <span className="roster-profile-copy"><strong>{chef.name}</strong><small>{chefAssigned(state, chef) ? 'Assigned' : 'Unassigned'}</small></span>
          <span className="roster-drag-grip" aria-hidden="true">⠿</span>
        </Target>} />
    </section>
    {drag && <div className={`roster-drag-ghost ${drag.valid ? 'roster-drop-valid' : ''}`} style={{ left: drag.x, top: drag.y }} aria-hidden="true"><Character name={drag.chef.name} /><span>{drag.chef.name}</span></div>}
  </div>;
}
