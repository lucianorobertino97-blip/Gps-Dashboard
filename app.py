import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


from matplotlib.patches import FancyBboxPatch
from matplotlib import colors

# ==================================
# CONFIG
# ==================================
st.set_page_config(
    page_title="GPS Club Atletico Colon",
    layout="wide"
)

col1, col2 = st.columns([1, 6])

with col1:
    st.image("escudo_colon.png", width=120)

with col2:
    st.markdown(
        "<h1 style='margin-bottom:0;'>GPS Club Atlético Colón</h1>",
        unsafe_allow_html=True
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
# SIDEBAR
# ==================================
st.sidebar.header("Filtros")

if st.sidebar.button("🔄 Actualizar datos"):
    st.cache_data.clear()
    st.rerun()

posiciones = sorted(df["Position Name"].dropna().unique())
posiciones_sel = st.sidebar.multiselect(
    "Posición",
    posiciones,
    default=posiciones
)

df = df[df["Position Name"].isin(posiciones_sel)].copy()

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

# ==================================
# BIENVENIDA
# ==================================
with tab_bienvenida:
    st.markdown("""
    ### 👋 Bienvenido

    Dashboard de análisis **GPS profesional**.

    - Rankings de velocidad
    - Evolución individual
    - Comparativas
    - Indicadores de carga y fatiga

    👉 Entrá en **Empezar análisis** para comenzar.
    """)

# ==================================
# EMPEZAR
# ==================================
with tab_inicio:
    st.markdown("""
    ### ▶️ Empezar análisis

    - Elegí posiciones desde el panel izquierdo
    - Navegá por las pestañas
    - Exportá rankings cuando lo necesites

    ℹ️ Todos los análisis usan **todas las fechas**  
    excepto el **ranking de pico**, que se elige por fecha.
    """)

# ==================================
# RANKING PICO (POR FECHA)
# ==================================
with tab_pico:

    st.subheader("🏆 Ranking – Pico máximo de velocidad")

    fechas = sorted(df["Fecha"].unique())
    fecha_sel = st.selectbox("Seleccioná una fecha", fechas)

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
        "velocidad", ["#b11226", "#f1c40f", "#2ecc71"]
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

    st.pyplot(dibujar_ranking_pico())

    if st.button("📸 Exportar ranking pico"):
        archivo = dibujar_ranking_pico(exportar=True)
        st.success("Imagen exportada")
        st.image(archivo)

# ==================================
# VELOCIDAD MEDIA (TODAS LAS FECHAS)
# ==================================
with tab_media:
    st.subheader("📊 Velocidad media (todas las fechas)")

    df_media = (
        df.groupby("Name", as_index=False)
        .agg({"Maximum Velocity (km/h)": "mean"})
        .rename(columns={"Maximum Velocity (km/h)": "Velocidad media (km/h)"})
        .sort_values("Velocidad media (km/h)")
    )

    st.dataframe(df_media.round(1))

# ==================================
# ==================================
# EVOLUCIÓN + FATIGA
# ==================================
with tab_evolucion:

    st.subheader("📈 Evolución individual")

    jugador_sel = st.selectbox("Jugador", sorted(df["Name"].unique()))
    df_j = df[df["Name"] == jugador_sel].sort_values("Fecha")

    # -------------------------
    # VELOCIDAD MÁXIMA
    # -------------------------
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_j["Fecha"],
        y=df_j["Maximum Velocity (km/h)"],
        mode="lines+markers",
        name="Velocidad máxima",
        hovertemplate=
            "<b>Fecha:</b> %{x}<br>" +
            "<b>Velocidad:</b> %{y:.1f} km/h<extra></extra>"
    ))

    fig.update_layout(
        title=f"Evolución individual – {jugador_sel}",
        yaxis_title="Velocidad máxima (km/h)",
        xaxis_title="Fecha",
        hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # ⚡ ACELERACIONES
    # =========================
    st.subheader("⚡ Evolución individual – Aceleraciones")

    fig_acc = go.Figure()

    # Acc 2–4 m/s²
    fig_acc.add_trace(go.Scatter(
        x=df_j["Fecha"],
        y=df_j["Acc Mts 2-4 m/ss"],
        mode="lines+markers",
        name="Acc 2–4 m/s²",
        hovertemplate=
            "<b>Fecha:</b> %{x}<br>" +
            "<b>Metros:</b> %{y:.1f} m<extra></extra>"
    ))

    # Acc +4 m/s²
    fig_acc.add_trace(go.Scatter(
        x=df_j["Fecha"],
        y=df_j["Acc Mts + 4m/ss (m)"],
        mode="lines+markers",
        name="Acc +4 m/s²",
        hovertemplate=
            "<b>Fecha:</b> %{x}<br>" +
            "<b>Metros:</b> %{y:.1f} m<extra></extra>"
    ))

    fig_acc.update_layout(
        title=f"Aceleraciones – {jugador_sel}",
        xaxis_title="Fecha",
        yaxis_title="Metros en aceleración",
        hovermode="closest",
        legend_title="Tipo de aceleración"
    )

    st.plotly_chart(fig_acc, use_container_width=True)


# ==================================
# COMPARATIVA (INTERACTIVA)
# ==================================
with tab_comp:

    st.subheader("👥 Comparativa entre jugadores")

    jugadores_sel = st.multiselect(
        "Jugadores",
        sorted(df["Name"].unique())
    )

    if len(jugadores_sel) < 2:
        st.info("Seleccioná al menos 2 jugadores para comparar")
        st.stop()

    # =========================================
    # 🏃‍♂️ COMPARATIVA – VELOCIDAD PICO
    # =========================================
    df_vel = (
        df[df["Name"].isin(jugadores_sel)]
        .groupby("Name", as_index=False)
        .agg({
            "Maximum Velocity (km/h)": "max"
        })
    )

    fig_vel = px.bar(
        df_vel,
        x="Name",
        y="Maximum Velocity (km/h)",
        text_auto=".1f",
        title="🏃‍♂️ Pico de velocidad por jugador",
        labels={
            "Name": "Jugador",
            "Maximum Velocity (km/h)": "Velocidad máxima (km/h)"
        }
    )

    fig_vel.update_traces(
        hovertemplate=
        "Jugador: %{x}<br>" +
        "Velocidad pico: %{y:.1f} km/h"
    )

    fig_vel.update_layout(
        hovermode="x unified",
        yaxis_title="km/h"
    )

    st.plotly_chart(fig_vel, use_container_width=True)

    # =========================================
    # ⚡ COMPARATIVA – ACELERACIONES
    # =========================================
    df_acc = (
        df[df["Name"].isin(jugadores_sel)]
        .groupby("Name", as_index=False)
        .agg({
            "Acc Mts 2-4 m/ss": "sum",
            "Acc Mts + 4m/ss (m)": "sum"
        })
    )

    fig_acc = go.Figure()

    fig_acc.add_bar(
        x=df_acc["Name"],
        y=df_acc["Acc Mts 2-4 m/ss"],
        name="Acc 2–4 m/s²",
        hovertemplate=
        "Jugador: %{x}<br>" +
        "Acc 2–4 m/s²: %{y:.0f} m"
    )

    fig_acc.add_bar(
        x=df_acc["Name"],
        y=df_acc["Acc Mts + 4m/ss (m)"],
        name="Acc +4 m/s²",
        hovertemplate=
        "Jugador: %{x}<br>" +
        "Acc +4 m/s²: %{y:.0f} m"
    )

    fig_acc.update_layout(
        title="⚡ Metros en aceleración",
        barmode="group",
        xaxis_title="Jugador",
        yaxis_title="Metros",
        hovermode="x unified"
    )

    st.plotly_chart(fig_acc, use_container_width=True)
    
        # =========================================
    
      # =========================================
    # 🏃‍♂️ EVOLUCIÓN – TOTAL DISTANCE (POR FECHA)
    # =========================================

    df_dist = (
        df[df["Name"].isin(jugadores_sel)]
        .sort_values("Fecha")
    )

    fig_dist = px.line(
        df_dist,
        x="Fecha",
        y="Total Distance (m)",
        color="Name",
        markers=True,
        title="📈 Evolución de la distancia total por jugador",
        labels={
            "Fecha": "Fecha",
            "Total Distance (m)": "Distancia total (m)",
            "Name": "Jugador"
        }
    )

    fig_dist.update_traces(
        hovertemplate=
        "Jugador: %{legendgroup}<br>" +
        "Fecha: %{x}<br>" +
        "Distancia: %{y:,.0f} m"
    )

    fig_dist.update_layout(
        hovermode="x unified",
        yaxis_title="Metros"
    )

    st.plotly_chart(fig_dist, use_container_width=True)


# ==================================
# PROMEDIOS EQUIPO
# ==================================
with tab_equipo:
    st.subheader("📌 Promedios del equipo")

    c1, c2, c3 = st.columns(3)

    c1.metric("Velocidad media",
              f"{df['Maximum Velocity (km/h)'].mean():.1f} km/h")

    c2.metric("Pico máximo",
              f"{df['Maximum Velocity (km/h)'].max():.1f} km/h")

    c3.metric("Distancia media",
              f"{df['Total Distance (m)'].mean():.0f} m")
