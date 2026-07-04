#!/bin/bash
# Entrypoint script — fixes jpyconfig.properties before running any Java command
# Called automatically when container starts

D="/usr/local/lib/python3.8/dist-packages"

cat > "$D/jpyconfig.properties" << 'EOF'
jpy.jpyLib = /usr/local/lib/python3.8/dist-packages/jpy.cpython-38-x86_64-linux-gnu.so
jpy.jdlLib = /usr/local/lib/python3.8/dist-packages/jdl.cpython-38-x86_64-linux-gnu.so
jpy.pythonLib = /usr/lib/x86_64-linux-gnu/libpython3.8.so.1.0
jpy.pythonPrefix = /usr/local
jpy.pythonExecutable = /usr/bin/python3.8
EOF

echo "[entrypoint] jpyconfig.properties fixed:"
cat "$D/jpyconfig.properties"

# The simulator expands a 'testbed <experiment>' config into per-seed files under
# generatedExperiments/<experiment>/ but does not create that directory. Pre-create
# the output dirs for the requested experiment so the run does not fail.
base="${WORKSPACE:-/workspace}"
mkdir -p "$base/generatedExperiments" "$base/output" "$base/results"
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  if [ "${args[$i]}" = "testbed" ] || [ "${args[$i]}" = "folder" ]; then
    exp="${args[$((i+1))]}"
    [ -n "$exp" ] && mkdir -p "$base/generatedExperiments/$exp" "$base/output/$exp" "$base/results/$exp"
  fi
done

exec "$@"
