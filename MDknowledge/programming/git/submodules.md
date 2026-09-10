# Git submodules

- In Git, submodules pin external repos at exact commits inside superprojects.
- In Git, `git submodule add <url> path` registers plus clones in one step.
- In Git, clones need `git submodule update --init --recursive` to populate.
- In Git, superprojects record gitlinks (SHAs), not file contents, of submodules.
- In Git, update via pull inside, then commit the new gitlink outside.
- In Git, `git submodule foreach` runs commands across all submodules.
- In Git, subtrees merge histories alternatively for simpler collaboration.
- In Git, CI must recurse submodules or builds see empty directories.
