# TypeScript strictness

- In TypeScript, 'strict: true' enables the full safety family; keep it on for new projects.
- In TypeScript, `strictNullChecks` forces explicit handling of `null` and `undefined`.
- In TypeScript, `noUncheckedIndexedAccess` makes `arr[i]` possibly undefined, catching bounds bugs.
- In TypeScript, `noImplicitAny` rejects silently untyped parameters and members.
- In TypeScript, `exactOptionalPropertyTypes` distinguishes missing keys from explicit `undefined`.
- In TypeScript, enable `noUnusedLocals` and `noUnusedParameters` to prune dead code continuously.
- In TypeScript, `// @ts-expect-error` asserts an error exists and fails loudly once fixed.
- In TypeScript, narrowing with `if (x == null) return` satisfies the checker idiomatically.
- In TypeScript, assertion functions `asserts x is T` teach the checker custom validations.
- In TypeScript, `satisfies` checks shape conformance while preserving precise inferred types.
