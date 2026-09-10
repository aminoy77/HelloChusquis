# Bash tar and archives

- In Bash, `tar czf out.tar.gz dir/` compresses directories with gzip in one step.
- In Bash, `tar xzf in.tar.gz` extracts gzip archives into the current directory.
- In Bash, `tar tzf in.tar.gz` lists contents without extracting anything.
- In Bash, `z/j/J` select gzip, bzip2, and xz compression for tar pipelines.
- In Bash, `tar xf file.tar.*` auto-detects compression on modern tar versions.
- In Bash, `zip -r out.zip dir/` and `unzip -l out.zip` handle zip archives symmetrically.
- In Bash, `--exclude='*.log'` skips noise when archiving trees.
- In Bash, `-C dir` changes directory before archiving to control stored paths.
- In Bash, `tar --strip-components=1` drops leading folders on extraction.
- In Bash, verify archives (`tar tzf`) after creation before deleting originals.
