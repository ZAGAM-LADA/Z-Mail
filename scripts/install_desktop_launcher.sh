#!/usr/bin/env bash
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$APP_DIR"
cat > "$APP_DIR/z-mail-recovery.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Z-MAIL RECOVERY
Comment=Local email investigation and archive extraction
Exec=/bin/bash "$PROJECT_DIR/run.sh"
Terminal=false
Categories=Utility;Office;
StartupNotify=true
EOF
chmod 644 "$APP_DIR/z-mail-recovery.desktop"
echo "Desktop launcher installed: $APP_DIR/z-mail-recovery.desktop"
