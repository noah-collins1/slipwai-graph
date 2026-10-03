/**
 * What `make model` draws, and how it reaches disk: the diagrams the model produces, in order, and the draw of
 * those through a `RenderSession`.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

import { extractHash, renderGlobalMermaid, renderSegmentMermaid, renderSliceMermaid } from './mermaid.ts';
import { segmentModel, type Model } from './model.ts';
import type { RenderSession } from './render-session.ts';
import {
  MODEL_MERMAID,
  MODEL_SVG,
  ROOT,
  segmentArtifact,
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

/**
 * The source stamp `check-model` reads: the SVG's first line, carrying the hash of the Mermaid it was drawn
 * from. It is what lets a diagram be told current from stale without launching a browser.
 */
function stamped(diagram: Diagram, svg: Uint8Array): string {
  const hash = extractHash(diagram.source);
  if (hash === undefined) {
    throw new Error(`generated Mermaid for ${diagram.svg} carried no hash — mermaid.ts should always stamp one`);
  }
  return `<!-- em-source-sha256: ${hash} -->\n${Buffer.from(svg).toString('utf8')}`;
}

/** Draws the diagrams through the session, up to four at a time, and writes each SVG as it is drawn. */
export async function drawDiagrams(diagrams: readonly Diagram[], session: RenderSession): Promise<void> {
  for (let start = 0; start < diagrams.length; start += IN_FLIGHT) {
    const batch = diagrams.slice(start, start + IN_FLIGHT);
    const drawn = await Promise.all(batch.map((diagram) => session.draw(diagram.source, 'svg')));
    batch.forEach((diagram, index) => {
      writeFileSync(join(ROOT, diagram.svg), stamped(diagram, drawn[index] as Uint8Array), 'utf8');
      console.log(`  wrote ${diagram.svg}`);
    });
  }
}

/** The raster copy of the whole timeline, drawn through the same session when asked for. */
export async function drawPng(source: string, session: RenderSession, path: string): Promise<void> {
  writeFileSync(join(ROOT, path), await session.draw(source, 'png'));
  console.log(`  wrote ${path}`);
}

export function readSvg(diagram: Diagram): string {
  return readFileSync(join(ROOT, diagram.svg), 'utf8');
}
