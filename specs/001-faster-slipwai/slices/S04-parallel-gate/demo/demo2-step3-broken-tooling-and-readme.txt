$ grep -n 'not reinstalled\|node_modules' docs/event-model/README.md
596:given a Node for it where the project has none of its own. Where a run says the tooling was not reinstalled and then
598:a file's date), delete `scripts/event-model/node_modules` (under `delivery/` in an adopted repository) and run the gate

@esbuild
esbuild
tsx
yaml
zod
-rw-rw-r-- 1 noahc noahc 0 Oct  4 11:07 scripts/event-model/node_modules/.installed

$ rm -rf scripts/event-model/node_modules/esbuild

$ make check-drawio
check-drawio: scripts/event-model/package-lock.json is not newer than the installed model tooling; not reinstalled
node scripts/event-model/node_modules/tsx/dist/cli.mjs scripts/event-model/render-drawio.ts --check
node:internal/modules/cjs/loader:1386
  throw err;
  ^

Error: Cannot find module 'esbuild'
Require stack:
- /tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/index-6kqi0x0U.cjs
- /tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/register-C557imBs.cjs
- /tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/cjs/index.cjs
- /tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/get-pipe-path-D4YM6rQt.cjs
- /tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/preflight.cjs
- internal/preload
    at Module._resolveFilename (node:internal/modules/cjs/loader:1383:15)
    at defaultResolveImpl (node:internal/modules/cjs/loader:1025:19)
    at resolveForCJSWithHooks (node:internal/modules/cjs/loader:1030:22)
    at Module._load (node:internal/modules/cjs/loader:1192:37)
    at TracingChannel.traceSync (node:diagnostics_channel:328:14)
    at wrapModuleLoad (node:internal/modules/cjs/loader:237:24)
    at Module.require (node:internal/modules/cjs/loader:1463:12)
    at require (node:internal/modules/helpers:147:16)
    at Object.<anonymous> (/tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/index-6kqi0x0U.cjs:1:147)
    at Module._compile (node:internal/modules/cjs/loader:1705:14) {
  code: 'MODULE_NOT_FOUND',
  requireStack: [
    '/tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/index-6kqi0x0U.cjs',
    '/tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/register-C557imBs.cjs',
    '/tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/cjs/index.cjs',
    '/tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/get-pipe-path-D4YM6rQt.cjs',
    '/tmp/s04-demo2/shop/scripts/event-model/node_modules/tsx/dist/preflight.cjs',
    'internal/preload'
  ]
}

Node.js v22.22.1
make: *** [Makefile:152: check-drawio] Error 1
exit 2

$ rm -rf scripts/event-model/node_modules   # what the README says

$ make check-drawio
npm --prefix scripts/event-model ci --no-audit --no-fund --loglevel=error

added 5 packages in 320ms
node scripts/event-model/node_modules/tsx/dist/cli.mjs scripts/event-model/render-drawio.ts --check
check-drawio: docs/event-model/model.yaml has no slices yet — nothing to check.
exit 0

$ make check-drawio
check-drawio: scripts/event-model/package-lock.json is not newer than the installed model tooling; not reinstalled
node scripts/event-model/node_modules/tsx/dist/cli.mjs scripts/event-model/render-drawio.ts --check
check-drawio: docs/event-model/model.yaml has no slices yet — nothing to check.
exit 0

$ git status --porcelain
