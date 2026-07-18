#!/bin/sh

cd /app/share/sas || exit 1
exec python3 /app/share/sas/sas.py "$@"
