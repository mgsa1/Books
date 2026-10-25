// Prints the narration as plain text, one scene per block, for a TTS pass.
// Usage: npm run narration > narration.txt
import {readFileSync} from 'node:fs';
const src = readFileSync(new URL('../src/script.ts', import.meta.url), 'utf8');
const blocks = [...src.matchAll(/(\w+): \{\s*seconds: (\d+),\s*narration: \[([\s\S]*?)\]/g)];
for (const [, id, seconds, body] of blocks) {
  const lines = [...body.matchAll(/'((?:[^'\\]|\\.)*)'/g)].map((m) => m[1]);
  console.log(`# ${id} (${seconds}s)\n${lines.join('\n')}\n`);
}
