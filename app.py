import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from matplotlib.patches import FancyBboxPatch
from matplotlib import colors

# ==================================
# CONFIG
# ==================================
st.set_page_config(
    page_title="Dashboard GPS",
    layout="wide"
)

# ==================================
# CARGA DE DATOS
# ==================================
@st.cache_data
def cargar_datos():
    df = pd.read_excel("carga.xlsx")
    df["Fecha"] = pd.to_datetime(df["Fecha"])
    return df

df = cargar_datos()

# ==================================
# SIDEBAR – FILTRO POSICIÓN
# ==================================
st.sidebar.header("Filtros")

posiciones = sorted(df["Position Name"].dropna().unique())
posiciones_sel = st.sidebar.multiselect(
    "Posición",
    posiciones,
    default=posiciones
)

df = df[df["Position Name"].isin(posiciones_sel)].copy()

# ==================================
# TÍTULO
# ==================================
st.title("📊 Dashboard GPS")

# ==================================
# PESTAÑAS
# ==================================
tab_bienvenida, tab_inicio, tab_pico, tab_media, tab_evolucion, tab_comp, tab_equipo = st.tabs([
    "👋 Bienvenida",
    "▶️ Empezar análisis",
    "🏆 Pico de velocidad",
    "📊 Velocidad media",
    "📈 Evolución individual",
    "👥 Comparativa",
    "📌 Promedios equipo"
])

# ======================================================
# BIENVENIDA
# ======================================================
with tab_bienvenida:
    st.markdown(
        """
        ### 👋 Bienvenido al Dashboard GPS

        Esta herramienta está diseñada para **analizar el rendimiento físico**
        de los jugadores a partir de datos GPS.

        #### ¿Qué vas a encontrar?
        - Rankings de velocidad máxima y media  
        - Evolución individual por jugador  
        - Comparaciones entre jugadores  
        - Alertas de fatiga  
        - Promedios generales del equipo  

        👉 Usá la pestaña **Empezar análisis** para comenzar.
        """
    )

# ======================================================
# EMPEZAR ANÁLISIS
# ======================================================
with tab_inicio:
    st.markdown(
        """
        ### ▶️ Empezar análisis

        1️⃣ Seleccioná las **posiciones** desde el panel lateral  
        2️⃣ Ingresá a la pestaña del análisis que quieras  
        3️⃣ Exportá rankings si lo necesitás  

        💡 Todos los análisis (excepto el ranking pico) se calculan
        **con todas las fechas disponibles**.
        """
    )

# ======================================================
# TAB – RANKING PICO DE VELOCIDAD (POR FECHA)
# ======================================================
with tab_pico:

    st.subheader("🏆 Ranking – Pico máximo de velocidad")

    fechas_disponibles = sorted(df["Fecha"].unique())
    fecha_sel = st.selectbox("Seleccioná una fecha", fechas_disponibles)

    df_fecha = df[df["Fecha"] == fecha_sel]

    df_rank = (
        df_fecha
        .groupby("Name", as_index=False)
        .agg({"Maximum Velocity (km/h)": "max"})
        .sort_values("Maximum Velocity (km/h)")
    )

    jugadores = df_rank["Name"].values
    velocidades = df_rank["Maximum Velocity (km/h)"].values

    step = 0.42
    y_pos = np.arange(len(jugadores)) * step
    bar_height = 0.36

    cmap = colors.LinearSegmentedColormap.from_list(
        "velocidad",
        ["#b11226", "#f1c40f", "#2ecc71"]
    )

    norm = colors.Normalize(
        vmin=velocidades.min(),
        vmax=velocidades.max()
    )

    colores = cmap(norm(velocidades))

    def dibujar_ranking_pico(exportar=False):
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

        ax.set_xlim(0, velocidades.max() * 1.08)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(jugadores, fontsize=9, color="white")

        ax.set_ylim(y_pos.min() - step, y_pos.max() + step)

        ax.set_title(
            f"RANKING – PICO MÁXIMO DE VELOCIDAD\n{fecha_sel.date()}",
            fontsize=14,
            fontweight="bold",
            color="white",
            pad=18
        )

        ax.tick_params(axis="x", colors="white")
        ax.tick_params(axis="y", length=0)

        for spine in ax.spines.values():
            spine.set_visible(False)

        plt.subplots_adjust(left=0.33, right=0.97, top=0.88, bottom=0.08)

        if exportar:
            nombre = f"ranking_pico_velocidad_{fecha_sel.date()}.png"
            plt.savefig(
                nombre,
                dpi=260,
                facecolor=fig.get_facecolor(),
                bbox_inches="tight",
                pad_inches=0.25
            )
            plt.close()
            return nombre

        return fig

    fig = dibujar_ranking_pico()
    st.pyplot(fig)

    if st.button("📸 Exportar ranking pico"):
        archivo = dibujar_ranking_pico(exportar=True)
        st.success("Imagen exportada")
        st.image(archivo)

# ======================================================
# TAB – VELOCIDAD MEDIA (TODAS LAS FECHAS)
# ======================================================
with tab_media:

    st.subheader("📊 Ranking – Velocidad media (todas las fechas)")

    df_media = (
        df
        .groupby("Name", as_index=False)
        .agg({"Maximum Velocity (km/h)": "mean"})
        .rename(columns={"Maximum Velocity (km/h)": "Velocidad media (km/h)"})
        .sort_values("Velocidad media (km/h)")
    )

    st.dataframe(df_media.round(1))

# ======================================================
# TAB – EVOLUCIÓN + FATIGA
# ======================================================
with tab_evolucion:

    st.subheader("📈 Evolución individual")

    jugador_sel = st.selectbox("Jugador", sorted(df["Name"].unique()))

    df_jugador = df[df["Name"] == jugador_sel].sort_values("Fecha")

    fig, ax = plt.subplots()
    ax.plot(df_jugador["Fecha"], df_jugador["Maximum Velocity (km/h)"], marker="o")
    ax.set_ylabel("Velocidad máxima (km/h)")
    ax.set_title(jugador_sel)
    plt.xticks(rotation=45)

    st.pyplot(fig)

    prom = df_jugador["Maximum Velocity (km/h)"].mean()
    ultima = df_jugador.iloc[-1]["Maximum Velocity (km/h)"]

    if ultima < prom * 0.95:
        st.error("⚠️ Posible fatiga detectada")
    else:
        st.success("✅ Rendimiento normal")

# ======================================================
# TAB – COMPARATIVA
# ======================================================
with tab_comp:

    st.subheader("👥 Comparativa entre jugadores")

    jugadores_sel = st.multiselect("Jugadores", sorted(df["Name"].unique()))

    if len(jugadores_sel) >= 2:
        df_comp = (
            df[df["Name"].isin(jugadores_sel)]
            .groupby("Name")
            .agg({"Maximum Velocity (km/h)": "mean"})
            .reset_index()
        )

        st.dataframe(df_comp.round(1))

# ======================================================
# TAB – PROMEDIOS EQUIPO
# ======================================================
with tab_equipo:

    st.subheader("📌 Promedios del equipo")

    c1, c2 = st.columns(2)

    c1.metric(
        "Velocidad media equipo",
        f"{df['Maximum Velocity (km/h)'].mean():.1f} km/h"
    )

    c2.metric(
        "Pico máximo equipo",
        f"{df['Maximum Velocity (km/h)'].max():.1f} km/h"
    )
