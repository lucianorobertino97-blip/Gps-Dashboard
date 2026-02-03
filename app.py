import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px


from matplotlib.patches import FancyBboxPatch
from matplotlib import colors

def kpi_card(titulo, valor, unidad, ratio):
    st.markdown(f"""
    <div style="
        background: linear-gradient(145deg,#111,#1a1a1a);
        padding:20px;
        border-radius:18px;
        box-shadow: 0 6px 18px rgba(0,0,0,0.5);
        margin-bottom:12px;
    ">
        <div style="color:#9aa0a6; font-size:14px; margin-bottom:6px;">
            {titulo}
        </div>
        <div style="color:white; font-size:34px; font-weight:700;">
            {valor} {unidad}
        </div>
        <div style="background:#222; border-radius:10px; height:8px; margin-top:12px;">
            <div style="
                width:{min(ratio*100,100)}%;
                background:#1f77ff;
                height:100%;
                border-radius:10px;">
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
# ==================================
# CARGA DE DATOS DESDE GOOGLE SHEETS
# ==================================
@st.cache_data
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/1rkV1FOM8cLz6jJ1OotB6pUWIyzSoYcrPa6rubqn3aX8/export?format=xlsx"
    
    df = pd.read_excel(url, sheet_name=0)          # Hoja principal (GPS)
    Baselines = pd.read_excel(url, sheet_name=1)   # Hoja 2 (Baselines)

    df["Fecha"] = pd.to_datetime(df["Fecha"])
    
    return df, Baselines

df, Baselines = cargar_datos()

# ==================================
# VARIABLES DERIVADAS
# ==================================
df["High Speed Running (m)"] = (
    df["Mts 20-25.1km/h (m)"] +
    df["Mts +25.2km/h (m)"]
)

import os

def obtener_foto_jugador(nombre):
    carpeta = "fotos_jugadores"
    extensiones = [".png", ".jpg", ".jpeg"]

    for ext in extensiones:
        ruta = os.path.join(carpeta, f"{nombre}{ext}")
        if os.path.exists(ruta):
            return ruta
    return None

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

    vel_pico = df_j["Maximum Velocity (km/h)"].max()
    dist_media = df_j["Total Distance (m)"].mean()
    hsr_media = df_j["High Speed Running (m)"].mean()

    # COLUMNAS PRINCIPALES
    col_img, col_stats = st.columns([1,3], vertical_alignment="center")

    # FOTO
    with col_img:
        foto = obtener_foto_jugador(jugador_sel)
        if foto:
            st.image(foto, width=260)   # ⚠️ NO usar use_container_width
        else:
            st.info("Sin foto del jugador")

    # BARRAS KPI
    with col_stats:

        st.markdown(f"## {jugador_sel}")

        def barra_kpi(titulo, valor, maximo, unidad):
            progreso = min(valor / maximo, 1)

            st.markdown(f"""
            <div style="margin-bottom:22px">
                <div style="font-size:14px; opacity:0.8">{titulo}</div>
                <div style="font-size:28px; font-weight:700">{valor:.1f} {unidad}</div>
                <div style="height:6px;background:#222;border-radius:6px;margin-top:6px;">
                    <div style="width:{progreso*100}%;height:6px;
                        background:linear-gradient(90deg,#00c6ff,#0072ff);
                        border-radius:6px;">
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        barra_kpi("Velocidad pico histórica", vel_pico, 36, "km/h")
        barra_kpi("Distancia media", dist_media, 12000, "m")
        barra_kpi("HSR medio (>20 km/h)", hsr_media, 600, "m")


    st.subheader("Semáforo por microciclo en base a referencia")

    # Baseline del jugador
    base_j = Baselines[Baselines["Name"] == jugador_sel]

    if base_j.empty:
     st.warning("Este jugador no tiene baseline cargado")
    else:
     acc_base = base_j["Acc Mts 2-4 m/ss T"].values[0]
     dec_base = base_j["Decc Mts 2-4m/ss T"].values[0]

    # 👉 SUMA POR MICROCICLO
    micro_df = (
        df[df["Name"] == jugador_sel]
        .groupby("Micro", as_index=False)
        .agg({
            "Acc Mts 2-4 m/ss": "sum",
            "Acc Mts + 4m/ss (m)": "sum",
            "Decc Mts 2-4m/ss": "sum",
            "Decc Mts+4m/ss": "sum"
        })
    )

    # Totales del micro
    micro_df["Acc Micro"] = micro_df["Acc Mts 2-4 m/ss"] + micro_df["Acc Mts + 4m/ss (m)"]
    micro_df["Dec Micro"] = micro_df["Decc Mts 2-4m/ss"] + micro_df["Decc Mts+4m/ss"]

    # % contra su micro 100
    micro_df["Acc %"] = micro_df["Acc Micro"] / acc_base * 100
    micro_df["Dec %"] = micro_df["Dec Micro"] / dec_base * 100

    # FUNCIÓN SEMÁFORO
    def semaforo(x):
        if x >= 100:
            return "🟢 Alto"
        elif x >= 90:
            return "🟡 Normal"
        else:
            return "🔴 Bajo"

    micro_df["Estado Acc"] = micro_df["Acc %"].apply(semaforo)
    micro_df["Estado Dec"] = micro_df["Dec %"].apply(semaforo)

    st.dataframe(
        micro_df[[
            "Micro",
            "Acc Micro",
            "Acc %",
            "Estado Acc",
            "Dec Micro",
            "Dec %",
            "Estado Dec"
        ]].round(1),
        use_container_width=True
    )
    # HIGH SPEED RUNNING (>20 km/h)
    # =========================
    df_j["High Speed Running (m)"] = (
    df_j["Mts 20-25.1km/h (m)"] +
    df_j["Mts +25.2km/h (m)"]
    )

    
    

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
        title=f"Velocidad maxima – {jugador_sel}",
        yaxis_title="Velocidad máxima (km/h)",
        xaxis_title="Fecha",
        hovermode="closest"
    )

    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # ⚡ ACELERACIONES
    # =========================
    st.subheader("⚡ – Aceleraciones")

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
    # =========================
    # 🏃‍♂️ HIGH SPEED RUNNING
    # =========================
    st.subheader("🏃‍♂️ – High Speed Running")

    fig_hsr = go.Figure()

    fig_hsr.add_trace(go.Scatter(
    x=df_j["Fecha"],
    y=df_j["High Speed Running (m)"],
    mode="lines+markers",
    name="HSR >20 km/h",
    hovertemplate=
        "<b>Fecha:</b> %{x}<br>" +
        "<b>HSR:</b> %{y:,.0f} m<extra></extra>"
      ))

    fig_hsr.update_layout(
    title=f"High Speed Running – {jugador_sel}",
    xaxis_title="Fecha",
    yaxis_title="Metros >20 km/h",
    hovermode="closest"
     )

    st.plotly_chart(fig_hsr, use_container_width=True)

# PROMEDIOS EQUIPO
# ==================================
with tab_equipo:
    st.subheader("📌 Promedios del equipo")
    c1, c2, c3 = st.columns(3)

    with c1:
     st.markdown(f"""
    <div class="kpi-card kpi-green">
        <div class="kpi-title">Velocidad media</div>
        <div class="kpi-value">{df['Maximum Velocity (km/h)'].mean():.1f} km/h</div>
    </div>
    """, unsafe_allow_html=True)

    with c2:
     st.markdown(f"""
    <div class="kpi-card kpi-red">
        <div class="kpi-title">Pico máximo</div>
        <div class="kpi-value">{df['Maximum Velocity (km/h)'].max():.1f} km/h</div>
    </div>
    """, unsafe_allow_html=True)

    with c3:
      st.markdown(f"""
    <div class="kpi-card kpi-blue">
        <div class="kpi-title">Distancia media</div>
        <div class="kpi-value">{df['Total Distance (m)'].mean():.0f} m</div>
    </div>
    """, unsafe_allow_html=True)

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
