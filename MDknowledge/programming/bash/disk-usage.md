# Bash disk usage

- In Bash, `df -h` reports filesystem free space in human units.
- In Bash, `du -sh dir` summarizes one directory's total footprint.
- In Bash, `du -sh * | sort -h` ranks children to find space hogs fast.
- In Bash, `ncdu` navigates usage interactively for big cleanups.
- In Bash, `find / -size +1G` hunts gigabyte-scale files across mounts.
- In Bash, `lsof +L1` lists deleted-but-open files still consuming disk.
- In Bash, `journalctl --disk-usage` plus `--vacuum-size` trims systemd logs.
- In Bash, `docker system df` and `docker system prune` audit container disk use.
- In Bash, inodes exhaust independently of bytes; `df -i` diagnoses 'no space' with free GB.
- In Bash, `/tmp` and caches are the first safe candidates during space crunches.
