# SpVAR Colombia · Agro ↔ Industria manufacturera

Modelo **VAR Espacial (SpVAR)** de la relación entre la actividad agropecuaria y la industria manufacturera en los
32 departamentos de Colombia y Bogotá D.C., estimado por máxima verosimilitud, con interfaz interactiva en Streamlit.

[![Abrir en Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/andresguerradaza-ops/SPvar-agro-industria-colombia/blob/main/SpVAR_Colombia_agro_manufactura.ipynb)

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
- **App interactiva en Streamlit**: mapas, relieve 3D, simulador, ESDA, realidad aumentada e interpretación automática.

## Cómo ejecutarlo

### Opción 1 · Google Colab (recomendada)
Pulse el botón **Abrir en Colab** y luego *Entorno de ejecución → Ejecutar todo*. Las librerías se instalan solas.
Al final aparece la app y un enlace público temporal.

### Opción 2 · Streamlit Community Cloud (enlace permanente)
En share.streamlit.io: *Create app* → repositorio `andresguerradaza-ops/SPvar-agro-industria-colombia`,
rama `main`, archivo principal **`streamlit_app.py`**. En *Advanced settings* elija Python 3.11 o 3.12.

### Opción 3 · En su computador
```bash
git clone https://github.com/andresguerradaza-ops/SPvar-agro-industria-colombia.git
cd SPvar-agro-industria-colombia
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Archivos

| Archivo | Contenido |
|---|---|
| `SpVAR_Colombia_agro_manufactura.ipynb` | Notebook para Colab (una sola celda) |
| `spvar_colombia_agro_manufactura.py` | Código completo |
| `streamlit_app.py` | App web para Streamlit Cloud (ejecuta el código sin modificarlo y muestra las 8 pestañas) |
| `.streamlit/config.toml` | Tema oscuro de la app |
| `requirements.txt` | Librerías necesarias |

La primera ejecución tarda varios minutos: descarga los datos, estima todas las combinaciones de W y modelo, y
corre la auditoría. Los resultados (Excel, CSV, mapas, informe) se guardan en `spvar_resultados/`.

## Configuración

Todo se ajusta en el diccionario `CONFIG` al inicio del código: fuente de datos (`MODO_DATOS`), covariables
climáticas (`FUENTE_SAT`), matrices W candidatas, modelos, criterio de selección y horizonte de las respuestas impulso.

## Licencia

MIT
