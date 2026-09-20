import './catalog.css';
import catalog from './prototypes.json';
const list = document.getElementById('prototypes');
for (const prototype of catalog) {
  const link = document.createElement('a');
  link.className = 'prototype';
  link.href = `./prototypes/${prototype.slug}/`;
  const title = document.createElement('h2'); title.textContent = prototype.title;
  const description = document.createElement('p'); description.textContent = prototype.description;
  const action = document.createElement('span'); action.textContent = 'Play →';
  link.append(title, description, action); list.append(link);
}
