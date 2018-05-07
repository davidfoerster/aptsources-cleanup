#!/bin/sh
set -eu
while IFS=' =' read -r name value; do
	if [ "$(exec git config --get -- "$name")" != "$value" ]; then
		printf 'Setting: %s = %s\n' "$name" "$value"
		git config "$@" -- "$name" "$value"
	fi
done \
<<EOF
core.autocrlf = input
diff.po.textconv = msgcat --no-location --no-wrap --sort-output
EOF
