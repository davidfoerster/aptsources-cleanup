#!/bin/sh
set -eu
if [ -L "$0" ]; then EXE="$(exec readlink -e -- "$0")"; else EXE="$0"; fi
cd "${EXE%/*}" 2>&- || :

GIT_WD="$(exec git rev-parse --show-toplevel)"
GIT_DIR="$(exec git rev-parse --absolute-git-dir)"

while IFS=' =' read -r name value; do
	if [ "$(exec git config --get -- "$name")" != "$value" ]; then
		printf 'Setting: %s = %s\n' "$name" "$value"
		git config "$@" -- "$name" "$value"
	fi <&-
done \
<<EOF
core.autocrlf = input
diff.po.textconv = msgcat --no-location --no-wrap --sort-output
EOF

for hook_src in "$GIT_WD/tools/git-config/hooks/"*; do
	hook_dst="$GIT_DIR/hooks/${hook_src##*/}"
	if ! cmp -s -- "$hook_src" "$hook_dst"; then
		cp -viT -- "$hook_src" "$hook_dst"
	fi
done
