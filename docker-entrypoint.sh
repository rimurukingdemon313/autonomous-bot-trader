#!/bin/sh
# Railway mounts a volume owned by root; the service runs as uid 10001.
# As root: give the data directory to the service user, then drop privileges
# for good. Anything else (a platform that already runs us as non-root) goes
# straight through.
set -e
DATA_DIR="${DATA_DIR:-/data}"
if [ "$(id -u)" = "0" ]; then
  mkdir -p "$DATA_DIR"
  chown -R 10001:10001 "$DATA_DIR"
  exec setpriv --reuid=10001 --regid=10001 --clear-groups "$@"
fi
exec "$@"
