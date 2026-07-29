#!/usr/bin/env bash
# Waybar GPU module — NVIDIA via nvidia-smi.
# Outputs JSON: text, tooltip, percentage (for class thresholds).
# On a machine without nvidia-smi it prints an empty text, which makes waybar
# hide the module instead of showing "GPU n/a" forever.

command -v nvidia-smi >/dev/null || { printf '{"text":""}\n'; exit 0; }

read -r util temp mem_used mem_total power < <(
    nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,power.draw \
        --format=csv,noheader,nounits 2>/dev/null | tr -d ',' | head -n1
)

[[ -z "$util" ]] && { printf '{"text":""}\n'; exit 0; }

tooltip="GPU  ${util}%\nTemp  ${temp}°C\nVRAM  ${mem_used} / ${mem_total} MiB\nPower  ${power} W"

printf '{"text":"%s%%","tooltip":"%s","percentage":%s}\n' "$util" "$tooltip" "$util"
