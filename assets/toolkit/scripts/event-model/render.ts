/**
 * Regenerates every artifact the model produces: Mermaid source, SVGs, and the browsable page.
 *
 * Run with: make model            (add PNG=1 for a raster copy)
 *
 * Mermaid CLI is fetched on demand into `scripts/event-model/.mermaid-cli/` rather than being a
 * devDependency, because it pulls a headless browser: making every `npm install` in the project pay for
 * that, so that one person can regenerate a diagram, is a poor trade (`render-session.ts` owns that, and
 * the one browser a run draws through). `render-plan.ts` owns which diagrams there are and how they reach disk.
 * `make check-model` needs no browser at all, which is why *it* is the gate that runs in CI.
 */
import { readFileSync, rmSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

import { drawDiagrams, drawPng, isCurrent, planDiagrams, readSvg, removeOrphans, type Diagram } from './render-plan.ts';
import { patchInstalledMermaid } from './patch-mermaid-swimlanes.ts';
import { CLI_PREFIX, installRenderer, lazySession, rendererKey } from './render-session.ts';
import { renderPage } from './page.ts';
import { renderReadmeSection, withReadmeSection } from './readme.ts';
import type { Model } from './model.ts';
import {
  loadModel,
  loadServices,
  MODEL_HTML,
  MODEL_MERMAID,
  MODEL_PNG,
  MODEL_SOURCE,
  MODEL_SVG,
  README,
  ROOT,
  SEGMENT_DIR,
  SLICE_DIR,
} from './workspace.ts';

function write(relativePath: string, contents: string): void {
  const absolute = join(ROOT, relativePath);
  writeFileSync(absolute, contents, 'utf8');
  console.log(`  wrote ${relativePath}`);
}

/**
 * Refreshes the README's event-model block, if it has one.
 *
 * Silent when the README carries no markers: a project that does not want the section deletes them, and a
 * generator that nagged about it would be a generator people stop running. Runs for an empty model too —
 * "no slices yet" is a true and useful thing for a README to say.
 */
function updateReadme(model: Model): void {
  const path = join(ROOT, README);
  let current: string;
  try {
    current = readFileSync(path, 'utf8');
  } catch {
    return; // No README at all. Not this script's business to create one.
  }

  const updated = withReadmeSection(current, renderReadmeSection(model));
  if (updated === undefined || updated === current) return;

  writeFileSync(path, updated, 'utf8');
  console.log(`  wrote ${README} (event-model block)`);
}

async function main(): Promise<void> {
  const model = loadModel();
  const wantPng = process.env['PNG'] === '1' || process.argv.includes('--png');

  if (model.slices.length === 0) {
    // An empty model is the correct state for a project that has not modelled anything yet, and for this
    // template permanently. Rendering an empty diagram would be a syntax error, and inventing a
    // placeholder slice would be inventing a domain model.
    console.log(`${MODEL_SOURCE} has no slices yet — nothing to render.`);
    console.log('Model your first workflow with the `event-modeling` skill, then run this again.');
    for (const artifact of [MODEL_MERMAID, MODEL_SVG, MODEL_PNG, MODEL_HTML]) {
      rmSync(join(ROOT, artifact), { force: true });
    }
    for (const dir of [SLICE_DIR, SEGMENT_DIR]) {
      rmSync(join(ROOT, dir), { force: true, recursive: true });
    }
    updateReadme(model);
    return;
  }

  const diagrams = planDiagrams(model);
  removeOrphans(diagrams);
  for (const diagram of diagrams) write(diagram.mmd, diagram.source);

  installRenderer();
  patchInstalledMermaid(CLI_PREFIX); // before the first draw: the swimlane fix lives in the tree we own
  const key = rendererKey();
  const session = lazySession();
  try {
    await drawDiagrams(diagrams.filter((diagram) => !isCurrent(diagram, key)), session, key);
    if (wantPng) await drawPng(diagrams[0]?.source ?? '', session, MODEL_PNG);
  } finally {
    await session.close();
  }

  const pictures = <K extends number | string>(kind: string): Map<K, string> =>
    new Map(diagrams.filter((d) => d.kind === kind).map((d) => [d.ref as K, readSvg(d)] as const));
  write(
    MODEL_HTML,
    renderPage({
      model,
      globalSvg: readSvg(diagrams[0] as Diagram),
      segmentSvgs: pictures<number>('segment'),
      sliceSvgs: pictures<string>('slice'),
      sourcePath: MODEL_SOURCE,
      services: loadServices(),
    }),
  );

  updateReadme(model);

  console.log('');
  console.log(`model: ${String(model.slices.length)} slices rendered. Open ${MODEL_HTML} to browse it.`);
}

main().catch((error: unknown) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
