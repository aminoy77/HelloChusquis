# TypeScript interfaces

- In TypeScript, `interface User { name: string; age?: number }` shapes objects with optional fields.
- In TypeScript, `readonly` properties catch mutation at compile time.
- In TypeScript, interfaces merge across declarations; types do not — use merging for augmentation.
- In TypeScript, `extends` composes interfaces: `interface Admin extends User { level: number }`.
- In TypeScript, index signatures `{ [key: string]: number }` type dynamic dictionaries.
- In TypeScript, prefer `interface` for public object shapes and `type` for unions and tuples.
- In TypeScript, function types read `{(input: string): number}` inside interfaces.
- In TypeScript, `implements` clauses verify classes against interfaces at declaration.
- In TypeScript, optional methods use `save?(): void` syntax in interfaces.
- In TypeScript, excessive `any` in interfaces defeats checking; type fields precisely.
