# Linux package managers

- `apt update` refreshes indexes; `apt upgrade` applies available updates.
- `apt install -y pkg` scripts installs non-interactively in automation.
- `dnf/yum` serve RHEL-family systems with near-identical verbs.
- `pacman -Syu` rolls Arch systems fully with one command.
- `snap`/`flatpak` sandbox desktop apps at disk-cost tradeoff.
- `dpkg -l | grep pkg` and `rpm -qa | grep pkg` audit installed software.
- Pin versions (`pkg=1.2.3`) in automation for reproducible fleets.
- `apt autoremove` plus `autoclean` reclaims orphaned packages and caches.
- Unattended-upgrades patch security releases automatically on servers.
- Vendor repos (PPAs, COPR) extend coverage at supply-chain trust cost.
