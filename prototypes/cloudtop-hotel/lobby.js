import './lobby.css';
import { cleanName, SCORE_VERSION } from './score-rules.js';

const API = '/api/cloudtop-hotel/leaderboard';
const element = (tag, className, text) => { const el = document.createElement(tag); el.className = className; if (text != null) el.textContent = text; return el; };

export function mountLobby({ img, guestbook, paper, isReduced, onStart, onResume, onRules, onSound, onMotion }) {
  const root = element('section', 'frontdesk'); root.id = 'frontdesk'; root.setAttribute('aria-label', 'Hotel lobby');
  root.innerHTML = `
    <div class="lobby-page home-page" id="home-page">
      <header class="lobby-top" data-enter data-delay="50"><a href="/" class="collection-link">← The paper collection</a><span class="edition-label">EST. IN THE CLOUDS</span></header>
      <div class="welcome-layout">
        <div class="welcome-copy">
          <div class="hanging-sign" data-enter="sign" data-delay="100"><p class="welcome-eyebrow" data-enter data-delay="190">A LITTLE PAPER. A LOT OF POSSIBILITY.</p><h1 id="home-title" tabindex="-1"><span data-enter data-delay="250">Cloudtop</span><span data-enter data-delay="340">Hotel<span class="title-star" aria-hidden="true">✦</span></span></h1><div class="sign-rule" data-enter data-delay="400"><span>ROOM FOR EVERYONE</span></div></div>
          <p class="welcome-description" data-enter data-delay="470">A pocketful of coins.<br>A sky full of possibilities.</p>
          <div class="welcome-actions">
            <button class="paper-button primary-button" id="lobby-play" data-enter data-delay="550"><span class="button-symbol" aria-hidden="true">✦</span><span>Build a hotel</span><span aria-hidden="true">→</span></button>
            <button class="paper-button resume-button" id="lobby-resume" data-enter data-delay="590" hidden>Continue your stay <span aria-hidden="true">→</span></button>
            <button class="paper-button guestbook-button" id="lobby-board" data-enter data-delay="650"><span class="book-symbol" aria-hidden="true">▤</span><span>The guestbook<small>Leaderboard & your best stays</small></span><span aria-hidden="true">↗</span></button>
          </div>
          <button class="text-button how-button" id="lobby-rules" data-enter data-delay="720">First visit? How to play <span aria-hidden="true">↗</span></button>
        </div>
        <div class="welcome-illustration" aria-hidden="true">
          <div class="hotel-postcard">
            <div class="hero-halo" data-enter="bloom" data-delay="0"></div>
            <span class="sky-note" data-enter data-delay="850">Your next great stay<br>starts with one floor.</span>
            <div class="hero-balloon hero-balloon-a" data-enter="balloon" data-delay="650"></div><div class="hero-balloon hero-balloon-b" data-enter="balloon" data-delay="800"></div>
            <div class="hero-island" data-enter="island" data-delay="80"></div>
            <div class="hero-hotel"><div class="hero-roof" data-enter="roof" data-delay="520"></div><div class="hero-floor cat" data-enter="floor" data-delay="390"></div><div class="hero-floor bunny" data-enter="floor" data-delay="280"></div><div class="hero-floor frog" data-enter="floor" data-delay="170"></div></div>
            <div class="welcome-seal" data-enter="stamp" data-delay="850"><span>100</span><small>COINS<br>ENDLESS CHARM</small></div>
            <span class="hero-spark spark-a" data-enter="stamp" data-delay="700">✦</span><span class="hero-spark spark-b" data-enter="stamp" data-delay="850">✧</span>
          </div>
        </div>
      </div>
      <footer class="lobby-bottom"><p id="lobby-best" data-enter data-delay="800">Make a little room for something wonderful.</p><div class="lobby-preferences" data-enter data-delay="850"><button id="lobby-sound" aria-pressed="false">Sound off</button><button id="lobby-motion" aria-pressed="false">Reduce motion</button></div></footer>
    </div>
    <div class="lobby-page guestbook-page" id="guestbook-page" hidden>
      <header class="lobby-top" data-enter><button class="text-button" id="board-back">← Back to the lobby</button><span class="edition-label">THE CLOUDTOP COLLECTION</span></header>
      <div class="guestbook-layout">
        <aside class="guestbook-intro"><span class="eyebrow" data-enter data-delay="70">EVERY HOTEL HAS A STORY</span><h1 id="board-title" tabindex="-1" data-enter data-delay="140">The <br>guestbook<span aria-hidden="true">.</span></h1><p data-enter data-delay="220">Little rooms. <br>Extraordinary heights.</p><div class="guestbook-medal" aria-hidden="true" data-enter="stamp" data-delay="360"></div><p class="ranking-note" data-enter data-delay="420">Tallest hotels first. <br>Ties: neighborhoods, then coins saved.</p><button class="paper-button primary-button" id="board-play" data-enter data-delay="470">Build your next hotel <span aria-hidden="true">→</span></button></aside>
        <section class="guestbook-paper" aria-label="Leaderboard" data-enter="page" data-delay="100">
          <div class="book-binding" aria-hidden="true"></div>
          <div class="board-tabs" aria-label="Leaderboard view" data-enter data-delay="250"><button id="board-everyone" aria-pressed="true">Everyone</button><button id="board-personal" aria-pressed="false">Your hotels</button></div>
          <p class="board-caption" id="board-caption" data-enter data-delay="300">The 100 tallest stays in the clouds</p>
          <form id="score-form" class="score-form" data-enter data-delay="350" hidden><div><strong id="score-heading">Leave your mark</strong><p id="score-summary"></p></div><label for="innkeeper-name">Public innkeeper name</label><div class="signature-line"><input id="innkeeper-name" name="name" maxlength="20" autocomplete="nickname" placeholder="e.g. Cloud Keeper" required><button class="paper-button primary-button" id="score-submit" type="submit">Sign guestbook</button></div><p class="signature-note">Your name, score and hotel seed will be visible to everyone.</p><p id="score-message" role="status"></p></form>
          <div class="board-scroll" tabindex="0" aria-label="Hotel rankings"><ol id="leaderboard-rows" aria-label="Ranked hotels"></ol><div id="board-empty" class="board-empty" hidden><div class="empty-art" aria-hidden="true" data-enter="stamp"></div><h2 id="empty-title" data-enter data-delay="60"></h2><p id="empty-detail" data-enter data-delay="110"></p><button class="text-button" id="board-retry" data-enter data-delay="160" hidden>Try again ↻</button></div></div>
          <footer class="book-footer" data-enter data-delay="500"><span id="board-count"></span><button class="text-button" id="board-refresh">Refresh ↻</button></footer>
        </section>
      </div>
    </div>`;
  document.body.append(root); paper.dress(root);
  const $ = id => root.querySelector(`#${id}`), app = document.querySelector('.hotel-app');
  root.querySelector('.hero-island').append(img('island'));
  root.querySelector('.hero-roof').append(img('roof'));
  for (const suit of ['cat','bunny','frog']) for (let i=0;i<3;i++) root.querySelector(`.hero-floor.${suit}`).append(img(`resident-${suit}-${i}`));
  root.querySelector('.hero-balloon-a').append(img('balloon-bunny'));
  root.querySelector('.hero-balloon-b').append(img('balloon-frog'));
  root.querySelector('.guestbook-medal').append(img('charm'));
  root.querySelector('.empty-art').append(img('parcel'));
  let artReady = false;
  let tab = 'everyone', rows = [], lastRun = null, canResume = false, transitioning = false, requestEpoch = 0, animations = [], controller;
  function clearMotion() { paper.clear(root); for (const a of animations) a.cancel(); animations = []; }
  function enter(scope) {
    if (isReduced()) return;
    for (const el of scope.querySelectorAll('[data-enter]')) {
      if (el.hidden || (!artReady && el.closest('.welcome-illustration'))) continue;
      paper.dress(el);
      if (el.hasAttribute('data-paper')) {
        const large = el.matches('.hanging-sign,.guestbook-paper');
        paper.unfold(el,{delay:Number(el.dataset.delay||0),duration:large?620:340,axis:el.matches('.hanging-sign,.score-form,.leaderboard-row')?'y':'x'});
        continue;
      }
      const transforms = { sign:['translateY(-45px) rotate(-5deg)','translateY(0) rotate(0)'], floor:['translateY(55px) scale(.8)','translateY(0) scale(1)'], roof:['translateY(-120px) rotate(8deg)','translateY(0) rotate(0)'], island:['translateY(70px)','translateY(0)'], balloon:['translateY(65px) rotate(-12deg)','translateY(0) rotate(0)'], stamp:['scale(1.5) rotate(12deg)','scale(1) rotate(0)'], page:['perspective(1000px) rotateY(-12deg) translateX(25px)','perspective(1000px) rotateY(0) translateX(0)'], bloom:['scale(.7)','scale(1)'] };
      const [from,to] = transforms[el.dataset.enter] ?? ['translateY(16px)','translateY(0)'];
      animations.push(el.animate([{opacity:0,transform:from},{opacity:1,transform:to}],{duration:el.dataset.enter==='stamp'?400:650,delay:Number(el.dataset.delay||0),easing:'cubic-bezier(.18,.8,.22,1)',fill:'backwards'}));
    }
  }
  Promise.all([...root.querySelectorAll('.welcome-illustration img')].map(image => image.decode().catch(() => {}))).then(() => {
    artReady = true; root.dataset.artReady = 'true';
    if (document.body.dataset.screen === 'home') enter(root.querySelector('.welcome-illustration'));
  });
  function front(page) {
    controller?.abort(); requestEpoch++; clearMotion(); root.scrollTop = 0; root.hidden = false; root.inert = false; app.inert = true; app.setAttribute('aria-hidden','true');
    document.body.dataset.screen = page;
    $('home-page').hidden = page !== 'home'; $('guestbook-page').hidden = page !== 'leaderboard';
    enter($(page === 'home' ? 'home-page' : 'guestbook-page'));
    $(page === 'home' ? 'home-title' : 'board-title').focus({preventScroll:true});
  }
  function game(resume = false, seed) {
    if (transitioning) return;
    transitioning = true; root.inert = true; controller?.abort(); requestEpoch++;
    const finish = () => {
      clearMotion(); root.hidden = true; root.inert = true; app.inert = false; app.removeAttribute('aria-hidden'); document.body.dataset.screen = 'game'; transitioning = false;
      if (resume) onResume(); else onStart(seed);
      if (!isReduced()) document.querySelectorAll('.dashboard [data-paper]').forEach((el,i)=>paper.unfold(el,{delay:80+i*40,duration:320}));
      document.getElementById('menu-open').focus({preventScroll:true});
      if (!isReduced()) for (const [selector,delay] of [['.dashboard',70],['.shop',170]]) {
        const el = document.querySelector(selector); animations.push(el.animate([{opacity:0,translate:'0 18px'},{opacity:1,translate:'0 0'}],{duration:450,delay,easing:'ease-out',fill:'backwards'}));
      }
    };
    if (isReduced()) { finish(); return; }
    const exit = root.animate([{opacity:1,transform:'scale(1)'},{opacity:0,transform:'scale(1.035)'}],{duration:220,easing:'ease-in'});
    exit.finished.then(finish,finish);
  }
  function preferences(sound, reduced) {
    $('lobby-sound').textContent = sound ? 'Sound on' : 'Sound off'; $('lobby-sound').setAttribute('aria-pressed',String(sound));
    $('lobby-motion').setAttribute('aria-pressed',String(reduced));
    if (reduced) clearMotion();
  }
  function home(options = {}) {
    canResume = options.canResume ?? !!guestbook.data.active;
    $('lobby-resume').hidden = !canResume;
    const best = guestbook.data.runs[0];
    $('lobby-best').textContent = best ? `Your highest stay · ${best.floors} floors ✦` : 'Make a little room for something wonderful.';
    front('home');
  }
  function empty(title, detail, retry = false) {
    $('leaderboard-rows').replaceChildren(); $('board-empty').hidden = false;
    $('empty-title').textContent = title; $('empty-detail').textContent = detail; $('board-retry').hidden = !retry;
    $('board-count').textContent = '';
    enter($('board-empty'));
  }
  function renderRows() {
    $('board-empty').hidden = true;
    $('board-caption').textContent = tab === 'everyone' ? 'The 100 tallest stays in the clouds' : (guestbook.persistent ? 'Your best finished hotels · saved on this device' : 'Your hotels this visit · device storage unavailable');
    const entries = tab === 'everyone' ? rows : guestbook.data.runs;
    if (!entries.length) { empty(tab === 'everyone' ? 'A fresh page in the clouds.' : 'Your story starts here.', tab === 'everyone' ? 'Finish a hotel and be the first to sign the guestbook.' : 'Place the roof on your first hotel. We’ll keep your best stays here.'); return; }
    $('leaderboard-rows').replaceChildren(...entries.map((entry,index) => {
      const row = element('li','leaderboard-row'); row.dataset.enter = ''; row.dataset.delay = String(Math.min(index,8)*45);
      if (entry.id === lastRun?.id || entry.id === lastRun?.serverId) row.classList.add('your-latest');
      const rank = element('span','rank-number',String(index+1).padStart(2,'0')); rank.setAttribute('aria-label',`Rank ${index+1}`);
      const avatar = element('span',`rank-portrait rank-${index%3}`); avatar.setAttribute('aria-hidden','true'); avatar.append(img(`resident-${['bunny','frog','cat'][index%3]}-0`));
      const copy = element('div','rank-copy'); copy.append(element('strong','',tab === 'everyone' ? entry.name : entry.name || 'Your hotel'),element('small','',`${entry.neighborhoods} neighborhoods · ${entry.coins} coins left`));
      const score = element('div','rank-score'); score.append(element('strong','',entry.floors),element('small','','floors'));
      if (tab === 'personal' && !entry.shared) { const share = element('button','','Sign this stay ↗'); share.addEventListener('click',()=>board(entry)); copy.append(share); }
      row.append(rank,avatar,copy,score); return row;
    }));
    $('board-count').textContent = `${entries.length} ${entries.length===1?'stay':'stays'} recorded`;
    enter($('leaderboard-rows'));
  }
  async function load() {
    controller?.abort(); const ticket = ++requestEpoch;
    $('board-caption').textContent = tab === 'everyone' ? 'The 100 tallest stays in the clouds' : (guestbook.persistent ? 'Your best finished hotels · saved on this device' : 'Your hotels this visit · device storage unavailable');
    $('board-everyone').setAttribute('aria-pressed',String(tab==='everyone')); $('board-personal').setAttribute('aria-pressed',String(tab==='personal'));
    $('board-refresh').hidden = tab === 'personal';
    if (tab === 'personal') { renderRows(); return; }
    empty('Opening the guestbook…','Gathering the tallest hotels.');
    const requestController = new AbortController(); controller = requestController;
    const timeout = setTimeout(()=>requestController.abort(),10000);
    try {
      const response = await fetch(API,{signal:requestController.signal});
      if (!response.ok) throw new Error();
      const body = await response.json(); if (!Array.isArray(body.entries)) throw new Error();
      if (ticket !== requestEpoch) return;
      rows = body.entries; renderRows();
    } catch { if (ticket===requestEpoch) empty('The guestbook is away for a moment.','You can still build a hotel and find your scores under Your hotels.',true); }
    finally { clearTimeout(timeout); }
  }
  function board(run = null) {
    lastRun = run; tab = 'everyone'; $('score-form').hidden = !run || !!run.shared;
    if (run) { $('score-summary').textContent = `${run.floors} floors · ${run.neighborhoods} neighborhoods. A stay worth remembering.`; $('innkeeper-name').value = guestbook.data.name; }
    $('score-message').textContent = ''; $('score-submit').disabled = false; $('score-submit').textContent = 'Sign guestbook';
    front('leaderboard'); load();
  }
  $('score-form').addEventListener('submit', async event => {
    event.preventDefault(); if (!lastRun || $('score-submit').disabled) return;
    let name; try { name = cleanName($('innkeeper-name').value); } catch (error) { $('score-message').textContent = error.message; return; }
    const run = lastRun, button = $('score-submit'); button.disabled = true; button.textContent = 'Signing…'; $('score-message').textContent = '';
    try {
      const response = await fetch(API,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({version:SCORE_VERSION,name,seed:run.seed,moves:run.moves}),signal:AbortSignal.timeout(12000)});
      const body = await response.json(); if (!response.ok) throw new Error(body.error || 'Please try signing again.');
      guestbook.markShared(run.id,body.entry.name,body.entry.id); run.shared = true; run.serverId = body.entry.id;
      if (lastRun !== run || document.body.dataset.screen !== 'leaderboard') return;
      controller?.abort(); requestEpoch++; rows = body.entries; tab = 'everyone'; $('board-everyone').setAttribute('aria-pressed','true'); $('board-personal').setAttribute('aria-pressed','false'); $('board-refresh').hidden = false;
      $('score-message').textContent = body.rank ? `Signed! Your hotel is #${body.rank} in the guestbook.` : 'Signed! Your stay is saved in Your hotels. The shared book shows the top 100.';
      button.textContent = 'Signed ✓'; renderRows();
    } catch(error) { if(lastRun===run) { $('score-message').textContent = error.name==='TimeoutError' ? 'The guestbook is taking a moment. Your score is still here; try again.' : error.message || 'Could not sign. Your score is still available here; try again.'; button.disabled = false; button.textContent = 'Try signing again'; } }
  });
  $('lobby-play').addEventListener('click',()=>game());
  $('lobby-resume').addEventListener('click',()=>game(true));
  $('lobby-board').addEventListener('click',()=>board()); $('board-back').addEventListener('click',()=>home());
  $('board-play').addEventListener('click',()=>game());
  $('lobby-rules').addEventListener('click',onRules); $('lobby-sound').addEventListener('click',onSound); $('lobby-motion').addEventListener('click',onMotion);
  $('board-everyone').addEventListener('click',()=>{tab='everyone';load();}); $('board-personal').addEventListener('click',()=>{tab='personal';load();});
  $('board-refresh').addEventListener('click',load); $('board-retry').addEventListener('click',load);
  root.addEventListener('keydown',event=>{ if(event.key==='Escape' && document.body.dataset.screen==='leaderboard') {event.preventDefault();home();} });
  return { home, board, preferences, get visible(){return !root.hidden;}, destroy(){controller?.abort();clearMotion();root.remove();} };
}
