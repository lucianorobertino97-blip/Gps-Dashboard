import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------
# CONFIG
# ----------------------------------
st.set_page_config(page_title="Dashboard GPS", layout="wide")

# ----------------------------------
# CARGA DE DATOS
# ----------------------------------
@st.cache_data
def cargar_datos():
    df = pd.read_excel("carga.xlsx")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

df = cargar_datos()

# ----------------------------------
# FILTROS
# ----------------------------------
st.sidebar.header("Filtros")

# Posición
posiciones = sorted(df["Position Name"].dropna().unique())
posiciones_sel = st.sidebar.multiselect(
    "Posición",
    posiciones,
    default=posiciones
)

# Fechas
fecha_min = df["Fecha"].min().date()
fecha_max = df["Fecha"].max().date()

tipo_fecha = st.sidebar.radio(
    "Selección de fecha",
    ["Una fecha", "Rango de fechas"]
)

if tipo_fecha == "Una fecha":
    fecha_sel = st.sidebar.date_input("Fecha", fecha_min)
    df_filtrado = df[
        (df["Position Name"].isin(posiciones_sel)) &
        (df["Fecha"].dt.date == fecha_sel)
    ]
else:
    fecha_ini, fecha_fin = st.sidebar.date_input(
        "Rango de fechas",
        [fecha_min, fecha_max]
    )
    df_filtrado = df[
        (df["Position Name"].isin(posiciones_sel)) &
        (df["Fecha"].dt.date >= fecha_ini) &
        (df["Fecha"].dt.date <= fecha_fin)
    ]

if df_filtrado.empty:
    st.warning("No hay datos para los filtros seleccionados")
    st.stop()

df_filtrado = df_filtrado.copy()

# ----------------------------------
# MÉTRICAS
# ----------------------------------
df_filtrado["High Intensity Distance"] = (
    df_filtrado["Mts 16-20km/h (m)"] +
    df_filtrado["Mts 20-25.1km/h (m)"] +
    df_filtrado["Mts +25.2km/h (m)"]
)

df_filtrado["High Intensity %"] = (
    df_filtrado["High Intensity Distance"] /
    df_filtrado["Total Distance (m)"]
) * 100

# ----------------------------------
# TABLA SEMÁFORO VELOCIDAD
# ----------------------------------
st.subheader("Velocidad máxima por jugador")

max_vel = df_filtrado["Maximum Velocity (km/h)"].max()
min_vel = df_filtrado["Maximum Velocity (km/h)"].min()

def color_velocidad(val):
    if val >= max_vel * 0.9:
        return "background-color: #2ecc71; color: black"
    elif val <= min_vel * 1.1:
        return "background-color: #e74c3c; color: black"
    else:
        return "background-color: #f1c40f; color: black"

tabla_vel = df_filtrado[[
    "Name",
    "Position Name",
    "Fecha",
    "Maximum Velocity (km/h)"
]].copy()

tabla_vel["Maximum Velocity (km/h)"] = tabla_vel["Maximum Velocity (km/h)"].round(1)

st.dataframe(
    tabla_vel.style.applymap(
        color_velocidad,
        subset=["Maximum Velocity (km/h)"]
    )
)

# ----------------------------------
# EVOLUCIÓN POR JUGADOR
# ----------------------------------
st.subheader("Evolución por jugador")

jugador_sel = st.selectbox(
    "Jugador",
    sorted(df_filtrado["Name"].unique())
)

df_jugador = df_filtrado[df_filtrado["Name"] == jugador_sel]
df_jugador = df_jugador.sort_values("Fecha")

fig, ax = plt.subplots()
ax.plot(
    df_jugador["Fecha"],
    df_jugador["Maximum Velocity (km/h)"],
    marker="o"
)
ax.set_ylabel("Velocidad máxima (km/h)")
ax.set_title(f"Evolución – {jugador_sel}")
plt.xticks(rotation=45)

st.pyplot(fig)

# ----------------------------------
# PROMEDIOS
# ----------------------------------
st.subheader("Promedios")

prom_jugador = df_jugador["Maximum Velocity (km/h)"].mean()
pos_jugador = df_jugador["Position Name"].iloc[0]

prom_posicion = df_filtrado[
    df_filtrado["Position Name"] == pos_jugador
]["Maximum Velocity (km/h)"].mean()

prom_equipo = df_filtrado["Maximum Velocity (km/h)"].mean()

c1, c2, c3 = st.columns(3)
c1.metric("Jugador", f"{prom_jugador:.1f} km/h")
c2.metric("Posición", f"{prom_posicion:.1f} km/h")
c3.metric("Equipo", f"{prom_equipo:.1f} km/h")

# ----------------------------------
# ALERTA DE FATIGA
# ----------------------------------
st.subheader("Alerta de fatiga")

ultima_vel = df_jugador.iloc[-1]["Maximum Velocity (km/h)"]

if ultima_vel < prom_jugador * 0.95:
    st.error("⚠️ Posible fatiga detectada")
else:
    st.success("✅ Rendimiento normal")

# ----------------------------------
# COMPARACIÓN ENTRE JUGADORES
# ----------------------------------
st.subheader("Comparación entre jugadores")

jugadores_comp = st.multiselect(
    "Seleccioná jugadores",
    sorted(df_filtrado["Name"].unique())
)

if len(jugadores_comp) >= 2:
    df_comp = (
        df_filtrado[df_filtrado["Name"].isin(jugadores_comp)]
        .groupby("Name")
        .agg({
            "Total Distance (m)": "mean",
            "High Intensity Distance": "mean",
            "High Intensity %": "mean",
            "Maximum Velocity (km/h)": "mean"
        })
        .reset_index()
    )

    df_comp["Total Distance (m)"] = df_comp["Total Distance (m)"].round(0).astype(int)
    df_comp["High Intensity Distance"] = df_comp["High Intensity Distance"].round(0).astype(int)
    df_comp["High Intensity %"] = df_comp["High Intensity %"].round(1).astype(str) + " %"
    df_comp["Maximum Velocity (km/h)"] = df_comp["Maximum Velocity (km/h)"].round(1)

    st.dataframe(df_comp)

    metrica = st.selectbox(
        "Métrica",
        [
            "Total Distance (m)",
            "High Intensity Distance",
            "Maximum Velocity (km/h)"
        ]
    )

    fig2, ax2 = plt.subplots()
    ax2.bar(df_comp["Name"], df_comp[metrica])
    ax2.set_title(f"Comparación – {metrica}")
    plt.xticks(rotation=45)

    st.pyplot(fig2)
else:
    st.info("Seleccioná al menos dos jugadores")
# =============================
# =============================
# IMPORTS
# =============================
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.patches import FancyBboxPatch
from matplotlib import colors

# =============================
# SELECTOR DE FECHA
# =============================
st.subheader("📅 Selección de fecha")

fechas_disponibles = sorted(
    df_filtrado["Fecha"].dropna().unique()
)

fecha_seleccionada = st.selectbox(
    "Elegí una fecha",
    fechas_disponibles
)

df_fecha = df_filtrado[
    df_filtrado["Fecha"] == fecha_seleccionada
]

st.caption(f"📊 Ranking correspondiente a la fecha: {fecha_seleccionada}")

# =============================
# RANKING – PICOS DE VELOCIDAD
# =============================
st.subheader("🏆 Ranking – Pico máximo de velocidad")

if st.button(
    "📸 Exportar imagen profesional",
    key="export_ranking_velocidad"
):

    # -------------------------
    # DATA: pico máximo por jugador (FECHA)
    # -------------------------
    df_rank = (
        df_fecha
        .groupby("Name", as_index=False)
        .agg({"Maximum Velocity (km/h)": "max"})
        .sort_values("Maximum Velocity (km/h)")
    )

    jugadores = df_rank["Name"].values
    velocidades = df_rank["Maximum Velocity (km/h)"].values

    # -------------------------
    # ESPACIADO COMPACTO
    # -------------------------
    step = 0.42
    y_pos = np.arange(len(jugadores)) * step
    bar_height = 0.36

    # -------------------------
    # COLORES (GRADIENTE)
    # -------------------------
    cmap = colors.LinearSegmentedColormap.from_list(
        "velocidad",
        ["#b11226", "#f1c40f", "#2ecc71"]
    )

    norm = colors.Normalize(
        vmin=velocidades.min(),
        vmax=velocidades.max()
    )

    colores = cmap(norm(velocidades))

    # -------------------------
    # FIGURA
    # -------------------------
    fig_height = max(4, len(jugadores) * 0.25)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))

    fig.patch.set_facecolor("#0e0e0e")
    ax.set_facecolor("#0e0e0e")

    # -------------------------
    # BARRAS REDONDEADAS
    # -------------------------
    for i, (vel, color) in enumerate(zip(velocidades, colores)):
        barra = FancyBboxPatch(
            (0, y_pos[i] - bar_height / 2),
            vel,
            bar_height,
            boxstyle="round,pad=0.02,rounding_size=0.25",
            linewidth=0,
            facecolor=color
        )
        ax.add_patch(barra)

        ax.text(
            vel + 0.15,
            y_pos[i],
            f"{vel:.1f} km/h",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold"
        )

    # -------------------------
    # AJUSTES ANTI-RECORTE
    # -------------------------
    ax.set_yticks(y_pos)
    ax.set_yticklabels(jugadores, fontsize=9, color="white")

    ax.set_xlim(0, velocidades.max() + 1)

    y_min = y_pos.min() - step
    y_max = y_pos.max() + step
    ax.set_ylim(y_min, y_max)

    ax.set_title(
        f"RANKING – PICO MÁXIMO DE VELOCIDAD\n{fecha_seleccionada}",
        fontsize=14,
        fontweight="bold",
        color="white",
        pad=18
    )

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.subplots_adjust(
        left=0.34,
        right=0.97,
        top=0.86,
        bottom=0.08
    )

    # -------------------------
  
    plt.savefig(
        nombre_archivo,
        dpi=260,
        facecolor=fig.get_facecolor(),
        bbox_inches="tight",
        pad_inches=0.25
    )

    plt.close()

    st.success("✅ Imagen exportada correctamente")
    st.image(nombre_archivo)
# =============================


# -------------------------
# DATA: pico máximo por jugador (FECHA)
# -------------------------
df_rank = (
    df_fecha
    .groupby("Name", as_index=False)
    .agg({"Maximum Velocity (km/h)": "max"})
    .sort_values("Maximum Velocity (km/h)")
)

jugadores = df_rank["Name"].values
velocidades = df_rank["Maximum Velocity (km/h)"].values

# -------------------------
# ESPACIADO COMPACTO
# -------------------------
step = 0.42
y_pos = np.arange(len(jugadores)) * step
bar_height = 0.36

# -------------------------
# COLORES (GRADIENTE)
# -------------------------
cmap = colors.LinearSegmentedColormap.from_list(
    "velocidad",
    ["#b11226", "#f1c40f", "#2ecc71"]
)

norm = colors.Normalize(
    vmin=velocidades.min(),
    vmax=velocidades.max()
)

colores = cmap(norm(velocidades))

# -------------------------
# FUNCIÓN DE DIBUJO
# -------------------------
def dibujar_ranking(exportar=False):

    fig_height = max(4, len(jugadores) * 0.25)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))

    fig.patch.set_facecolor("#0e0e0e")
    ax.set_facecolor("#0e0e0e")

    for i, (vel, color) in enumerate(zip(velocidades, colores)):
        barra = FancyBboxPatch(
            (0, y_pos[i] - bar_height / 2),
            vel,
            bar_height,
            boxstyle="round,pad=0.02,rounding_size=0.25",
            linewidth=0,
            facecolor=color
        )
        ax.add_patch(barra)

        ax.text(
            vel + 0.15,
            y_pos[i],
            f"{vel:.1f} km/h",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold"
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(jugadores, fontsize=9, color="white")

    ax.set_xlim(0, velocidades.max() + 1)

    ax.set_ylim(
        y_pos.min() - step,
        y_pos.max() + step
    )

    ax.set_title(
        f"RANKING – PICO MÁXIMO DE VELOCIDAD\n{fecha_seleccionada}",
        fontsize=14,
        fontweight="bold",
        color="white",
        pad=18
    )

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.subplots_adjust(
        left=0.34,
        right=0.97,
        top=0.86,
        bottom=0.08
    )

    if exportar:
        fecha_str = str(fecha_seleccionada).replace("/", "-")
        nombre_archivo = f"ranking_picos_velocidad_{fecha_str}.png"

        plt.savefig(
            nombre_archivo,
            dpi=260,
            facecolor=fig.get_facecolor(),
            bbox_inches="tight",
            pad_inches=0.25
        )

        plt.close()
        return nombre_archivo

    return fig


# -------------------------
# MOSTRAR RANKING EN PANTALLA
# -------------------------
fig = dibujar_ranking(exportar=False)
st.pyplot(fig)

# -------------------------
# BOTÓN EXPORTAR
# -------------------------
if st.button(
    "📸 Exportar Ranking Picos de velocidad",
    key=f"export_ranking_{fecha_seleccionada}"
):
    archivo = dibujar_ranking(exportar=True)
    st.success("✅ Imagen exportada correctamente")
    st.image(archivo)
# =============================
# RANKING – VELOCIDAD MEDIA TOTAL
# =============================
st.subheader("📊 Ranking – Velocidad media")

# -------------------------
# DATA: MEDIA TOTAL POR JUGADOR
# -------------------------
df_media = (
    df_filtrado
    .groupby("Name", as_index=False)
    .agg({"Maximum Velocity (km/h)": "mean"})
    .rename(columns={
        "Maximum Velocity (km/h)": "Velocidad media (km/h)"
    })
    .sort_values("Velocidad media (km/h)")
)

jugadores = df_media["Name"].values
velocidades = df_media["Velocidad media (km/h)"].values

# -------------------------
# ESPACIADO COMPACTO
# -------------------------
step = 0.42
y_pos = np.arange(len(jugadores)) * step
bar_height = 0.36

# -------------------------
# COLORES (GRADIENTE)
# -------------------------
cmap = colors.LinearSegmentedColormap.from_list(
    "velocidad_media",
    ["#b11226", "#f1c40f", "#2ecc71"]
)

norm = colors.Normalize(
    vmin=velocidades.min(),
    vmax=velocidades.max()
)

colores = cmap(norm(velocidades))

# -------------------------
# FUNCIÓN DE DIBUJO
# -------------------------
def dibujar_ranking_media_total(exportar=False):

    fig_height = max(4, len(jugadores) * 0.25)
    fig, ax = plt.subplots(figsize=(9.5, fig_height))

    fig.patch.set_facecolor("#0e0e0e")
    ax.set_facecolor("#0e0e0e")

    for i, (vel, color) in enumerate(zip(velocidades, colores)):
        barra = FancyBboxPatch(
            (0, y_pos[i] - bar_height / 2),
            vel,
            bar_height,
            boxstyle="round,pad=0.02,rounding_size=0.25",
            linewidth=0,
            facecolor=color
        )
        ax.add_patch(barra)

        ax.text(
            vel + 0.15,
            y_pos[i],
            f"{vel:.1f} km/h",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold"
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(jugadores, fontsize=9, color="white")

    ax.set_xlim(0, velocidades.max() + 1)

    ax.set_ylim(
        y_pos.min() - step,
        y_pos.max() + step
    )

    ax.set_title(
        "RANKING – VELOCIDAD MEDIA",
        fontsize=14,
        fontweight="bold",
        color="white",
        pad=18
    )

    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    plt.subplots_adjust(
        left=0.34,
        right=0.97,
        top=0.86,
        bottom=0.08
    )

    if exportar:
        nombre_archivo = "ranking_velocidad_media_total.png"

        plt.savefig(
            nombre_archivo,
            dpi=260,
            facecolor=fig.get_facecolor(),
            bbox_inches="tight",
            pad_inches=0.25
        )

        plt.close()
        return nombre_archivo

    return fig


# -------------------------
# MOSTRAR RANKING
# -------------------------
fig = dibujar_ranking_media_total(exportar=False)
st.pyplot(fig)

# -------------------------
# EXPORTAR IMAGEN
# -------------------------
if st.button(
    "📸 Exportar imagen – Velocidad media total",
    key="export_vel_media_total"
):
    archivo = dibujar_ranking_media_total(exportar=True)
    st.success("✅ Imagen exportada correctamente")
    st.image(archivo)
