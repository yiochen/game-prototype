import React, { useState } from 'react';
import './feedback.css';

const STORAGE_KEY = 'sushi-loop-wireframe-feedback:v1';
const BRANCH = 'codex/sushi-loop-wireframes';
const MAX_LENGTH = 1500;
const emptyStore = () => ({ version: 1, comments: [], drafts: {} });
// React remounts this component when the selected story changes. Keep tab-only
// edits here so blocked browser storage cannot discard feedback on navigation.
let tabStore;
let tabWriteFailed = false;

function loadStore() {
  if (tabWriteFailed && tabStore) return {
    store: tabStore,
    warning: 'Browser storage is unavailable. Your feedback is retained in this tab; export or hand it off before closing.',
  };
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      tabStore = emptyStore();
      return { store: tabStore, warning: '' };
    }
    const parsed = JSON.parse(raw);
    if (parsed?.version !== 1 || !Array.isArray(parsed.comments)) throw new Error('Unknown feedback format');
    const comments = parsed.comments.filter((comment) => comment && typeof comment.id === 'string' && typeof comment.storyId === 'string' && typeof comment.storyTitle === 'string' && typeof comment.text === 'string' && !Number.isNaN(Date.parse(comment.createdAt))).map((comment) => ({ ...comment, text: comment.text.slice(0, MAX_LENGTH), persisted: true }));
    const drafts = Object.fromEntries(Object.entries(parsed.drafts || {}).filter(([, text]) => typeof text === 'string').map(([id, text]) => [id, text.slice(0, MAX_LENGTH)]));
    tabStore = { version: 1, comments, drafts };
    return { store: tabStore, warning: '' };
  } catch {
    tabStore ||= emptyStore();
    return { store: tabStore, warning: 'Browser storage could not be read. New feedback will stay in this tab unless saving becomes available.' };
  }
}

function saveStore(store) {
  tabStore = store;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
    tabWriteFailed = false;
    return true;
  } catch {
    tabWriteFailed = true;
    return false;
  }
}

function storyUrl(storyId) {
  const url = new URL(window.location.href);
  url.hash = storyId;
  return url.href;
}

function githubLink(comment) {
  const body = [
    '## Wireframe feedback',
    '',
    `**Example:** ${comment.storyTitle}`,
    `**Story ID:** \`${comment.storyId}\``,
    `**Preview:** ${storyUrl(comment.storyId)}`,
    `**Branch:** \`${BRANCH}\``,
    '',
    '## Requested change',
    '',
    comment.text,
    '',
    'Please apply this feedback to the shared component that renders this example and update its other affected UI states.',
    '',
    'This issue was prepared from the wireframe review form. The design remains a review draft.',
  ].join('\n');
  const url = new URL('https://github.com/yiochen/game-prototype/issues/new');
  url.searchParams.set('title', `[Sushi Loop wireframe] ${comment.storyTitle}`);
  url.searchParams.set('body', body);
  url.searchParams.set('labels', 'wireframe-feedback');
  return url.href;
}

function exportMarkdown(comments) {
  return [
    '# Sushi Loop wireframe feedback',
    '',
    `Branch: \`${BRANCH}\``,
    '',
    'This feedback has not been automatically sent to GitHub or Codex.',
    '',
    ...comments.flatMap((comment, index) => [
      `## ${index + 1}. ${comment.storyTitle}`,
      '',
      `Story: \`${comment.storyId}\``,
      `Saved: ${comment.createdAt}`,
      `Storage: ${comment.persisted ? 'Saved on this device' : 'Only in this tab; device storage was unavailable'}`,
      `Preview: ${storyUrl(comment.storyId)}`,
      '',
      comment.text,
      '',
      'Apply the requested change to the shared component and review other affected states.',
      '',
      '---',
      '',
    ]),
  ].join('\n');
}

function downloadMarkdown(comments) {
  const url = URL.createObjectURL(new Blob([exportMarkdown(comments)], { type: 'text/markdown;charset=utf-8' }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'sushi-loop-wireframe-feedback.md';
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function dateLabel(timestamp) {
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(timestamp));
}

export function Feedback({ story }) {
  const [initial] = useState(loadStore);
  const [store, setStore] = useState(initial.store);
  const [draft, setDraft] = useState(initial.store.drafts[story.id] || '');
  const [message, setMessage] = useState('');
  const [warning, setWarning] = useState(initial.warning);
  const comments = store.comments.filter((comment) => comment.storyId === story.id);
  const textareaId = `feedback-draft-${story.id}`;
  const helperId = `${textareaId}-help`;
  const statusId = `${textareaId}-status`;

  function updateDraft(value) {
    const text = value.slice(0, MAX_LENGTH);
    setDraft(text);
    const next = { ...store, drafts: { ...store.drafts, [story.id]: text } };
    const saved = saveStore(next);
    setStore(next);
    if (!saved) setWarning('Your draft is only in this tab. Browser storage is unavailable; export saved comments before closing.');
    else if (warning) setWarning('');
  }

  function addComment(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const comment = {
      id: window.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      storyId: story.id, storyTitle: story.title, text,
      createdAt: new Date().toISOString(), persisted: true,
    };
    const next = { ...store, comments: [...store.comments, comment], drafts: { ...store.drafts, [story.id]: '' } };
    const saved = saveStore(next);
    if (!saved) comment.persisted = false;
    setStore(next);
    setDraft('');
    setWarning(saved ? '' : 'This comment is only in this tab. Browser storage is unavailable; use Export all or the GitHub form before closing.');
    setMessage(saved ? 'Comment added. Saved on this device.' : 'Comment added to this tab. It has not been saved on this device.');
  }

  function removeComment(id) {
    const next = { ...store, comments: store.comments.filter((comment) => comment.id !== id) };
    const saved = saveStore(next);
    setStore(next);
    setWarning(saved ? '' : 'The removal could not be saved on this device. The previous comment may return after a reload.');
    setMessage(saved ? 'Comment removed from this device.' : 'Comment removed from this tab only.');
  }

  function exportAll() {
    downloadMarkdown(store.comments);
    setMessage(`Exported ${store.comments.length} ${store.comments.length === 1 ? 'comment' : 'comments'} as Markdown. Nothing was sent automatically.`);
  }

  async function copyAll() {
    try {
      if (!navigator.clipboard?.writeText) throw new Error('Clipboard unavailable');
      await navigator.clipboard.writeText(exportMarkdown(store.comments));
      setMessage('All feedback copied. Paste it into your message to Codex.');
    } catch {
      downloadMarkdown(store.comments);
      setMessage('Clipboard access was unavailable. Downloaded your feedback as Markdown instead.');
    }
  }

  return <section className="feedback-section" aria-labelledby={`feedback-heading-${story.id}`}>
    <div className="feedback-heading"><h3 id={`feedback-heading-${story.id}`}>Review this example</h3><span>{comments.length} {comments.length === 1 ? 'comment' : 'comments'}</span></div>
    <p className="feedback-scope">{story.title}</p>
    <form onSubmit={addComment} className="feedback-form">
      <label htmlFor={textareaId}>What would you change?</label>
      <textarea id={textareaId} value={draft} onChange={(event) => updateDraft(event.target.value)} rows={4} maxLength={MAX_LENGTH} aria-describedby={`${helperId} ${statusId}`} placeholder="Describe the placement, behavior, transition, or wording you want to change…" />
      <div className="feedback-form-footer"><span>{draft.length} / {MAX_LENGTH}</span><button type="submit" disabled={!draft.trim()}>Add comment</button></div>
    </form>
    <p id={helperId} className="feedback-helper">{warning ? 'Browser storage is unavailable. Export or hand off feedback before closing this tab.' : 'Saved on this device. Comments and drafts stay here until you export or hand them off.'}</p>
    <div id={statusId} className={`feedback-status ${warning ? 'has-warning' : ''}`} role="status" aria-live="polite">{warning && <span>{warning}</span>}{message && <span>{message}</span>}</div>
    {comments.length ? <ol className="feedback-comments">{comments.map((comment) => <li key={comment.id}>
      <div className="feedback-comment-meta"><span>{comment.persisted ? 'Saved on this device' : 'Only in this tab'}</span><time dateTime={comment.createdAt}>{dateLabel(comment.createdAt)}</time></div>
      <p className="feedback-comment-text">{comment.text}</p>
      <div className="feedback-comment-actions"><a href={githubLink(comment)} target="_blank" rel="noopener noreferrer">Open GitHub feedback form ↗</a><button type="button" onClick={() => removeComment(comment.id)} aria-label={`Remove comment saved ${dateLabel(comment.createdAt)}`}>Remove</button></div>
    </li>)}</ol> : <p className="feedback-empty">No comments on this example yet.</p>}
    <p className="feedback-handoff">The GitHub link opens a review form; you still need to submit it. <strong>Submit the GitHub issue, then ask Codex to apply it.</strong></p>
    <div className="feedback-export"><button type="button" onClick={exportAll} disabled={!store.comments.length}>Export all .md</button><button type="button" onClick={copyAll} disabled={!store.comments.length}>Copy all feedback</button></div>
    <p className="feedback-export-helper">{store.comments.length} {store.comments.length === 1 ? 'comment' : 'comments'} across all examples. You can also attach the exported file or paste copied feedback into this chat.</p>
  </section>;
}
