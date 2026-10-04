/**
 * What `make model` draws, and how it reaches disk: the diagrams the model produces, in order, and the draw of
 * those through a `RenderSession`.
 */
import {
  existsSync,
  lstatSync,
  mkdirSync,
  readdirSync,
  readFileSync,
  renameSync,
  rmSync,
  unlinkSync,
  writeFileSync,
} from 'node:fs';
import { basename, dirname, join } from 'node:path';

import { extractHash, renderGlobalMermaid, renderSegmentMermaid, renderSliceMermaid } from './mermaid.ts';
import { segmentModel, type Model } from './model.ts';
import { BrowserError, reasonOf, type RenderSession } from './render-session.ts';
import {
  MODEL_MERMAID,
  MODEL_SVG,
  README,
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

/** Whether a CI marker is set, to a value; under one every diagram is drawn, and the closing line says so. */
export const underCiMarker = (): boolean => CI_MARKERS.some((name) => (process.env[name] ?? '') !== '');

/** What is at a path, asked of the entry itself: a link is a link, never the file or directory it names. */
function kindAt(path: string): 'absent' | 'directory' | 'file' | 'other' {
  try {
    const stat = lstatSync(join(ROOT, path));
    return stat.isDirectory() ? 'directory' : stat.isFile() ? 'file' : 'other';
  } catch {
    return 'absent';
  }
}

/**
 * Removes the entry at `path` as itself: a real directory with what is in it, anything else (a link, a file, a FIFO)
 * by unlinking it, so what a link names is never touched. Says `removed <path>` unless `quiet`.
 */
export function removeAsItself(path: string, quiet = false): void {
  const kind = kindAt(path);
  if (kind === 'absent') return;
  const absolute = join(ROOT, path);
  if (kind === 'directory') rmSync(absolute, { recursive: true });
  else unlinkSync(absolute);
  if (!quiet) console.log(`  removed ${path.replaceAll('\\', '/')}`);
}

/** A name the run is about to read or write must be a regular file or nothing: anything else is removed first. */
export function clearIrregular(path: string): void {
  const kind = kindAt(path);
  if (kind === 'directory' || kind === 'other') removeAsItself(path);
}

const sourceStamp = (diagram: Diagram): string => {
  const hash = extractHash(diagram.source);
  if (hash === undefined) {
    throw new Error(`render: generated Mermaid for ${diagram.svg} carried no hash — mermaid.ts should always stamp one`);
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
  if (underCiMarker() || kindAt(diagram.svg) !== 'file') return false;
  let text: string;
  try {
    text = readFileSync(join(ROOT, diagram.svg), 'utf8');
  } catch {
    return false;
  }
  const [first, second] = text.split('\n', 2);
  return first === sourceStamp(diagram) && second === rendererStamp(key) && text.trimEnd().endsWith('</svg>');
}

/**
 * What the model no longer produces, in `segments/` and `slices/`, is removed by name — never what it still does.
 * Both must be real directories: a link or anything else there is removed as itself and a directory made, so nothing
 * a link names is listed, emptied or descended. A name the model does produce that is not a regular file is removed
 * too, to be drawn or written afresh. Each removal is said.
 */
export function removeOrphans(diagrams: readonly Diagram[]): void {
  const slashed = (path: string): string => path.replaceAll('\\', '/');
  for (const dir of [SEGMENT_DIR, SLICE_DIR]) {
    try {
      if (kindAt(dir) !== 'directory') removeAsItself(dir);
      mkdirSync(join(ROOT, dir), { recursive: true });
      const produced = new Set(
        diagrams
          .flatMap((diagram) => [diagram.mmd, diagram.svg])
          .filter((path) => slashed(dirname(path)) === slashed(dir))
          .map((path) => basename(path)),
      );
      for (const entry of readdirSync(join(ROOT, dir)).sort()) {
        if (!produced.has(entry)) removeAsItself(join(dir, entry));
      }
    } catch (error) {
      throw new Error(`render: could not clear ${dir}: ${reasonOf(error)}`);
    }
  }
  for (const diagram of diagrams) {
    for (const path of [diagram.mmd, diagram.svg]) clearIrregular(path);
  }
}

/** Counts the temporaries this process has named, so no two writes in one run share one. */
let temporaries = 0;

/**
 * Where a file is written before it is renamed: `.tmp-<process id>-<n>`, so two runs in one tree never write the same
 * temporary and a long file name never makes a temporary too long to open. `removeOrphans` takes any `.tmp-` entry,
 * whichever process left it.
 */
export function temporaryPath(): string {
  temporaries += 1;
  return join(ROOT, SLICE_DIR, `.tmp-${String(process.pid)}-${String(temporaries)}`);
}

/**
 * A file reaches its name finished, or not at all: written whole beside it and renamed over it, so nothing that
 * reads the output (the gate, a browser, `git`) ever sees half of one. The temporary sits in `slices/`, which
 * is already ignored and on the same filesystem as every output; its name — a leading dot, the process id, a count — is one the model never produces, so `removeOrphans` takes one a killed run left behind.
 */
function writeFinished(path: string, bytes: string | Uint8Array): void {
  const temporary = temporaryPath();
  try {
    clearIrregular(path);
    mkdirSync(dirname(temporary), { recursive: true });
    writeFileSync(temporary, bytes, { flag: 'wx' });
    renameSync(temporary, join(ROOT, path));
  } catch (error) {
    try {
      rmSync(temporary, { force: true });
    } catch {
      // The write's own failure is the one to say; a temporary that will not go is taken by the next run.
    }
    throw new Error(`render: could not write ${path}: ${reasonOf(error)}`);
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
    // The browser that would not start is one failure, shared by the window: reported as itself, no diagram blamed.
    const browser = settled.find((result) => result.status === 'rejected' && result.reason instanceof BrowserError);
    if (browser !== undefined) throw (browser as PromiseRejectedResult).reason;
    batch.forEach((diagram, index) => {
      const result = settled[index] as PromiseSettledResult<Uint8Array>;
      if (result.status === 'rejected') {
        const reason = reasonOf(result.reason);
        failed.push(`${diagram.svg}: ${reason}`);
        return;
      }
      const svg = Buffer.from(result.value).toString('utf8');
      writeFinished(diagram.svg, `${sourceStamp(diagram)}\n${rendererStamp(key)}\n${svg}`);
    });
  }
  if (failed.length > 0) {
    throw new Error(`render: could not draw ${failed.join('\nrender: could not draw ')}`);
  }
}

/** The raster copy of the whole timeline, drawn on every run that asks, in the same session, and renamed into place. */
export async function drawPng(source: string, session: RenderSession, path: string): Promise<void> {
  let bytes: Uint8Array;
  try {
    bytes = await session.draw(source, 'png');
  } catch (error) {
    if (error instanceof BrowserError) throw error;
    throw new Error(`render: could not draw ${path}: ${reasonOf(error)}`);
  }
  writeFinished(path, bytes);
}

export function readSvg(diagram: Diagram): string {
  try {
    return readFileSync(join(ROOT, diagram.svg), 'utf8');
  } catch (error) {
    throw new Error(`render: could not read ${diagram.svg}: ${reasonOf(error)}`);
  }
}

/**
 * Writes a text output only where its bytes differ from the file on disk, and says so: one `wrote <label>` line for
 * a file written and none for a file left, so nothing downstream (`git`, a watcher, a browser tab) is disturbed by
 * a rewrite of what was already right. Returns whether it wrote.
 */
export function writeIfDifferent(path: string, contents: string, label: string = path): boolean {
  const absolute = join(ROOT, path);
  try {
    // The README is the project's own and may be a link of its own making: it is read and written as it was.
    if (path !== README) clearIrregular(path);
    const present = path === README ? existsSync(absolute) : kindAt(path) === 'file';
    if (present && readFileSync(absolute, 'utf8') === contents) return false;
    mkdirSync(dirname(absolute), { recursive: true });
    writeFileSync(absolute, contents, 'utf8');
  } catch (error) {
    throw new Error(`render: could not write ${label}: ${reasonOf(error)}`);
  }
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
  /** A CI marker is set: everything was drawn for that reason, and the line says so. */
  underCi?: boolean;
}

export function closingLine(report: Report, pagePath: string): string {
  const noun = (count: number, word: string): string => `${String(count)} ${word}${count === 1 ? '' : 's'}`;
  const counts = `${noun(report.slices, 'slice')}, ${String(report.drawn)} of ${noun(report.diagrams, 'diagram')} drawn, ${String(report.unchanged)} unchanged`;
  const browser = report.sessionOpened ? '' : '; no browser started';
  const ci = report.underCi === true ? '; everything was drawn because a CI marker is set' : '';
  return `model: ${counts}${browser}${ci}. Open ${pagePath} to browse it.`;
}
