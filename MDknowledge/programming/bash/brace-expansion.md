# Bash brace expansion

- In Bash, `mkdir -p proj/{src,tests,docs}` creates trees in one command.
- In Bash, `{1..10}` generates sequences without external `seq`.
- In Bash, `{a,b,c}.txt` multiplies prefixes across shared suffixes.
- In Bash, `{01..12}` zero-pads numeric ranges for dated files.
- In Bash, nested braces (`{a,{b,c}}`) compose cartesian products.
- In Bash, expansion precedes globbing, so patterns generate before matching.
- In Bash, `echo {a..z}` lists alphabets for quick loops.
- In Bash, quote braces to suppress expansion when literal braces are needed.
