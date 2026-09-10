# Bash processes

- In Bash, `ps aux` snapshots processes with users, CPU, memory, and commands.
- In Bash, `top`/`htop` monitor live resource usage interactively.
- In Bash, `kill PID` requests termination; `kill -9` forces it as a last resort.
- In Bash, `pkill -f pattern` signals by command match instead of PID lookup.
- In Bash, `jobs`, `bg`, and `fg` manage shell-backgrounded work pipelines.
- In Bash, `cmd &` backgrounds immediately; `nohup cmd &` survives logout.
- In Bash, `nice`/`renice` lower priority of batch work to protect interactivity.
- In Bash, `lsof -i :8080` reveals which process holds a contested port.
- In Bash, `time cmd` reports real/user/sys durations for performance checks.
- In Bash, `watch -n1 cmd` reruns commands periodically for live observation.
