import React from 'react';
import {SharedClose} from '../../wireframe/shared-close.jsx';
import './exhibition-unlock.css';

export const exhibitionArt = new URL('./unlock-art/v1/underwater.webp', import.meta.url).href;

// Shared by the actual reveal flow and the direct review fixture.
// Text and controls stay independent from the full-aspect ImageGen illustration.
export function ExhibitionUnlock({onClose, onGo, pressed = false}) {
 return <section className="wr-panel exhibition-unlock" role="dialog" aria-modal="true" aria-labelledby="exhibition-title">
  <header className="exhibition-header">
   <h1 id="exhibition-title">Exhibition Unlocked</h1>
   <SharedClose onClick={onClose} label="Close"/>
  </header>
  <div className="exhibition-art"><img src={exhibitionArt} width="1536" height="1024" alt="A yellow submarine exploring turquoise water among coral, fish and ancient underwater ruins." draggable="false"/></div>
  <footer><button className={`wr-prepare exhibition-go ${pressed ? 'sample-pressed' : ''}`} onClick={onGo}>Let's go</button></footer>
 </section>;
}
