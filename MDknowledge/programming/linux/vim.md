# Vim essentials

- Vim modes: Normal (navigate), Insert (`i`), Visual (`v`), Command (`:`).
- `hjkl` move without arrows; `w/b` jump words, `0/$` line edges, `gg/G` file edges.
- `i/a/o` insert before cursor, after cursor, and new line below respectively.
- `dd` cuts lines, `yy` yanks, `p` pastes after cursor — Vim's clipboard verbs.
- `/pattern` searches forward, `n/N` repeats; `*` searches the word under cursor.
- `u` undoes, `Ctrl-r` redoes through the undo tree.
- `:w`, `:q`, `:wq`, `:q!` write, quit, write-quit, and force-quit respectively.
- `:%s/old/new/g` substitutes project-wide per file with `c` flag for confirm.
- `v` plus motions selects; `>`/`<` indent selections for code formatting.
- `.vimrc` (`set number`, `syntax on`) persists sane defaults across sessions.
