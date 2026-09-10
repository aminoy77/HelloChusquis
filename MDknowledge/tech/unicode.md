# Unicode and UTF-8

- Unicode assigns every character a code point (U+0041 is Latin A).
- UTF-8 encodes ASCII in one byte and other scripts in two to four bytes.
- UTF-8 is backward compatible: pure ASCII is already valid UTF-8.
- UTF-16 uses two bytes per unit with surrogate pairs beyond U+FFFF.
- BOM markers (`\uFEFF`) prefix some files; strip them when parsing text.
- Normalization forms (NFC/NFD) equate composed and decomposed accents for comparison.
- Case folding (`casefold`) beats lowercasing for caseless matching across scripts.
- Grapheme clusters (flag, family emoji) span multiple code points per visible glyph.
- Always declare encodings explicitly; guessing produces mojibake corruption.
- Length in code units differs from visible characters in UTF-16 APIs.
