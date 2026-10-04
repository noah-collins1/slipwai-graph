/**
 * The renderer, installed once and used through one browser.
 *
 * mermaid-cli is fetched on demand into `scripts/event-model/.mermaid-cli/` rather than being a devDependency,
 * because it pulls a headless browser: making every `npm install` in the project pay for that, so that one
 * person can regenerate a diagram, is a poor trade. The local prefix exists so the swimlane patch
 * (mermaid-js/mermaid#7986, until mermaid-cli ships it) can run against a tree we own.
 *
 * A session is one browser for every diagram a run draws. It imports mermaid-cli's own `renderMermaid` and
 * `puppeteer` from the prefix the patcher patched, and never spawns `mmdc`: a process per diagram is a
 * browser per diagram, which is what this replaces.
 */
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

/**
 * Pinned. An unpinned renderer means the committed SVG changes whenever upstream does, and every diff
 * then contains rendering churn nobody authored.
 */
const MERMAID_CLI = '@mermaid-js/mermaid-cli@11.16.0';

/** Wide enough that a dozen slices stay legible; Mermaid scales the viewBox to fit. */
const WIDTH = 2400;
/** What `mmdc --width 2400` passes besides the width, so a drawn SVG's bytes are what `mmdc` wrote. */
const DRAW_OPTIONS = { viewport: { width: WIDTH, height: 600, deviceScaleFactor: 1 }, backgroundColor: 'white' };

export const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
export const CLI_PREFIX = join(SCRIPT_DIR, '.mermaid-cli');

/**
 * Escape hatch for hosts where Puppeteer's download does not exist — Google ships no Chrome for
 * linux/arm64, so `npx mmdc` fails outright on ARM sandboxes and containers. Point this at a Puppeteer
 * JSON config naming an `executablePath` (Playwright's arm64 Chromium works) plus whatever the container
 * needs, typically `"args": ["--no-sandbox", "--disable-dev-shm-usage"]`. Unset, rendering is unchanged.
 */
export function puppeteerConfigPath(): string | undefined {
  const path = process.env['MERMAID_PUPPETEER_CONFIG'];
  return path === undefined || path === '' ? undefined : path;
}

/** What went wrong, in the words a person reads: an error's message, or whatever else was thrown, as text. */
export function reasonOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * The browser could not be started, or its configuration could not be read. It carries the whole line to print and
 * is the one failure every diagram in flight shares, so it is reported once, as itself, and never as a diagram's.
 */
export class BrowserError extends Error {}

/**
 * The Puppeteer config as the run reads it, once: the bytes the renderer key covers are the bytes the browser is
 * launched with, whatever happens to the file after. Absent where `MERMAID_PUPPETEER_CONFIG` is unset. A path that
 * cannot be read is named with the variable that gave it.
 */
export interface PuppeteerConfig {
  path: string;
  bytes: Buffer;
}

export function readPuppeteerConfig(): PuppeteerConfig | undefined {
  const path = puppeteerConfigPath();
  if (path === undefined) return undefined;
  try {
    return { path, bytes: readFileSync(path) };
  } catch (error) {
    throw new BrowserError(`render: could not read MERMAID_PUPPETEER_CONFIG (${path}): ${reasonOf(error)}`);
  }
}

/** The one seam a test substitutes: draws one diagram's source, and lets go of the browser. */
export interface RenderSession {
  draw(source: string, format: 'svg' | 'png'): Promise<Uint8Array>;
  close(): Promise<void>;
}

/**
 * mermaid-cli, installed once into a gitignored prefix so the caller can patch its mermaid before the first
 * render. `npx -y` would run the binary before we could touch the tree. An installed prefix stays installed.
 */
export function installRenderer(): void {
  const bin = join(CLI_PREFIX, 'node_modules', '.bin', 'mmdc');
  if (existsSync(bin)) return;
  try {
    mkdirSync(CLI_PREFIX, { recursive: true });
    const manifest = join(CLI_PREFIX, 'package.json');
    if (!existsSync(manifest)) {
      writeFileSync(manifest, '{"name":"event-model-mermaid-cli","private":true}\n');
    }
    execFileSync('npm', ['install', '--no-audit', '--no-fund', '--loglevel=error', MERMAID_CLI], {
      cwd: CLI_PREFIX,
      stdio: 'inherit',
    });
  } catch (error) {
    throw new Error(`render: could not install ${MERMAID_CLI} into ${CLI_PREFIX}: ${reasonOf(error)}`);
  }
}

/** Where mermaid itself sits in the prefix: hoisted beside mermaid-cli, or nested under it. */
function mermaidManifests(): string[] {
  return [
    join(CLI_PREFIX, 'node_modules', 'mermaid', 'package.json'),
    join(CLI_PREFIX, 'node_modules', '@mermaid-js', 'mermaid-cli', 'node_modules', 'mermaid', 'package.json'),
  ].filter((path) => existsSync(path));
}

function versionOf(manifest: string): string {
  try {
    return (JSON.parse(readFileSync(manifest, 'utf8')) as { version?: string }).version ?? '';
  } catch (error) {
    throw new Error(`render: could not read the installed version in ${manifest}: ${reasonOf(error)}`);
  }
}

/** The scripts whose bytes decide how a diagram is drawn: a change to any of them redraws every diagram. */
const DRAWING_SCRIPTS = ['render.ts', 'render-plan.ts', 'render-session.ts', 'patch-mermaid-swimlanes.ts'];

/**
 * Names the renderer that drew a diagram: SHA-256 over the installed mermaid-cli, mermaid and Puppeteer versions
 * (in that order), the drawing scripts' bytes, the Puppeteer config's bytes (a fixed word when none is set), and
 * every environment variable whose name begins `PUPPETEER_`, as name and value in name order: Puppeteer reads those
 * itself, and one of them can name another browser. That is the closed set of what the launch takes from outside the
 * scripts, less two things it does not notice: a browser behind an `executablePath` the config names, whose upgrade
 * changes no byte here, and a Puppeteer rc file, which Puppeteer reads from the project and this does not.
 * Computed once per run, after the install and the patch and before any comparison. Every part is length-prefixed,
 * so two inputs cannot run together into a third that reads the same.
 */
export function rendererKey(config: PuppeteerConfig | undefined): string {
  const environment = Object.keys(process.env)
    .filter((name) => name.startsWith('PUPPETEER_'))
    .sort()
    .flatMap((name) => [name, process.env[name] ?? '']);
  const parts: (Buffer | string)[] = [
    versionOf(join(CLI_PREFIX, 'node_modules', '@mermaid-js', 'mermaid-cli', 'package.json')),
    mermaidManifests().map(versionOf).join(','),
    versionOf(join(CLI_PREFIX, 'node_modules', 'puppeteer', 'package.json')),
    ...DRAWING_SCRIPTS.map((name) => readFileSync(join(SCRIPT_DIR, name))),
    config === undefined ? 'no-puppeteer-config' : config.bytes,
    ...environment,
  ];
  const hash = createHash('sha256');
  for (const part of parts) {
    const bytes = Buffer.from(part);
    hash.update(`${String(bytes.length)}:`).update(bytes);
  }
  return hash.digest('hex');
}

/** The file a package's `.` export names for `import`, read the way Node would, from the prefix. */
function entryOf(packageName: string): string {
  const root = join(CLI_PREFIX, 'node_modules', ...packageName.split('/'));
  const manifest = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8')) as { exports?: unknown; main?: string };
  const pick = (target: unknown): string | undefined => {
    if (typeof target === 'string') return target;
    if (typeof target !== 'object' || target === null) return undefined;
    for (const condition of ['import', 'default', 'node', 'require']) {
      const found = pick((target as Record<string, unknown>)[condition]);
      if (found !== undefined) return found;
    }
    return undefined;
  };
  const exported = typeof manifest.exports === 'object' && manifest.exports !== null
    ? pick((manifest.exports as Record<string, unknown>)['.'])
    : pick(manifest.exports);
  return join(root, exported ?? manifest.main ?? 'index.js');
}

interface Browser {
  close(): Promise<void>;
}
interface MermaidCli {
  renderMermaid(browser: Browser, source: string, format: string, options: object): Promise<{ data: Uint8Array }>;
}

/**
 * A failure to open the browser, as one error that says so. Chromium refuses to start as root without
 * `--no-sandbox`, which is how every rootless container fails here; when that is the situation and no Puppeteer
 * config was given, one line first says which variable fixes it, rather than leaving Chromium's own message to be
 * searched for.
 */
function browserFailure(error: unknown): BrowserError {
  if (error instanceof BrowserError) return error; // a step that already said what it was: not the launch
  if (puppeteerConfigPath() === undefined && typeof process.getuid === 'function' && process.getuid() === 0) {
    process.stderr.write(
      'render: running as root, and Chromium will not start without --no-sandbox. Point MERMAID_PUPPETEER_CONFIG '
        + 'at a JSON file such as {"args": ["--no-sandbox", "--disable-dev-shm-usage"]} and rerun; the generated '
        + 'CI workflow does exactly this.\n',
    );
  }
  return new BrowserError(`render: could not start the browser: ${reasonOf(error)}`);
}

function parseConfig(config: PuppeteerConfig): object {
  try {
    return JSON.parse(config.bytes.toString('utf8')) as object;
  } catch (error) {
    throw new BrowserError(
      `render: MERMAID_PUPPETEER_CONFIG (${config.path}) is not valid JSON: ${reasonOf(error)}`,
    );
  }
}

/** A package of the prefix, imported by its entry; one that cannot be loaded is named as that, never as the launch. */
async function load<T>(packageName: string): Promise<T> {
  try {
    return (await import(pathToFileURL(entryOf(packageName)).href)) as T;
  } catch (error) {
    throw new BrowserError(`render: could not load ${packageName} from ${CLI_PREFIX}: ${reasonOf(error)}`);
  }
}

/** Opens the browser with the config the run already read, and the options its bytes parse to. */
export async function launch(config: PuppeteerConfig | undefined): Promise<RenderSession> {
  const cli = await load<MermaidCli>('@mermaid-js/mermaid-cli');
  const loaded = await load<{
    default?: { launch(options: object): Promise<Browser> };
    launch?: (options: object) => Promise<Browser>;
  }>('puppeteer');
  const puppeteer = loaded.default ?? (loaded as { launch(options: object): Promise<Browser> });
  const options = config === undefined ? {} : parseConfig(config);
  const browser = await puppeteer.launch({ headless: 'shell', ...options });
  return {
    async draw(source, format) {
      return (await cli.renderMermaid(browser, source, format, DRAW_OPTIONS)).data;
    },
    close: async () => {
      try {
        await browser.close();
      } catch (error) {
        throw new BrowserError(`render: could not close the browser: ${reasonOf(error)}`);
      }
    },
  };
}

/** A session that opens its browser on the first `draw`, once, however many are in flight; closing one never opened is a no-op. */
export function lazySession(open: () => Promise<RenderSession>): RenderSession & { readonly opened: boolean } {
  let session: Promise<RenderSession> | undefined;
  return {
    get opened(): boolean {
      return session !== undefined;
    },
    async draw(source, format) {
      session ??= open().catch((error: unknown) => {
        throw browserFailure(error);
      });
      return (await session).draw(source, format);
    },
    async close() {
      if (session === undefined) return;
      await (await session.catch(() => undefined))?.close();
    },
  };
}
