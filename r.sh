#!/bin/bash
# ./r.sh vistas [res] [outdir] [args p/ cxy.py]
cd ~/corexy && python3 scripts/cxy.py $4 > /dev/null || exit 1
LD_LIBRARY_PATH=~/.local/opt/blibs/root/usr/lib/x86_64-linux-gnu ~/.local/opt/blender-4.2.3-linux-x64/blender -b --factory-startup -P ~/mulbot/scripts/render_asm.py -- ~/corexy/out/cxy.json ${3:-$HOME/corexy/out/r} ${1:-iso} ${2:-1100} 2>&1 | grep -iE "error|Traceback" | head
