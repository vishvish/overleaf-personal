#!/bin/bash
bundle_root="$(cd "$(dirname "$0")" && pwd -P)" || exit 1
result=0
if "$bundle_root/overleaf" start; then
  open "$("$bundle_root/overleaf" url)" || result=$?
else
  result=$?
fi
printf '\nPress Return to close this window. '
read -r
exit "$result"
