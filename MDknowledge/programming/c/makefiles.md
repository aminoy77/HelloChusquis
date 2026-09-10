# C makefiles

- In C, make rebuilds targets whose prerequisites changed, skipping fresh outputs.
- In C, `target: deps` rules pair with tab-indented recipes; spaces break parsing.
- In C, `$@` names the target, `$<` the first prerequisite, `$^` all prerequisites.
- In C, `.PHONY: clean` marks non-file targets so same-named files never shadow them.
- In C, `CFLAGS=-Wall -Wextra -g` centralizes warning and debug flags.
- In C, pattern rules like `%.o: %.c` compile families of sources uniformly.
- In C, header dependencies via `-MMD` flags regenerate objects when headers change.
- In C, `make -j$(nproc)` parallelizes independent recipes across cores.
- In C, `clean:` recipes remove artifacts for reproducible rebuilds.
- In C, prefer CMake or Meson past small projects; raw make scales poorly.
