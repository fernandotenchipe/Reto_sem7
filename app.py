import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(page_title='Spotify Pop Dashboard', layout='wide')

# ==========================================
# 2. CARGAR CSS (ESTILO SPOTIFY)
# ==========================================
custom_css = """
.stApp { background-color: #121212; }
p, label, span, div, li { color: #FFFFFF !important; }
h1, h2, h3, .stHeading, div[data-testid="stMarkdownContainer"] h1, div[data-testid="stMarkdownContainer"] h2, div[data-testid="stMarkdownContainer"] h3 {
    color: #1DB954 !important;
}
[data-testid="stSidebar"] { background-color: #000000 !important; border-right: 1px solid #1DB954; }
hr { border-color: #1DB954 !important; }
[data-testid="stMetricValue"] { color: #1DB954 !important; }
.stMultiSelect span { color: #000000 !important; }
"""
st.markdown(f"<style>{custom_css}</style>", unsafe_allow_html=True)

# ==========================================
# 2.1. FUNCIÓN GLOBAL PARA ESTILO PLOTLY
# ==========================================
def apply_plotly_theme(fig):
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white")
    )
    return fig

# ==========================================
# 3. CARGAR DATOS
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("datasetspotify.csv")
        if "Unnamed: 0" in df.columns:
            df = df.drop(columns=["Unnamed: 0"])

        df["artists"] = df["artists"].astype(str)
        df["track_genre"] = df["track_genre"].astype(str)
        df["duration_min"] = df["duration_ms"] / 60000
        df["track_name"] = df["track_name"].astype(str)

        # Filtro base: Solo géneros que contengan "pop"
        df = df[df["track_genre"].str.contains("pop", case=False, na=False)].copy()
        return df
    except:
        return pd.DataFrame()

df = load_data()

# ==========================================
# 4. SIDEBAR (BARRA LATERAL)
# ==========================================
with st.sidebar:
    st.title("🎧 Configuración")
    st.markdown("---")

    st.header("Filtros Generales")
    # 1. Filtro Global
    min_pop = st.slider("Popularidad mínima", 0, 100, 0)

    st.markdown("---")
    st.caption("Datos procesados de Spotify.")

# ==========================================
# 5. PÁGINA PRINCIPAL
# ==========================================
st.title('Dashboard de análisis del Pop - Spotify')

if not df.empty:
    # --- FILTRO GLOBAL (POPULARIDAD) ---
    # df_global se usa como base para todos los tabs
    df_global = df[df["popularity"] >= min_pop]

    # MÉTRICAS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Artistas", df_global["artists"].nunique())
    c2.metric("Duración Media", f"{df_global['duration_min'].mean():.2f} min")
    c3.metric("Subgéneros Totales", df_global["track_genre"].nunique())
    c4.metric("Total Canciones", len(df_global))

    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Duración por Subgénero",
        "Distribución de Duración",
        "Popularidad por Subgénero",
        "Impacto Explícito",
        "Resumen"
    ])

    # TAB 1
    with tab1:
        st.subheader("Duración por Subgénero (General)")
        col_a, col_b = st.columns(2)
        top_n = col_b.selectbox("Mostrar Top", [5, 10, 15], index=0, key="tab1_top")

        data_g1 = (
            df_global.groupby("track_genre")["duration_min"]
            .mean()
            .reset_index()
            .sort_values("duration_min", ascending=False)
            .head(top_n)
        )

        fig1 = px.bar(
            data_g1,
            x="duration_min",
            y="track_genre",
            orientation='h',
            color_discrete_sequence=["#1DB954"]
        )
        fig1 = apply_plotly_theme(fig1)
        st.plotly_chart(fig1, use_container_width=True)

    # TAB 2
    with tab2:
        st.subheader("Distribución de Duración (General)")
        fig2 = px.histogram(
            df_global[df_global["duration_min"] <= 15],
            x="duration_min",
            nbins=30,
            color_discrete_sequence=["#1DB954"]
        )
        fig2 = apply_plotly_theme(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    # TAB 3
    with tab3:
        st.subheader("Popularidad por Subgénero (General)")
        data_g3 = (
            df_global.groupby("track_genre")["popularity"]
            .mean()
            .reset_index()
            .sort_values("popularity", ascending=False)
            .head(10)
        )

        fig3 = px.line(
            data_g3,
            x="track_genre",
            y="popularity",
            markers=True,
            color_discrete_sequence=["#1DB954"]
        )
        fig3 = apply_plotly_theme(fig3)
        st.plotly_chart(fig3, use_container_width=True)

    # TAB 4
    with tab4:
        st.subheader("Impacto del Contenido Explícito en Popularidad")

        # --- CONTROLES LOCALES ---
        col_filter_1, col_filter_2 = st.columns([3, 1])  # Una columna ancha y una vacía para espaciado

        with col_filter_1:
            # Obtenemos géneros disponibles
            available_genres = sorted(df["track_genre"].unique())
            selected_genres = st.multiselect(
                "Selecciona los Subgéneros a comparar:",
                options=available_genres,
                default=[],
                key="tab4_multiselect",  
                help="Deja vacío para ver todos los géneros."
            )

        # --- LÓGICA DE FILTRADO  ---
        if selected_genres:
            df_box = df_global[df_global["track_genre"].isin(selected_genres)]
        else:
            df_box = df_global

        # --- GRÁFICA ---
        if not df_box.empty:
            df_box_plot = df_box.copy()
            df_box_plot["explicit_label"] = df_box_plot["explicit"].map(
                {True: "Explícito", False: "Apto (Clean)"}
            )

            fig4 = px.box(
                df_box_plot,
                x="explicit_label",
                y="popularity",
                color="explicit_label",
                points="outliers",
                color_discrete_map={"Explícito": "#1DB954", "Apto (Clean)": "#B3B3B3"}
            )

            fig4 = apply_plotly_theme(fig4)
            fig4.update_layout(
                xaxis_title="Tipo de Contenido",
                yaxis_title="Popularidad (0-100)",
                showlegend=False
            )

            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.warning("No hay datos que coincidan con los filtros seleccionados.")
            
    with tab5:

        st.subheader("Popularidad")
        col_a2, col_b2 = st.columns(2)
        top_n2 = col_b2.selectbox("Mostrar Top", [5, 10, 15], index=0, key="tab5_top")
        
        data_g5 = (
            df_global.groupby("track_genre")["popularity"]
            .mean()
            .reset_index()
            .sort_values("popularity", ascending=False)
            .head(top_n2)
        )

        fig5 = px.bar(
            data_g5,
            x="popularity",
            y="track_genre",
            orientation='h',
            color_discrete_sequence=["#1DB954"]
        )
        fig5 = apply_plotly_theme(fig5)
        st.plotly_chart(fig5, use_container_width=True)

        col_a3, col_b3 = st.columns(2)
            top_n2 = col_b2.selectbox("Seleccionar", ["track_name"], index=0, key="tab6_song")
            
            data_g6 = (
                df_global["track_name"]
                .reset_index()
                .sort_values("track_name", ascending=False)
                .head(top_n2)
            )

    st.write("La canción: ", data_g6, " tiene una energia de: ")
        
        

else:
    st.warning("No hay datos o el archivo no se encuentra.")
















