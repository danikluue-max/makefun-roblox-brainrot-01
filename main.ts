// Brainrot Bay — entry for make.fun's "Make the best AI Roblox brainrot game"
// (roblox-brainrot-01). Node 22, standard library only.
//
// The game itself is the Rojo project in this directory: `rojo build
// default.project.json --output game.rbxl` produces the binary place, and this
// program hands it in. It copies the place, the Luau sources, the screenshots
// and PLAY.json from beside this file into /output, then writes
// /output/dossier.json — the summary the judge reads — with the vendored
// make.fun library (vendor/makefun-roblox.ts, the kit's copy, unchanged).
//
// The game: walk the conveyor, buy an original brainrot, carry it to your
// base, earn $/sec, steal from rivals, lock your base, rebirth, and outrun
// the tsunami. Put PNG or JPEG screenshots in screenshots/ (the first by name
// is the cover, and one of them is the thumbnail you upload for the game on
// Roblox) and fill in PLAY.json with your published place.
//
// Output names: every name under /output must start with a letter, a digit
// or _ and hold only letters, digits, . _ and -. The grader fails an entry
// whose output holds any other name, so a file such as .gitkeep or .DS_Store
// copied in fails it. src/ and screenshots/ are therefore copied without any
// name that starts with a dot, at any depth.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, cpSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { basename, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { buildDossier } from './vendor/makefun-roblox.ts';

const here = fileURLToPath(new URL('.', import.meta.url));
const out = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

/** Copy filter for cpSync: skip every file and directory whose name starts
 *  with a dot (.gitkeep, .DS_Store, .git). */
function notDotted(path: string): boolean {
  return !basename(path).startsWith('.');
}

/** Copy one whole tree (src/, screenshots/) under /output. */
function copyTree(name: string): void {
  const srcDir = join(here, name);
  if (!existsSync(srcDir)) return;
  cpSync(srcDir, join(out, name), { recursive: true, filter: notDotted });
}

mkdirSync(out, { recursive: true });
copyFileSync(join(here, 'game.rbxl'), join(out, 'game.rbxl'));
copyFileSync(join(here, 'PLAY.json'), join(out, 'PLAY.json'));
copyTree('src');
copyTree('screenshots');

// The scorer's own caps (reference/gate.json): only text_max_bytes shapes the
// bytes; the others refuse an entry the scorer would refuse — more than 4
// screenshots or one over 256 KiB; a place of more than 500000 instances,
// whose scripts' sources come to over 8 MiB or whose scripts' paths come to
// over 1048576 characters, in all.
writeFileSync(
  join(out, 'dossier.json'),
  buildDossier(out, {
    text_max_bytes: 65536,
    screenshots: { max: 4, max_bytes: 262144 },
    max_instances: 500000,
    scripts_max_source_bytes: 8388608,
    scripts_max_path_chars: 1048576,
  }),
);
