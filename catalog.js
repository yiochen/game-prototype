import './catalog.css';
import catalog from './prototypes.json';
const covers = import.meta.glob('./prototypes/*/assets/cover.svg', { eager: true, query: '?url', import: 'default' });
const list = document.getElementById('prototypes');
for (const prototype of [...catalog].sort((a, b) => Number(Boolean(b.new)) - Number(Boolean(a.new)))) {
  const link = document.createElement('a');
  link.className = 'prototype';
  link.href = `./prototypes/${prototype.slug}/`;
  const art = document.createElement('div'); art.className = 'prototype-art';
  art.style.background = prototype.color || '';
  if (prototype.cover) { const img = document.createElement('img'); img.src = covers[`./prototypes/${prototype.slug}/${prototype.cover}`]; img.alt = ''; img.loading = 'lazy'; art.append(img); }
  else { const icon = document.createElement('span'); icon.className = 'prototype-icon'; icon.textContent = prototype.icon || '✦'; art.append(icon); }
  if (prototype.new) { const badge = document.createElement('span'); badge.className = 'new-badge'; badge.textContent = 'FRESHLY PLAYABLE'; art.append(badge); }
  const body = document.createElement('div'); body.className = 'prototype-body';
  const genre = document.createElement('p'); genre.className = 'genre'; genre.textContent = prototype.genre || 'Prototype';
  const title = document.createElement('h2'); title.textContent = prototype.title;
  const description = document.createElement('p'); description.textContent = prototype.description;
  const action = document.createElement('span'); action.className = 'play-link'; action.textContent = prototype.action || 'Come play ↗';
  body.append(genre, title, description, action); link.append(art, body); list.append(link);
}
