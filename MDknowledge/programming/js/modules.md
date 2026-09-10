# JavaScript modules

- In JavaScript, `export function f()` shares bindings and `import {f} from './m.js'` consumes them.
- In JavaScript, `export default` allows any import name but permits only one per module.
- In JavaScript, named exports refactor safely; default exports obscure usage in editors.
- In JavaScript, `import()` loads modules dynamically, enabling route-level code splitting.
- In JavaScript, ES modules are strict mode with deferred execution by default.
- In JavaScript, circular imports resolve partially; restructure shared bits into a third module.
- In JavaScript, `package.json` 'type: module' selects ESM; `.cjs` keeps CommonJS per file.
- In JavaScript, bare specifiers (`import 'lodash'`) resolve via bundlers or import maps, not browsers.
- In JavaScript, side-effect-only `import './init.js'` runs setup exactly once per graph.
- In JavaScript, tree-shaking drops unused named exports from production bundles.
