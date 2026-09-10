# TypeScript basics

- In TypeScript, `let x: number = 1` annotates types; the compiler rejects mismatched assignments.
- In TypeScript, `any` disables checking while `unknown` forces narrowing before use; prefer `unknown`.
- In TypeScript, `interface User { name: string; age?: number }` shapes objects, with `?` marking optional fields.
- In TypeScript, `type` aliases compose unions (`string | null`) while interfaces describe object shapes and merge.
- In TypeScript, function signatures annotate both sides: `(input: string) => number`.
- In TypeScript, generics like `function first<T>(xs: T[]): T | undefined` keep collection utilities type-safe.
- In TypeScript, `strict: true` in tsconfig enables null checks and strict inference; keep it on.
- In TypeScript, `strictNullChecks` forces handling `null`/`undefined` instead of crashing at runtime.
- In TypeScript, narrow unions with `typeof x === "string"` guards or `in` checks before accessing variants.
- In TypeScript, `as const` freezes literals (`"red" as const`) for exact-type constants and readonly tuples.
- In TypeScript, `readonly` arrays and properties catch accidental mutation at compile time.
- In TypeScript, `enum` has runtime cost and quirks; string-literal unions (`"a" | "b"`) are usually simpler.
- In TypeScript, `Record<string, number>` types dictionaries and `Partial<T>`/`Pick<T>` derive variants.
- In TypeScript, `async` functions return `Promise<T>`; annotate the resolved type, not the promise wrapper twice.
- In TypeScript, `tsc --noEmit` type-checks without producing files, ideal for CI gates.
- In TypeScript, `// @ts-ignore` silences one error line; `// @ts-expect-error` fails loudly when the error disappears.
- In TypeScript, `.d.ts` declaration files describe untyped JavaScript for the checker.
- In TypeScript, `npm run` scripts plus `tsc` build steps belong in CI before tests execute.
