# Linux environment variables

- `printenv`/`env` list exports; `echo $HOME` expands single values.
- `export KEY=value` shares with child processes for the session.
- Persistence lives in `~/.bashrc` (interactive), `~/.profile` (login), `/etc/environment` (system).
- `PATH` colon-lists command search dirs; prepend project bins deliberately.
- `VAR=value cmd` scopes one-shot variables without polluting shells.
- `unset KEY` removes exports confusing downstream tools.
- `env -i` launches pristine environments exposing hidden variable dependencies.
- Secrets belong in managers, never exported in dotfiles or shell history.
- `set -u` fails on unset expansions, catching typos like `$SERIVCE` early.
- `${VAR:-default}` and `${VAR:?error}` express fallbacks and hard requirements inline.
