# Data model: S11-render-once

No stored data but the SVG files themselves.

| Thing | Shape | Rule |
|---|---|---|
| Source stamp | line 1 of an SVG: `<!-- em-source-sha256: <64 hex> -->` | As today; what `extractHash` and `check.ts` read. |
| Renderer line | line 2 of an SVG: `<!-- em-renderer-sha256: <64 hex> -->` | New. Absent in an SVG an earlier factory drew: that SVG is redrawn once. |
| Renderer key | SHA-256 over: installed mermaid-cli version; installed mermaid version; installed puppeteer version (D70); the bytes of `render.ts`, `render-plan.ts`, `render-session.ts`, `patch-mermaid-swimlanes.ts`; the bytes of the file `MERMAID_PUPPETEER_CONFIG` names, or a fixed word | Computed once per run, after the install and the patch, before any comparison. Each part is length-prefixed or separated so two inputs cannot run together. |
| Diagram | `{ kind: global | segment | slice, mmd path, svg path, source }` | The model produces 1 + segments + slices of them, in that order. |
| Current | all of: stamp equals the source's hash · renderer line equals the key · trimmed file ends `</svg>` · no CI marker (`CI`, `GITHUB_ACTIONS`, `GITLAB_CI` non-empty) | Otherwise drawn. |
| `RenderSession` | `draw(source, 'svg' | 'png') → bytes`, `close()` | Opened by the first draw; at most one per run; up to four draws in flight. |
| Report | `{ slices, diagrams, drawn, unchanged, sessionOpened }` | The closing line is written from it. |
