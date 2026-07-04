# Datos del proyecto — Paper 4

## Donde estan los datos reales

Los datos NO se copian a este directorio por su tamano (varios GB).
Estan en su ubicacion original:

```
C:\Users\PcVIP\Desktop\Proyecto Sergi\networkExperiments\
├── workloads\
│   ├── planetlab\          # Trazas PlanetLab (workload principal del paper)
│   ├── materna\            # Trazas Materna/BitBrains
│   ├── alibaba2018\        # Trazas Alibaba 2018
│   └── azure\              # Trazas Azure
├── paper4_data\            # Resultados del paper (GROUND TRUTH)
│   ├── planetlab\          # xlsx + figuras PlanetLab
│   ├── alibaba_wbf_final_without_wibf\   # xlsx + figuras Alibaba
│   ├── materna_wbf_final_without_wibf\   # xlsx + figuras Materna
│   └── azure_wbf_final_without_wibf\     # xlsx + figuras Azure
├── topologies\             # Definiciones de topologia de red
│   └── fatTreeTopology_*   # Fat-tree topologies para simulacion
├── interactions\           # Matrices de interaccion entre VMs
│   └── fnss3000_*          # Trafico FNSS a 3000 nodes
└── testbed\                # Configuraciones JSON de experimentos
    └── paper4_*.json       # Configs del Paper 4
```

## Workloads del paper

### PlanetLab (workload principal)
- Fuente: PlanetLab distributed computing traces
- Periodo: 2011-03-03 (24h)
- VMs: 800 VMs (100 hosts x 8 VMs/host)
- Usado en: Tabla 6 del paper
- Archivo clave: `planetlab_20110303_100_mostDiff` (100 trazas mas variables)

### Alibaba 2018
- Fuente: Alibaba Cloud Production Cluster Traces 2018
- Periodo: muestras de 8 dias
- Usado en: Tabla 7 del paper

### Materna (BitBrains)
- Fuente: BitBrains Fast Storage cluster
- Periodo: muestras de produccion
- Usado en: Tabla 8 del paper

### Azure
- Fuente: Microsoft Azure VM traces
- Periodo: muestras de produccion
- Usado en: Tabla 9 del paper

## Ground truth (resultados del paper)

Los resultados originales que el paper reporta estan en:
`networkExperiments/paper4_data/`

Estos NO necesitan re-ejecutarse para el analisis. Ver:
- `results/reference/README.md` — descripcion de los resultados
- `scripts/run_analysis.py` — script de analisis sobre estos datos
- `python/notebooks/statistics_paper4.ipynb` — notebook completo

## Para re-ejecutar las simulaciones

Ver: `README.md` en la raiz de `project_minimized/`
Requiere: Java 8 + Python 3.8 + jpy + pymodule (o Docker)
