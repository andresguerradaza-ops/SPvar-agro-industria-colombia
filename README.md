---
title: SpVAR Colombia Agro Manufactura
emoji: 🌾
colorFrom: green
colorTo: blue
sdk: gradio
app_file: app.py
python_version: "3.11"
pinned: false
license: mit
---

# SpVAR Colombia · Agro ↔ Industria manufacturera

Modelo **VAR Espacial (SpVAR)** de la relación entre la actividad agropecuaria y la industria manufacturera en los
32 departamentos de Colombia y Bogotá D.C., estimado por máxima verosimilitud, con interfaz interactiva en Gradio.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/andresguerradaza-ops/SPvar/blob/main/SpVAR_Colombia_agro_manufactura.ipynb)

## Qué hace

- **Datos reales descargados automáticamente** (no hay que subir archivos):
  - Valor agregado agropecuario y manufacturero: DANE, Cuentas Nacionales Departamentales, base 2015, precios constantes.
  - Precipitación y temperatura anual: NASA POWER (MERRA-2), como anomalías estandarizadas.
  - Geometría: geoBoundaries ADM1 (o el MGN del DANE).
- **Selección automática** de la matriz de pesos W (Queen, Rook, k-vecinos, distancia inversa) y de la especificación
  de cada ecuación (OLS, SAR, SEM, SAC, SDM) con AIC/BIC, pruebas LM y LR.
- **Cuatro mecanismos de transmisión**: autodinámica espacial, cruce local, relación espacial directa y cruzada,
  con impactos directos e indirectos.
- **Dinámica**: estabilidad del sistema, respuestas impulso y simulador de choques por departamento.
- **Auditoría**: estacionariedad, matrices de covarianza, residuos y pruebas de robustez.
- **App Gradio**: mapas, ESDA, vistas 3D, simulador e interpretación automática.

## Cómo ejecutarlo

### Opción 1 · Google Colab (recomendada)
Pulse el botón **Abrir en Colab** y luego *Entorno de ejecución → Ejecutar todo*. Las librerías se instalan solas.
Al final aparece la app y un enlace público temporal.

### Opción 2 · En su computador
```bash
git clone https://github.com/andresguerradaza-ops/SPvar.git
cd SPvar
pip install -r requirements.txt
python app.py
```

### Opción 3 · Hugging Face Spaces (enlace permanente)
Cree un Space con SDK **Gradio** y suba `app.py`, `spvar_colombia_agro_manufactura.py` y `requirements.txt`
junto con este `README.md` (su encabezado ya trae la configuración del Space).

## Archivos

| Archivo | Contenido |
|---|---|
| `SpVAR_Colombia_agro_manufactura.ipynb` | Notebook para Colab (una sola celda) |
| `spvar_colombia_agro_manufactura.py` | Código completo |
| `app.py` | Punto de entrada para ejecución local o Hugging Face Spaces |
| `requirements.txt` | Librerías necesarias |

La primera ejecución tarda varios minutos: descarga los datos, estima todas las combinaciones de W y modelo, y
corre la auditoría. Los resultados (Excel, CSV, mapas, informe) se guardan en `spvar_resultados/`.

## Configuración

Todo se ajusta en el diccionario `CONFIG` al inicio del código: fuente de datos (`MODO_DATOS`), covariables
climáticas (`FUENTE_SAT`), matrices W candidatas, modelos, criterio de selección y horizonte de las respuestas impulso.

## Licencia

MIT
