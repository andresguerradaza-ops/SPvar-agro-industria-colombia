"""SpVAR Colombia · Agro ↔ Industria — interfaz para Streamlit Community Cloud.

Ejecuta el script principal (spvar_colombia_agro_manufactura.py) SIN modificarlo: corre todo el pipeline
(descarga DANE y NASA POWER, estimación, auditoría y preparación de figuras) y omite solo la última parte, que
lanza la interfaz Gradio. Luego muestra las mismas vistas con controles de Streamlit, reutilizando las funciones
del script (vista_mapas, vista_simulador, vista_esda, vista_relieve, vista_spvar, vista_ra...).
"""
import os
import re
import sys
import time
import types

os.environ.setdefault("MPLBACKEND", "Agg")

import streamlit as st
import streamlit.components.v1 as components

SCRIPT = os.environ.get(
    "SPVAR_SCRIPT",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "spvar_colombia_agro_manufactura.py"),
)
MARCA_GRADIO = '"""## Celda 19'          # desde aquí el script solo construye y lanza la app Gradio

st.set_page_config(page_title="SpVAR Colombia · Agro ↔ Industria", page_icon="🌾", layout="wide")


# ----------------------------------------------------------------------------------------------
# 1. Ejecutar el pipeline una sola vez por servidor (queda en caché para todos los visitantes)
# ----------------------------------------------------------------------------------------------
def _escala(colores):
    n = len(colores) - 1
    return [[round(i / n, 4), c] for i, c in enumerate(colores)]


PALETAS_CLARAS = {
    # centro gris claro: los valores cercanos a cero se distinguen del fondo oscuro
    "Divergente rojo–azul": _escala(["#b2182b", "#d6604d", "#f4a582", "#eeeeee", "#92c5de", "#4393c3", "#2166ac"]),
    "Viridis": _escala(["#440154", "#414487", "#2a788e", "#22a884", "#7ad151", "#fde725"]),
    "Plasma": _escala(["#0d0887", "#6a00a8", "#b12a90", "#e16462", "#fca636", "#f0f921"]),
    "Cividis": _escala(["#00224e", "#35456c", "#666970", "#948e77", "#c8b866", "#fee838"]),
}


def aplicar_paletas_claras(ns):
    """Sustituye las escalas 'nocturnas' (con extremos o centro casi negros) por paletas legibles sobre fondo
    oscuro, sin modificar el script: se reemplazan las referencias en el espacio de nombres ya ejecutado."""
    esc = ns.get("ESCALAS")
    if not esc:
        return
    reemplazo = {
        id(esc["Divergente nocturna"]): PALETAS_CLARAS["Divergente rojo–azul"],
        id(esc["Visión nocturna · cian"]): PALETAS_CLARAS["Viridis"],
        id(esc["Visión nocturna · fósforo"]): PALETAS_CLARAS["Viridis"],
        id(esc["Térmica nocturna"]): PALETAS_CLARAS["Plasma"],
    }
    for etq, valor in list(ns["VARS_MAPA"].items()):
        if id(valor[3]) in reemplazo:
            ns["VARS_MAPA"][etq] = valor[:3] + (reemplazo[id(valor[3])],) + valor[4:]
    ns["ESC_DIV"] = PALETAS_CLARAS["Divergente rojo–azul"]
    ns["ESC_SEQ"] = PALETAS_CLARAS["Viridis"]
    ns["ESCALAS"] = {**PALETAS_CLARAS, **esc}            # las nocturnas siguen disponibles en el selector
    ns["PALETAS"] = ["Auto"] + list(ns["ESCALAS"])
    if "COLORES_LISA" in ns:                             # "No significativo" era casi del color del fondo
        ns["COLORES_LISA"].update({"Alto-Alto": "#d6604d", "Bajo-Bajo": "#4393c3", "Alto-Bajo": "#f4a582",
                                   "Bajo-Alto": "#92c5de", "No significativo": "#5b6770"})


def _area_firmada(anillo):
    return 0.5 * sum(x0 * y1 - x1 * y0 for (x0, y0, *_), (x1, y1, *_) in zip(anillo, anillo[1:]))


def orientar_para_plotly(geojson):
    """GeoJSON estándar (RFC 7946) dibuja el borde exterior en sentido antihorario; los mapas de Plotly
    (d3-geo) esperan sentido horario y, si no, rellenan 'todo el planeta menos el polígono'. Se invierten
    los anillos que lo necesitan: exterior horario (área < 0) y huecos antihorarios (área > 0)."""
    import copy
    gj = copy.deepcopy(geojson)

    def arreglar(poligono):
        salida = []
        for j, anillo in enumerate(poligono):
            area = _area_firmada(anillo)
            invertir = area > 0 if j == 0 else area < 0
            salida.append(anillo[::-1] if invertir else anillo)
        return salida

    for f in gj.get("features", []):
        g = f.get("geometry") or {}
        if g.get("type") == "Polygon":
            g["coordinates"] = arreglar(g["coordinates"])
        elif g.get("type") == "MultiPolygon":
            g["coordinates"] = [arreglar(p) for p in g["coordinates"]]
    return gj


@st.cache_resource(show_spinner=False)
def ejecutar_pipeline():
    with open(SCRIPT, encoding="utf-8") as fh:
        fuente = fh.read()
    corte = fuente.find(MARCA_GRADIO)
    if corte < 0:
        raise RuntimeError(f"No se encontró la marca {MARCA_GRADIO!r} en {SCRIPT}.")
    try:                                      # la Celda 18 solo importa gradio; aquí no se usa
        import gradio  # noqa: F401
    except Exception:
        sys.modules["gradio"] = types.ModuleType("gradio")
    ns = {"__name__": "__spvar__", "__file__": SCRIPT}
    exec(compile(fuente[:corte], SCRIPT, "exec"), ns)
    if ns.get("GEOJ") is not None:            # Plotly necesita anillos exteriores en sentido horario
        ns["GEOJ"] = orientar_para_plotly(ns["GEOJ"])
    aplicar_paletas_claras(ns)
    m = re.search(r'CSS_APP = """(.*?)"""', fuente[corte:], re.S)
    ns["_CSS_APP"] = m.group(1) if m else ""
    return ns


with st.spinner("Descargando datos oficiales y estimando el SpVAR… la primera carga tarda varios minutos."):
    try:
        S = ejecutar_pipeline()
    except Exception as e:                    # el script se detiene con un mensaje claro si falla una descarga
        st.error(f"El pipeline se detuvo: {e}")
        st.exception(e)
        st.stop()

st.markdown(
    f"""<style>{S['_CSS_APP']}
.stApp {{background: radial-gradient(1000px 520px at 12% -10%, #06263a 0%, transparent 60%),
  linear-gradient(170deg, #01050a 0%, #02070d 50%, #030a12 100%);}}
.interp {{display:block;}}
.kpi .l {{text-transform: none !important;}}   /* evita que ρ en mayúscula se vea como "P" */
</style>""",
    unsafe_allow_html=True,
)

NOMBRES_VAR, ORDEN, dn, up = S["NOMBRES_VAR"], S["ORDEN"], S["dn"], S["up"]
ANIOS, CONFIG, PAUSA = S["ANIOS"], S["CONFIG"], S["PAUSA_ANIM"]
DEPTOS = list(S["DPT"].nombre)
ORIGEN0 = S["COD_A_NOMBRE"].get(CONFIG["DPTO_CHOQUE"], DEPTOS[0])
HMAX = CONFIG["HORIZONTE_IRF"]
TIPOS = [t for t, _ in S["TIPOS_CHOQUE"]]
ARGS0 = (ORIGEN0, TIPOS[0], 1.0, HMAX, NOMBRES_VAR[dn])
VARS_MAPA, VARS_PANEL = list(S["VARS_MAPA"]), S["VARS_PANEL"]
VAR0 = VARS_PANEL[0]
ECUS = [NOMBRES_VAR[v] for v in S["FINAL"]]
MODOS_3D = {"Raíz con signo (realza efectos pequeños)": "raiz", "Lineal": "lineal"}
RESPUESTAS = [NOMBRES_VAR[v] for v in ORDEN]
ANIO_MIN, ANIO_MAX = int(ANIOS[0]), int(ANIOS[-1])


def grafico(destino, fig, key):
    """Dibuja una figura Plotly conservando el estilo nocturno del script."""
    destino.plotly_chart(fig, use_container_width=True, theme=None, key=key)


def interp(destino, texto):
    destino.markdown(texto)


def sin_ninguno(valor):
    return None if valor == "(ninguno)" else valor


# ----------------------------------------------------------------------------------------------
# 2. Encabezado
# ----------------------------------------------------------------------------------------------
proc = S.get("PROCEDENCIA", {})
st.markdown(
    f"""<div class='hero'><h1>SpVAR Colombia · Agro ↔ {NOMBRES_VAR['ind']}</h1>
<p>Transmisión dinámica y espacial entre la actividad agropecuaria y la industria ·
{S['N']} unidades territoriales · {ANIO_MIN}–{ANIO_MAX} · geometría: {S['FUENTE_GEOM']}<br>
Datos: {proc.get('fuente', '')}{' · clima: NASA POWER' if proc.get('clima') else ''}</p></div>""",
    unsafe_allow_html=True,
)
if S["AVISO_DEMO"]:
    st.markdown(S["AVISO_DEMO"], unsafe_allow_html=True)
st.markdown(S["html_kpis"](), unsafe_allow_html=True)

tabs = st.tabs(["Inicio", "Mapas nocturnos", "Relieve 3D", "Simulador de perturbaciones", "ESDA",
                "Realidad aumentada", "Modelo SpVAR", "Interpretabilidad"])

# ---- 1. Inicio ----
with tabs[0]:
    h = st.slider("Año tras el choque", 0, HMAX, 0, 1, key="i_h")
    reproducir = st.button("▶ Reproducir la difusión", type="primary", key="i_btn")
    c1, c2 = st.columns(2)
    p_mapa, p_rel = c1.empty(), c2.empty()
    if reproducir:
        for hh in range(HMAX + 1):
            mapa, rel = S["cuadro_sim"](*ARGS0, hh)
            grafico(p_mapa, mapa, f"i_mapa_{hh}")
            grafico(p_rel, rel, f"i_rel_{hh}")
            time.sleep(PAUSA)
    else:
        mapa, rel = S["cuadro_sim"](*ARGS0, h)
        grafico(p_mapa, mapa, "i_mapa")
        grafico(p_rel, rel, "i_rel")
    interp(st, S["interpretar_panorama"]())

# ---- 2. Mapas coropléticos ----
with tabs[1]:
    c = st.columns(4)
    m_var = c[0].selectbox("Variable", VARS_MAPA, index=VARS_MAPA.index(VAR0), key="m_var")
    m_anio = c[1].slider("Año", ANIO_MIN, ANIO_MAX, ANIO_MAX, 1, key="m_anio")
    m_pal = c[2].selectbox("Escala cromática", S["PALETAS"], key="m_pal")
    m_dep = c[3].selectbox("Resaltar departamento", ["(ninguno)"] + DEPTOS, key="m_dep")
    recorrer = st.button(f"▶ Recorrer {ANIO_MIN}–{ANIO_MAX}", type="primary", key="m_btn")
    c1, c2 = st.columns([3, 2])
    p_mapa, p_rank, p_txt = c1.empty(), c2.empty(), st.empty()
    anios = [int(a) for a in ANIOS] if recorrer else [m_anio]
    for a in anios:
        fig, rank, txt = S["vista_mapas"](m_var, a, m_pal, sin_ninguno(m_dep))
        grafico(p_mapa, fig, f"m_mapa_{a}" if recorrer else "m_mapa")
        grafico(p_rank, rank, f"m_rank_{a}" if recorrer else "m_rank")
        p_txt.markdown(txt)
        if recorrer:
            time.sleep(PAUSA)

# ---- 3. Relieve 3D ----
with tabs[2]:
    st.markdown("Cada departamento es su **polígono real extruido**: la altura y el color son una transformación "
                "explícita del valor (fórmula debajo). Arrastre para girar, rueda para acercar.")
    c = st.columns(3)
    r_var = c[0].selectbox("Variable", VARS_MAPA, index=VARS_MAPA.index(VAR0), key="r_var")
    r_anio = c[1].slider("Año", ANIO_MIN, ANIO_MAX, ANIO_MAX, 1, key="r_anio")
    r_dep = c[2].selectbox("Resaltar departamento", ["(ninguno)"] + DEPTOS, key="r_dep")
    dinamica = st.button(f"▶ Dinámica temporal {ANIO_MIN}–{ANIO_MAX}", type="primary", key="r_btn")
    p_fig, p_txt = st.empty(), st.empty()
    anios = [int(a) for a in ANIOS] if dinamica and S["VARS_MAPA"][r_var][0] == "panel" else [r_anio]
    for a in anios:
        fig, txt = S["vista_relieve"](r_var, a, sin_ninguno(r_dep))
        grafico(p_fig, fig, f"r_fig_{a}" if dinamica else "r_fig")
        p_txt.markdown(txt)
        if dinamica:
            time.sleep(PAUSA)

# ---- 4. Simulador ----
with tabs[3]:
    c = st.columns(3)
    s_origen = c[0].selectbox("Departamento de origen", DEPTOS, index=DEPTOS.index(ORIGEN0), key="s_origen")
    s_tipo = c[1].selectbox("Tipo de choque", TIPOS, key="s_tipo")
    s_resp = c[2].radio("Respuesta de", RESPUESTAS, index=RESPUESTAS.index(NOMBRES_VAR[dn]), key="s_resp",
                        horizontal=True)
    c = st.columns(3)
    s_mag = c[0].slider("Magnitud (múltiplos de 1 d.e.)", -3.0, 3.0, 1.0, 0.25, key="s_mag")
    s_hz = c[1].slider("Horizonte (años)", 2, 12, HMAX, 1, key="s_hz")
    s_m3 = c[2].radio("Altura del relieve", list(MODOS_3D), key="s_m3")
    s_h = st.slider("Año tras el choque (avanzar / retroceder)", 0, int(s_hz), 0, 1, key="s_h")
    s_btn = st.button("▶ Reproducir", type="primary", key="s_btn")
    args = (s_origen, s_tipo, s_mag, s_hz, s_resp)
    c1, c2 = st.columns(2)
    p_mapa, p_rel = c1.empty(), c2.empty()
    if s_btn:
        for hh in range(int(s_hz) + 1):
            mapa, rel = S["cuadro_sim"](*args, hh, MODOS_3D[s_m3])
            grafico(p_mapa, mapa, f"s_mapa_{hh}")
            grafico(p_rel, rel, f"s_rel_{hh}")
            time.sleep(PAUSA)
    mapa, rel, irf, txt, top = S["vista_simulador"](*args, s_h, MODOS_3D[s_m3])
    if not s_btn:
        grafico(p_mapa, mapa, "s_mapa")
        grafico(p_rel, rel, "s_rel")
    c1, c2 = st.columns([3, 2])
    grafico(c1, irf, "s_irf")
    c2.caption("10 departamentos más afectados (fuera del origen)")
    c2.dataframe(top, use_container_width=True, hide_index=True)
    interp(st, txt)

# ---- 5. ESDA ----
with tabs[4]:
    c = st.columns(3)
    e_var = c[0].selectbox("Variable", VARS_PANEL, key="e_var")
    e_anio = c[1].slider("Año", ANIO_MIN, ANIO_MAX, ANIO_MAX, 1, key="e_anio")
    lista_w = list(S["WS"])
    e_w = c[2].selectbox("Matriz de pesos W", lista_w, index=lista_w.index(S["ELECCION"][up]["W"]), key="e_w")
    moran, lisa, tabla, txt = S["vista_esda"](e_var, e_anio, e_w)
    c1, c2 = st.columns(2)
    grafico(c1, moran, "e_moran")
    grafico(c2, lisa, "e_lisa")
    interp(st, txt)
    st.caption("Autocorrelación espacial global (permutaciones)")
    st.dataframe(tabla, use_container_width=True, hide_index=True)

# ---- 6. Realidad aumentada ----
with tabs[5]:
    st.markdown("Genera una **maqueta 3D (GLB)** con los polígonos extruidos. En móviles compatibles "
                "(WebXR / Scene Viewer / Quick Look) aparece el botón *Ver en realidad aumentada*; en los demás "
                "dispositivos el visor es 3D convencional y así lo indica.")
    c = st.columns(3)
    a_fuente = c[0].radio("Contenido de la maqueta", ["Indicador por año", "Respuesta a un choque"], key="a_fuente")
    a_var = c[1].selectbox("Variable", VARS_MAPA, index=VARS_MAPA.index(VAR0), key="a_var")
    a_anio = c[2].slider("Año", ANIO_MIN, ANIO_MAX, ANIO_MAX, 1, key="a_anio")
    c = st.columns(5)
    a_origen = c[0].selectbox("Origen del choque", DEPTOS, index=DEPTOS.index(ORIGEN0), key="a_origen")
    a_tipo = c[1].selectbox("Tipo de choque", TIPOS, key="a_tipo")
    a_mag = c[2].slider("Magnitud (d.e.)", -3.0, 3.0, 1.0, 0.25, key="a_mag")
    a_resp = c[3].radio("Respuesta de", RESPUESTAS, index=RESPUESTAS.index(NOMBRES_VAR[dn]), key="a_resp")
    a_h = c[4].slider("Año tras el choque", 0, HMAX, 1, 1, key="a_h")
    if st.button("Generar maqueta 3D / RA", type="primary", key="a_btn"):
        ruta, html_visor, _, nota = S["vista_ra"](a_fuente, a_var, a_anio, a_origen, a_tipo, a_mag, a_resp, a_h)
        interp(st, nota)
        if ruta:
            components.html(html_visor, height=620)
            with open(ruta, "rb") as fh:
                st.download_button("Descargar GLB", fh.read(), file_name=os.path.basename(ruta),
                                   mime="model/gltf-binary", key="a_glb")
        else:
            st.markdown(html_visor, unsafe_allow_html=True)

# ---- 7. Modelo SpVAR ----
with tabs[6]:
    p_ec = st.radio("Ecuación", ECUS, index=len(ECUS) - 1, key="p_ec", horizontal=True)
    sel, mec, coef, txt = S["vista_spvar"](p_ec)
    grafico(st, sel, "p_sel")
    c1, c2 = st.columns([3, 2])
    grafico(c1, mec, "p_mec")
    c2.caption("Coeficientes (MV)")
    c2.dataframe(coef, use_container_width=True, hide_index=True)
    interp(st, txt)
    choques = list(S["IRF_PUNTO"])
    p_choque = st.selectbox("Choque agregado (todos los departamentos)", choques, key="p_choque")
    grafico(st, S["fig_irf_agregada"](p_choque), "p_irf")
    st.markdown("""#### Los cuatro mecanismos de transmisión
1. **Autodinámica espacial** — persistencia propia en el tiempo (φ) y su eco en los vecinos (ψ).
2. **Cruce local** — efecto del agro sobre la industria del mismo departamento, contemporáneo (β) y rezagado.
3. **Relación espacial directa** — contagio de la misma variable desde los vecinos (ρ, λ).
4. **Relación espacial cruzada** — el agro de los vecinos mueve la industria propia (θ, ψ cruzado).""")
    if "AUD" in S:
        with st.expander("Auditoría del modelo"):
            st.dataframe(S["AUD"], use_container_width=True, hide_index=True)
    archivos = [os.path.join(CONFIG["OUT_DIR"], f) for f in
                ["resultados_spvar.xlsx", "informe_spvar.md", "auditoria.csv", "mapa_interactivo_spvar.html",
                 "04_mapas_resultados.png", "05_difusion_choque_local.png", "panel_dane.csv"]]
    archivos = [f for f in archivos if os.path.exists(f)]
    if archivos:
        st.markdown("#### Descargar resultados")
        cols = st.columns(min(len(archivos), 4))
        for j, ruta in enumerate(archivos):
            with open(ruta, "rb") as fh:
                cols[j % len(cols)].download_button(os.path.basename(ruta), fh.read(),
                                                    file_name=os.path.basename(ruta), key=f"dl_{j}")

# ---- 8. Interpretabilidad ----
with tabs[7]:
    st.markdown("Texto generado exclusivamente a partir de las estimaciones y estadísticas calculadas. Cada afirmación "
                "indica su tipo de evidencia. Las pestañas de mapas, relieve, simulador, ESDA y modelo incluyen además "
                "su interpretación sincronizada con los controles.")
    x_sec = st.radio("Sección", S["SECCIONES_INTERP"], key="x_sec", horizontal=True)
    interp(st, S["vista_interpretacion"](x_sec))

st.markdown(f"<center style='color:#4d7284'>SpVAR por máxima verosimilitud · selección {CONFIG['CRITERIO']} · "
            f"geometría {S['FUENTE_GEOM']} · Plotly · Streamlit</center>", unsafe_allow_html=True)
