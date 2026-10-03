/**
 * What `make model` draws, and how it reaches disk: the diagrams the model produces, in order, and the draw of
 * those through a `RenderSession`.
 */
import { existsSync, mkdirSync, readdirSync, readFileSync, renameSync, rmSync, writeFileSync } from 'node:fs';
import { basename, dirname, join } from 'node:path';

import { extractHash, renderGlobalMermaid, renderSegmentMermaid, renderSliceMermaid } from './mermaid.ts';
import { segmentModel, type Model } from './model.ts';
import type { RenderSession } from './render-session.ts';
import {
  MODEL_MERMAID,
  MODEL_SVG,
  ROOT,
  SEGMENT_DIR,
  segmentArtifact,
  SLICE_DIR,
  sliceArtifact,
} from './workspace.ts';

export interface Diagram {
  kind: 'global' | 'segment' | 'slice';
  /** A segment's 1-based index, a slice's id; what the page keys the picture by. Absent for the timeline. */
  ref?: number | string;
  /** Where the Mermaid source is written, and where the SVG goes, relative to the project root. */
  mmd: string;
  svg: string;
  /** The Mermaid the model produces now, stamped with the hash `check-model` compares. */
  source: string;
}

/** The whole timeline, then the segments, then the slices: the model's order. */
export function planDiagrams(model: Model): Diagram[] {
  return [
    { kind: 'global', mmd: MODEL_MERMAID, svg: MODEL_SVG, source: renderGlobalMermaid(model) },
    ...segmentModel(model).map((segment): Diagram => ({
      kind: 'segment',
      ref: segment.index,
      mmd: segmentArtifact(segment.index, 'mmd'),
      svg: segmentArtifact(segment.index, 'svg'),
      source: renderSegmentMermaid(model, segment.sliceIds),
    })),
    ...model.slices.map((slice): Diagram => ({
      kind: 'slice',
      ref: slice.id,
      mmd: sliceArtifact(slice.id, 'mmd'),
      svg: sliceArtifact(slice.id, 'svg'),
      source: renderSliceMermaid(model, slice.id),
    })),
  ];
}

/** At most this many pages draw at once in the one browser; each file is still written in the model's order. */
const IN_FLIGHT = 4;

/** The environment markers of a CI run; under any of them nothing is left, so the gate's picture is drawn fresh. */
const CI_MARKERS = ['CI', 'GITHUB_ACTIONS', 'GITLAB_CI'];

const sourceStamp = (diagram: Diagram): string => {
  const hash = extractHash(diagram.source);
  if (hash === undefined) {
    throw new Error(`generated Mermaid for ${diagram.svg} carried no hash — mermaid.ts should always stamp one`);
  }
  return `<!-- em-source-sha256: ${hash} -->`;
};

const rendererStamp = (key: string): string => `<!-- em-renderer-sha256: ${key} -->`;

/**
 * A diagram is left only when its SVG can be shown current: line one is the source stamp of the Mermaid the model
 * produces now (never the `.mmd` on disk), line two names this run's renderer, the file ends `</svg>`, and this
 * is not a CI run. Anything else, an absent or torn file included, is drawn.
 */
export function isCurrent(diagram: Diagram, key: string): boolean {
  if (CI_MARKERS.some((name) => (process.env[name] ?? '') !== '')) return false;
  let text: string;
  try {
    text = readFileSync(join(ROOT, diagram.svg), 'utf8');
  } catch {
    return false;
  }
  const [first, second] = text.split('\n', 2);
  return first === sourceStamp(diagram) && second === rendererStamp(key) && text.trimEnd().endsWith('</svg>');
}

/** What the model no longer produces, in `segments/` and `slices/`, is removed by name — never what it still does. */
export function removeOrphans(diagrams: readonly Diagram[]): void {
  const slashed = (path: string): string => path.replaceAll('\\', '/');
  for (const dir of [SEGMENT_DIR, SLICE_DIR]) {
    mkdirSync(join(ROOT, dir), { recursive: true });
    const produced = new Set(
      diagrams
        .flatMap((diagram) => [diagram.mmd, diagram.svg])
        .filter((path) => slashed(dirname(path)) === slashed(dir))
        .map((path) => basename(path)),
    );
    for (const entry of readdirSync(join(ROOT, dir))) {
      if (!produced.has(entry)) rmSync(join(ROOT, dir, entry), { force: true, recursive: true });
    }
  }
}

/**
 * A file reaches its name finished, or not at all: written whole beside it and renamed over it, so nothing that
 * reads the output (the gate, a browser, `git`) ever sees half of one. The temporary sits in `slices/`, which
 * is already ignored and on the same filesystem as every output; its name — a leading dot, a kind, the file's
 * own name — is one the model never produces, so `removeOrphans` takes one a killed run left behind.
 */
function writeFinished(kind: Diagram['kind'], path: string, bytes: string | Uint8Array): void {
  const temporary = join(ROOT, SLICE_DIR, `.tmp-${kind}-${basename(path)}`);
  try {
    mkdirSync(dirname(temporary), { recursive: true });
    writeFileSync(temporary, bytes);
    renameSync(temporary, join(ROOT, path));
  } catch (error) {
    rmSync(temporary, { force: true });
    throw error;
  }
  console.log(`  wrote ${path}`);
}

/**
 * Draws the diagrams through the session, up to four at a time, and writes each SVG as it is drawn. When a
 * draw fails no further one is started; the ones in flight finish and are written like any other; then the
 * run says which diagrams failed, and fails.
 */
export async function drawDiagrams(diagrams: readonly Diagram[], session: RenderSession, key: string): Promise<void> {
  const failed: string[] = [];
  for (let start = 0; start < diagrams.length && failed.length === 0; start += IN_FLIGHT) {
    const batch = diagrams.slice(start, start + IN_FLIGHT);
    const settled = await Promise.allSettled(batch.map((diagram) => session.draw(diagram.source, 'svg')));
    batch.forEach((diagram, index) => {
      const result = settled[index] as PromiseSettledResult<Uint8Array>;
      if (result.status === 'rejected') {
        const reason = result.reason instanceof Error ? result.reason.message : String(result.reason);
        failed.push(`${diagram.svg}: ${reason}`);
        return;
      }
      const svg = Buffer.from(result.value).toString('utf8');
      writeFinished(diagram.kind, diagram.svg, `${sourceStamp(diagram)}\n${rendererStamp(key)}\n${svg}`);
    });
  }
  if (failed.length > 0) {
    throw new Error(`render: could not draw ${failed.join('\nrender: could not draw ')}`);
  }
}

/** The raster copy of the whole timeline, drawn on every run that asks, in the same session, and renamed into place. */
export async function drawPng(source: string, session: RenderSession, path: string): Promise<void> {
  writeFinished('global', path, await session.draw(source, 'png'));
}

export function readSvg(diagram: Diagram): string {
  return readFileSync(join(ROOT, diagram.svg), 'utf8');
}

/**
 * Writes a text output only where its bytes differ from the file on disk, and says so: one `wrote <label>` line for
 * a file written and none for a file left, so nothing downstream (`git`, a watcher, a browser tab) is disturbed by
 * a rewrite of what was already right. Returns whether it wrote.
 */
export function writeIfDifferent(path: string, contents: string, label: string = path): boolean {
  const absolute = join(ROOT, path);
  if (existsSync(absolute) && readFileSync(absolute, 'utf8') === contents) return false;
  mkdirSync(dirname(absolute), { recursive: true });
  writeFileSync(absolute, contents, 'utf8');
  console.log(`  wrote ${label}`);
  return true;
}

/** What a run did, from which its closing line is written. */
export interface Report {
  slices: number;
  diagrams: number;
  drawn: number;
  unchanged: number;
  sessionOpened: boolean;
}

export function closingLine(report: Report, pagePath: string): string {
  const counts = `${String(report.slices)} slices, ${String(report.drawn)} of ${String(report.diagrams)} diagrams drawn, ${String(report.unchanged)} unchanged`;
  const browser = report.sessionOpened ? '' : '; no browser started';
  return `model: ${counts}${browser}. Open ${pagePath} to browse it.`;
}
