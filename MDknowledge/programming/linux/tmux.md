# tmux essentials

- tmux multiplexes persistent terminal sessions surviving disconnects.
- `tmux new -s work` names sessions; `tmux attach -t work` rejoins them.
- Prefix `Ctrl-b` precedes all commands: `%` vertical split, `"` horizontal.
- `Ctrl-b d` detaches keeping work alive; `tmux ls` inventories sessions.
- `Ctrl-b c` spawns windows; `n/p` cycle them like browser tabs.
- `Ctrl-b [` enters scrollback copy mode with familiar search keys.
- `tmux kill-session -t old` reaps finished work deliberately.
- `.tmux.conf` rebinds prefix (often `Ctrl-a`) and enables mouse support.
- Pair sessions (`attach -t` twice) for shared incident terminals.
- Script layouts (`new-session` plus `split-window`) for one-command war rooms.
