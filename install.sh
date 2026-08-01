#!/usr/bin/env bash
# Set this desktop up on a fresh Arch box. Safe to re-run.
set -euo pipefail

repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
cfg="${XDG_CONFIG_HOME:-$HOME/.config}"
pics="${XDG_PICTURES_DIR:-$HOME/Pictures}"
stamp=$(date +%Y%m%d-%H%M%S)

say() { printf '\n\033[1;34m==>\033[0m %s\n' "$1"; }

[[ -f /etc/arch-release ]] || { echo "This expects Arch (or a derivative)." >&2; exit 1; }
[[ $EUID -ne 0 ]] || { echo "Run as your user, not root — it needs \$HOME." >&2; exit 1; }

# ── Packages ───────────────────────────────────────────────────────
say "Resolving packages"
mapfile -t wanted < <(sed 's/#.*//' "$repo/packages.txt" | tr -s ' ' '\n' | grep -v '^$')

repo_pkgs=() aur_pkgs=()
for p in "${wanted[@]}"; do
    if pacman -Si -- "$p" &>/dev/null; then repo_pkgs+=("$p"); else aur_pkgs+=("$p"); fi
done

say "Installing ${#repo_pkgs[@]} packages from the official repos"
sudo pacman -Syu --needed --noconfirm -- "${repo_pkgs[@]}"

if ((${#aur_pkgs[@]})); then
    helper=$(command -v paru || command -v yay || true)
    if [[ -n $helper ]]; then
        say "Installing from the AUR with ${helper##*/}: ${aur_pkgs[*]}"
        "$helper" -S --needed --noconfirm -- "${aur_pkgs[@]}"
    else
        say "No paru/yay found — install these yourself: ${aur_pkgs[*]}"
    fi
fi

# ── Per-machine config ─────────────────────────────────────────────
host="$repo/config/hypr/conf/host.lua"
if [[ ! -f $host ]]; then
    cp "$host.example" "$host"
    say "Created config/hypr/conf/host.lua (gitignored) — edit it for this machine's monitors"
fi

# ── Symlinks ───────────────────────────────────────────────────────
# Symlinks, not copies: editing ~/.config/hypr/... edits the repo, so `git diff`
# is the whole sync story.
say "Linking configs into $cfg"
mkdir -p "$cfg"
for dir in "$repo"/config/*/; do
    name=$(basename "$dir")
    target="$cfg/$name"
    if [[ -L $target ]]; then
        [[ $(readlink -f "$target") == "${dir%/}" ]] && { echo "  $name already linked"; continue; }
        rm "$target"
    elif [[ -e $target ]]; then
        mv "$target" "$target.bak.$stamp"
        echo "  backed up $name -> $name.bak.$stamp"
    fi
    ln -s "${dir%/}" "$target"
    echo "  linked $name"
done

chmod +x "$repo"/config/hypr/scripts/*.sh "$repo"/config/waybar/scripts/*.sh

# ── Wallpapers & screenshots ───────────────────────────────────────
say "Wallpapers -> $pics/wallpapers"
mkdir -p "$pics/wallpapers" "$pics/Screenshots"
cp -n "$repo"/wallpapers/* "$pics/wallpapers/" 2>/dev/null || true
command -v xdg-user-dirs-update >/dev/null && xdg-user-dirs-update

# ── Services ───────────────────────────────────────────────────────
say "Enabling services"
sudo systemctl enable --now NetworkManager.service
sudo systemctl enable --now bluetooth.service
systemctl --user enable --now pipewire.service pipewire-pulse.service wireplumber.service

# wlogout's style.css points at the packaged icons, so nothing to install there.
[[ -d /usr/share/wlogout/icons ]] || say "Note: /usr/share/wlogout/icons missing — power menu will have no icons"

say "Done."
cat <<'EOF'

Next:
  1. Edit config/hypr/conf/host.lua — monitors, workspace pinning, GPU env.
     `hyprctl monitors` (inside a session) lists output names.
  2. Log out and start Hyprland, or `hyprctl reload` if you're already in one.
  3. SUPER+/ shows every keybind. SHORTCUTS.md has the same list.
  4. Check for typos: hyprctl configerrors

EOF
