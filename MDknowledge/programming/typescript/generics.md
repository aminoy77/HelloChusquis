# TypeScript generics

- In TypeScript, `function first<T>(xs: T[]): T | undefined` preserves element types through helpers.
- In TypeScript, constrain parameters with `extends`: `<T extends { id: string }>` demands structure.
- In TypeScript, `Array<T>` and `T[]` spell the same type; pick one style per codebase.
- In TypeScript, `keyof T` unions a type's keys for safe dynamic access.
- In TypeScript, `Record<string, T>` types string-keyed dictionaries uniformly.
- In TypeScript, `Partial<T>`, `Required<T>`, `Pick<T, K>`, and `Omit<T, K>` derive variants without duplication.
- In TypeScript, generic classes `class Box<T> { value: T }` carry types through instances.
- In TypeScript, default type args `<T = string>` keep common cases terse.
- In TypeScript, variance is structural: assignability follows shape compatibility, not declarations.
- In TypeScript, avoid `Function` and `{}` types; they accept almost anything silently.
