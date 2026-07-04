FROM ubuntu:20.04

# Evitar prompts interactivos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid

# Java 8 + Python 3.8 + herramientas de compilacion
RUN apt-get update && apt-get install -y \
    openjdk-8-jdk \
    python3.8 python3.8-dev python3.8-venv python3-pip \
    git wget curl build-essential maven \
    && rm -rf /var/lib/apt/lists/*

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH

# Verificar versiones instaladas
RUN java -version && python3.8 --version

# Python deps de analisis/forecasting
COPY environment/requirements_docker.txt /tmp/
RUN python3.8 -m pip install --upgrade pip && \
    python3.8 -m pip install -r /tmp/requirements_docker.txt && \
    python3.8 -m pip install 'holidays==0.25' --force-reinstall --no-deps

# jpy desde bcdev/jpy (MISMA fuente que el jpy-0.10.0-SNAPSHOT en metacloud.jar)
# Sergi compilo de github.com/bcdev/jpy en 2020-12-21. Compilar lado Python (.so)
# del mismo source garantiza protocolo compatible con el .jar bundleado.
# setuptools<58 requerido: jpy 0.10 usa use_2to3 (eliminado en setuptools 58+)
WORKDIR /opt
RUN python3.8 -m pip install 'setuptools<58' wheel && \
    git clone https://github.com/bcdev/jpy.git && \
    cd jpy && \
    JDK_HOME=$JAVA_HOME JAVA_HOME=$JAVA_HOME python3.8 setup.py build maven bdist_wheel && \
    python3.8 -m pip install dist/jpy-*.whl && \
    cp build/lib.linux-x86_64-3.8/jpy.cpython-38-x86_64-linux-gnu.so /usr/local/lib/python3.8/dist-packages/ && \
    cp build/lib.linux-x86_64-3.8/jdl.cpython-38-x86_64-linux-gnu.so /usr/local/lib/python3.8/dist-packages/ && \
    cp build/lib.linux-x86_64-3.8/*.jar /opt/jpy-built.jar 2>/dev/null || true

ENV JPY_LIB=/usr/local/lib/python3.8/dist-packages/jpy.cpython-38-x86_64-linux-gnu.so
ENV JDL_LIB=/usr/local/lib/python3.8/dist-packages/jdl.cpython-38-x86_64-linux-gnu.so
# libpython must be preloaded so the JVM can start the embedded Python (jpy)
ENV LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libpython3.8.so.1.0

# Copiar pymodule Python (forecasting: Prophet, AutoARIMA, KNN, Bollinger)
# Path local: networkExperiments/svila_phd_metacloudsim/cloudsim/src/main/python
# (montar via docker-compose volume, o COPY si build standalone)

# Entrypoint script — corrige jpyconfig.properties en runtime
COPY scripts/docker_entrypoint.sh /usr/local/bin/docker_entrypoint.sh
RUN chmod +x /usr/local/bin/docker_entrypoint.sh

# Main working directory. The repository is mounted here at run time
# (docker run -v "$PWD":/workspace ...), so jar, launcher.json, testbed/,
# workloads/, pymodule/ and results/ all come from the mounted repo.
WORKDIR /workspace

# Exponer puerto para Jupyter
EXPOSE 8888

ENTRYPOINT ["/usr/local/bin/docker_entrypoint.sh"]
# Por defecto: shell interactivo
CMD ["bash"]
