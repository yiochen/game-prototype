import { compareScores, replayRun, scoreOf, SCORE_VERSION } from './score-rules.js';
const KEY = 'cloudtop-guestbook-v1';
export function createGuestbook(storage) {
  let persistent = true;
  let data = { runs: [], active: null, name: '', sound: false, reduced: null };
  try {
    storage ??= globalThis.localStorage;
    const saved = JSON.parse(storage.getItem(KEY));
    if (saved && Array.isArray(saved.runs)) {
      data = { ...data, name: typeof saved.name === 'string' ? saved.name.slice(0,20) : '', sound: saved.sound === true, reduced: typeof saved.reduced === 'boolean' ? saved.reduced : null };
      for (const run of saved.runs.slice(0,50)) {
        try {
          if (run.version !== SCORE_VERSION || typeof run.id !== 'string' || !Number.isFinite(Date.parse(run.createdAt))) continue;
          data.runs.push({ ...run, ...scoreOf(replayRun(run.seed, run.moves)) });
        } catch { /* A damaged record must not prevent a new stay. */ }
      }
      if (saved.active?.version === SCORE_VERSION) {
        try { replayRun(saved.active.seed, saved.active.moves, false); data.active = saved.active; } catch { /* Discard incompatible saves. */ }
      }
    }
  } catch { persistent = false; /* Private browsing and unavailable storage still allow play. */ }
  function persist() { try { storage.setItem(KEY, JSON.stringify(data)); persistent = true; return true; } catch { persistent = false; return false; } }
  return {
    get persistent() { return persistent; },
    get data() { return data; },
    preference(key, value) { data[key] = value; persist(); },
    saveActive(run) { data.active = { ...run, version: SCORE_VERSION }; return persist(); },
    finish(run, state) {
      let record = data.runs.find(r => r.id === run.id);
      if (!record) { record = { ...run, version: SCORE_VERSION, ...scoreOf(state), createdAt: new Date().toISOString() }; data.runs.push(record); }
      data.runs.sort(compareScores); data.runs = data.runs.slice(0,50); data.active = null;
      return { record, saved: persist() };
    },
    markShared(id, name, serverId) {
      data.name = name;
      const run = data.runs.find(r => r.id === id); if (run) { run.shared = true; run.serverId = serverId; run.name = name; }
      persist();
    },
  };
}
