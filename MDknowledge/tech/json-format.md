# JSON format

- JSON objects `{}` hold string keys; arrays `[]` hold ordered values.
- JSON strings need double quotes; single quotes and trailing commas are invalid.
- JSON numbers have no hex, octal, NaN, or Infinity forms.
- JSON booleans and null are lowercase literals only.
- JSON has no comments; strip or sidecar them before parsing.
- JSON UTF-8 is the interoperable default encoding for interchange.
- JSON Schema validates shapes before untrusted payloads reach logic.
- JSON Lines (one object per line) streams records that arrays would bloat.
- JSON numbers lose integer precision past 2^53; use strings for ids beyond it.
- JSON `null` means explicit absence versus missing keys meaning unknown.
