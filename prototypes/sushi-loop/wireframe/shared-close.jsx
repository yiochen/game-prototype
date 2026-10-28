import React from 'react';
import './shared-close.css';

// The same cream round X used by the approved applicant and chef popups.
export function SharedClose({onClick,label='Close'}) {
 return <button className="round shared-close" onClick={onClick} aria-label={label}><svg className="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="m7 7 10 10M17 7 7 17"/></svg></button>;
}
