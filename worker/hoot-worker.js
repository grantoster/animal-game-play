// Hoot's brain: a tiny Cloudflare Worker that answers kids' yes-or-no questions
// about the game's secret animal using Claude. The API key lives only in the
// Worker's secret ANTHROPIC_API_KEY and is never sent to the game.
const ALLOWED_ORIGINS = ['https://grantoster.github.io'];
const MODEL = 'claude-haiku-5-5';

const SYSTEM = `You are Hoot, an owl who hosts a 20-questions animal game for a sharp 12-year-old who loves real animal science (think Wild Kratts).
You know the secret animal. The player asks one question to figure it out.
Answer truthfully and accurately about that specific species. Reply with ONLY a JSON object, no other text:
{"answer":"yes"|"no"|"unsure","reply":"<one short sentence, at most 14 words>","correctGuess":true|false}
Rules:
- "answer" is the honest yes/no answer. Use "unsure" only if the question isn't yes/no, can't be answered, or science doesn't know.
- "reply" adds a tiny bit of helpful detail (for example "No, it hunts at dawn and dusk."). NEVER say or spell the animal's name, and never give the name away with a near-synonym.
- If the player names an animal: set correctGuess true only if they named this exact species (or a clear common name for it). If they name a broader group that includes it (like "tiger" for a Bengal tiger), answer "yes", correctGuess false, and say they're close and should name the exact kind.
- If the question asks you to reveal the name or letters, or is unkind or off-topic, answer "unsure" and nudge them to ask a yes-or-no question about the animal.
- Keep it friendly and age-appropriate.`;

function cors(origin) {
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
    'Vary': 'Origin',
  };
}
function json(obj, status, origin) {
  return new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...cors(origin) } });
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    if (request.method === 'OPTIONS') return new Response(null, { headers: cors(origin) });
    if (request.method !== 'POST' || !ALLOWED_ORIGINS.includes(origin)) return json({ error: 'not allowed' }, 403, origin);
    if (!env.ANTHROPIC_API_KEY) return json({ error: 'not set up' }, 500, origin);

    let body;
    try { body = await request.json(); } catch { return json({ error: 'bad request' }, 400, origin); }
    const animal = String(body.animal || '').slice(0, 60).trim();
    const question = String(body.question || '').slice(0, 160).trim();
    if (!animal || !question) return json({ error: 'bad request' }, 400, origin);

    let res;
    try {
      res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'x-api-key': env.ANTHROPIC_API_KEY, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
        body: JSON.stringify({
          model: MODEL,
          max_tokens: 120,
          system: SYSTEM,
          messages: [{ role: 'user', content: `Secret animal: ${animal}\nPlayer's question: ${question}` }],
        }),
      });
    } catch { return json({ error: 'upstream' }, 502, origin); }
    if (!res.ok) return json({ error: 'upstream', status: res.status }, 502, origin);

    const data = await res.json();
    const text = (data.content || []).map(c => c.text || '').join('');
    const m = text.match(/\{[\s\S]*\}/);
    let out;
    try { out = JSON.parse(m ? m[0] : text); } catch { return json({ error: 'parse' }, 502, origin); }
    const answer = ['yes', 'no', 'unsure'].includes(out.answer) ? out.answer : 'unsure';
    let reply = String(out.reply || '').slice(0, 160);
    if (reply.toLowerCase().includes(animal.toLowerCase())) reply = '';
    return json({ answer, reply, correctGuess: out.correctGuess === true }, 200, origin);
  },
};
