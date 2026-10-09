import React, { useState } from 'react';
import { Target, Icon } from './common.jsx';
import './inventory-tray.css';

// One compact paging rail for profiles, objects, and floor swatches.
export function PaginatedTray({ items, pageSize = 2, renderItem, label = 'Inventory', itemsClassName = '', className = '' }) {
  const [page, setPage] = useState(0);
  const pages = Math.max(1, Math.ceil(items.length / pageSize));
  const activePage = Math.min(page, pages - 1);
  const controlName = label.toLowerCase();
  return <nav className={`paginated-tray ${className}`} aria-label={`${label} pages`}>
    <Target className="tray-page-button" title={`Previous ${controlName} page`} disabled={activePage === 0} onClick={() => setPage(activePage - 1)}><Icon name="arrow-left" /></Target>
    <div className={`paginated-tray-items ${itemsClassName}`} role="group" aria-label={`${label} page ${activePage + 1} of ${pages}`} style={{ '--tray-page-size': pageSize }}>
      {items.slice(activePage * pageSize, (activePage + 1) * pageSize).map(renderItem)}
    </div>
    <Target className="tray-page-button" title={`Next ${controlName} page`} disabled={activePage === pages - 1} onClick={() => setPage(activePage + 1)}><Icon name="arrow-right" /></Target>
    <span className="sr-only" aria-live="polite">{label} page {activePage + 1} of {pages}</span>
  </nav>;
}
