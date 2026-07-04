#!/bin/bash
# Reproducible build of the SOTA-comparison methods (AMOVMC, EUQ-VMC) into metacloud.jar.
#
# metacloud.jar is an Eclipse "runnable JAR" (flat application classes at the root +
# nested dependency jars listed in the manifest Rsrc-Class-Path). We therefore:
#   1. extract the nested dependency jars to libs/ to form a compile classpath,
#   2. compile the new + modified svila/* sources against metacloud.jar + libs/*,
#   3. inject the resulting .class files back into metacloud.jar (jar uf).
# No Maven fat-jar reassembly is needed; the new classes become flat root classes
# exactly like the existing svila.* classes and are picked up by the jarinjarloader.
#
# Run inside the toolchain image (Java 8):
#   docker run --rm -v "$PWD:/work" -w /work metacloudsim-neural:latest bash scripts/build_sota.sh
set -eu

SRC="SOTA/src"   # SOTA method sources shipped in this repo (svila/* packages)
JAR="metacloud.jar"
WORK="$(mktemp -d)"
mkdir -p "$WORK/libs" "$WORK/classes"

echo "[1/3] extracting nested dependency jars -> compile classpath"
( cd "$WORK/libs" && unzip -o -q "$OLDPWD/$JAR" "*.jar" )

FILES="
svila/metricsLogic/CPUCalculator/DWMAForecastingTechnique.java
svila/metricsLogic/CPUCalculator/ForecastingTechniqueFactory.java
svila/policiesHostOverSaturation/future/FutureHostOverSaturationAMOVMC.java
svila/policiesHostOverSaturation/future/FutureHostOverSaturationEUQVMC.java
svila/policiesVmSelection/future/FutureAMOVMCVmSelection.java
svila/policiesVmSelection/future/FutureEUQVMCVmSelection.java
svila/policiesFactories/future/FutureHostOverSaturationPolicyFactory.java
svila/policiesFactories/future/FutureVmSelectionPolicyFactory.java
"

echo "[2/3] compiling SOTA sources against $JAR + libs/*"
SRCS=""
for f in $FILES; do SRCS="$SRCS $SRC/$f"; done
javac -encoding UTF-8 -cp "$JAR:$WORK/libs/*" -d "$WORK/classes" $SRCS

echo "[3/3] injecting compiled classes into $JAR"
( cd "$WORK/classes" && jar uf "$OLDPWD/$JAR" svila )

rm -rf "$WORK"
echo "DONE. AMOVMC (host=amovmc sel=amovmc fc=dwma) and EUQ-VMC (host=euqvmc sel=euqvmc) are now available."
