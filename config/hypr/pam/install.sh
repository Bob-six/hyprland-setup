#!/usr/bin/env bash
# Install hyprlock staged lockout into /etc. Run via: pkexec this-script
set -euo pipefail

SRC="$(cd "$(dirname "$0")" && pwd)"

install -d -m 0755 /run/faillock-hypr
install -D -m 0644 "$SRC/faillock-hypr-1min.conf"  /etc/security/faillock-hypr-1min.conf
install -D -m 0644 "$SRC/faillock-hypr-5min.conf"  /etc/security/faillock-hypr-5min.conf
install -D -m 0644 "$SRC/faillock-hypr-10min.conf" /etc/security/faillock-hypr-10min.conf
install -D -m 0644 "$SRC/faillock-hypr.conf"       /etc/tmpfiles.d/faillock-hypr.conf
install -D -m 0644 "$SRC/hyprlock"                 /etc/pam.d/hyprlock

# Drop any leftover lock-screen tally that used the system faillock dir.
if command -v faillock >/dev/null; then
  faillock --dir /run/faillock-hypr --reset || true
fi

echo "hyprlock PAM lockout installed: 5→1min, 10→5min, 15→10min"
