import { getStore, getDeployStore } from '@netlify/blobs';
import type { Context, Config } from '@netlify/functions';
import { handleLeaderboard } from '../leaderboard-service.js';
import { SCORE_VERSION } from '../score-rules.js';

export default async (request: Request, context: Context) => {
  try {
    const options = { name: `cloudtop-leaderboard-${SCORE_VERSION}`, consistency: 'strong' as const };
    // Preview scores stay separate from the live leaderboard.
    const store = context.deploy.context === 'production' ? getStore(options) : getDeployStore(options);
    return await handleLeaderboard(request, store);
  } catch {
    return Response.json({ error: 'The guestbook is taking a little break. Please try signing again.' }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  }
};
export const config: Config = {
  path: '/api/cloudtop-hotel/leaderboard',
  rateLimit: { windowLimit: 30, windowSize: 60, aggregateBy: ['ip', 'domain'] },
};
