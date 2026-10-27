#!/bin/bash
bundle_root="$(cd "$(dirname "$0")" && pwd -P)" || exit 1
"$bundle_root/overleaf" stop
result=$?
printf '\nPress Return to close this window. '
read -r
exit "$result"
