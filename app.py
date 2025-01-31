import streamlit as st
import pandas as pd
import plotly.express as px
import networkx as nx
from pyvis.network import Network
from streamlit.components.v1 import html
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import random

from parser import parse_multiple_files

# Diccionario original para invertirlo y así recuperar IDs numéricos
GRUPO_MAP = {
    101: 'SU-OPERACIÓN MINA',
    102: 'SU-COORD MINA',
    103: 'SU-MANTENC. MINA',
    104: 'SU-SERVICIOS MINA',
    105: 'SU-PERFO. TRONAD.',
    106: 'SU-PLANIFIC Y DES',
    107: 'SU-CHANCADO',
    108: 'SU-MOLIENDA',
    109: 'SU-FLOTACIÓN',
    110: 'SU-MANT MEC',
    111: 'SU-MANT ELEC',
    112: 'SU-MOLY',
    113: 'SU-RELAVES',
    114: 'SU-GERENCIA PROYECTO',
    117: 'SU-GERENCIA PROYECTO 01',
    115: 'ES-OP MINA',
    116: 'ES-COORD MINA',
    119: 'ES-PERF TRONAD',
    122: 'ES-MANTENC MINA',
    123: 'ES-SERV MINA',
    124: 'ES-PLAN DESA',
    120: 'SU-MANT SEG1',
    121: 'SU-MANT SEG2',
    201: 'OX-OPERACIÓN MINA',
    202: 'OX-COORD MINA',
    203: 'OX-MANTENC. MINA',
    204: 'OX-SERVICIOS MINA',
    205: 'OX-PERFO. TRONAD.',
    206: 'OX-PLANIFIC Y DES',
    207: 'OX-AREA SECA',
    208: 'OX-AREA HUMEDA',
    209: 'OX-RIPIOS',
    210: 'OX-MANTENC MEC',
    211: 'OX-MANTENC ELEC',
    212: 'OX-SX-EW',
    213: 'OX-CHANCADO',
    301: 'ENC-OPERACIÓN MINA',
    302: 'ENC-COORD MINA',
    303: 'ENC-MANTENC. MINA',
    304: 'ENC-SERVICIOS MINA',
    305: 'ENC-PERFO TRONAD',
    306: 'ENC-PLANIFIC Y DES',
    307: 'ENC-SERVICIOS MINA 2',
    308: 'ENC-SERVICIOS MINA 3',
    309: 'ENC-SERVICIOS MINA 4',
    501: 'DESPACHO PRIMARIO',
    601: 'PROTECC IND',
    602: 'COORD EMERG',
    603: 'EMER',
    604: 'TICA',
    605: 'GLOBAL',
    606: 'BODEGA',
    607: 'DESPACHO',
    901: 'DESPACHO SECUNDARIO',
    999: 'DESCONOCIDO'
}

# Invertimos el diccionario para poder recuperar el ID numérico a partir del nombre
INV_GRUPO_MAP = {v: k for k, v in GRUPO_MAP.items()}

st.set_page_config(page_title="Herramienta de Análisis de Archivos de Diagnóstico (CMSS)", layout="wide")


def main():
    st.title("Herramienta de Análisis de Archivos de Diagnóstico (CMSS)")
    st.write("""
    Esta aplicación procesa uno o varios archivos `.txt` de diagnóstico, donde cada archivo
    se asocia a una hora específica (ej. `10.txt` => Hora=10). Para generar un archivo de diagnóstico:

    1. Copia el código obtenido del proceso de diagnóstico.
    2. Guarda el contenido copiado en un archivo `.txt`.
    3. Nombra el archivo con la hora correspondiente. Por ejemplo, si generaste el diagnóstico a las 10:55, el archivo debe llamarse `11.txt`.

    Se generan visualizaciones:

    1. Uso de canales
    2. Afiliaciones de Grupo
    3. Radios registradas (activas vs inactivas)
    4. Uso por sitios
    5. Tiempo de llamada por Grupo
    6. Topología (simplificada)
    7. Evolución del uptime (Hora)
    8. Cantidad de dispositivos por Sitio y Hora
    9. Cantidad de Radios conectadas por hora a los distintos grupos
    """)

    uploaded_files = st.file_uploader(
        "Sube uno o varios archivos .txt (ej. 10.txt, 13.txt, etc.):",
        type=["txt"],
        accept_multiple_files=True
    )

    if uploaded_files:
        data_dict = parse_multiple_files(uploaded_files)
        channels_df = data_dict["channels_df"]
        registrations_df = data_dict["registrations_df"]
        tgs_affiliations_df = data_dict["tgs_affiliations_df"]

        st.subheader("Datos Parseados")
        with st.expander("Mostrar DataFrames en bruto"):
            st.write("**Channels DataFrame**", channels_df.head(20))
            st.write("**Registrations DataFrame**", registrations_df.head(20))
            st.write("**TG Affiliations DataFrame**", tgs_affiliations_df.head(20))

        # --------------------------
        # 1. Gráfico de uso de canales
        st.header("1. Gráfico de Uso de Canales")

        if not channels_df.empty:
            channel_status_count = channels_df.groupby("status").size().reset_index(name="count")
            fig1 = px.bar(
                channel_status_count,
                x="status",
                y="count",
                title="Distribución de estados de canales"
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No hay datos de canales en los archivos subidos.")

        # --------------------------
        # 2. Gráfico de Afiliaciones de Grupo
        st.header("2. Afiliaciones de Grupo (dinámicas)")

        if not tgs_affiliations_df.empty:
            aff_by_group = tgs_affiliations_df.groupby("grupo").agg(total_affs=("aff_count", "sum")).reset_index()
            fig2 = px.bar(
                aff_by_group,
                x="grupo",
                y="total_affs",
                title="Afiliaciones totales por Grupo"
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos de afiliaciones de grupo en los archivos subidos.")

        # --------------------------
        # 3. Radios registradas (activas vs inactivas)
        st.header("3. Radios registradas (activas vs inactivas)")

        if not registrations_df.empty:
            active_count = registrations_df.groupby("active").size().reset_index(name="count")
            fig3 = px.pie(
                active_count,
                names="active",
                values="count",
                title="Radios registradas: Activas vs. Inactivas"
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay datos de registros dinámicos en los archivos subidos.")

        # --------------------------
        # 4. Gráfico de uso por sitios
        st.header("4. Uso por Sitios (Canales)")

        if not channels_df.empty:
            busy_channels_by_site = (
                channels_df[channels_df["status"] == "Busy"]
                .groupby("sitio")
                .size()
                .reset_index(name="count_busy")
            )
            fig4 = px.bar(
                busy_channels_by_site,
                x="sitio",
                y="count_busy",
                title="Cantidad de canales Busy por Sitio"
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No hay información de canales para ver uso por sitios.")

        # --------------------------
        # 5. Tiempo de llamada por Grupo (ejemplo)
        st.header("5. Tiempo de llamada por Grupo (ejemplo)")

        if not channels_df.empty:
            # Filtramos solo llamadas de voz grupales que estén en Busy
            voice_calls = channels_df[
                (channels_df["status"] == "Busy") &
                (channels_df["calltype"] == "group-voice-call")
                ]
            time_by_group = (
                voice_calls
                .groupby("grupo")["allocated_time"]
                .sum()
                .reset_index(name="total_time")
            )
            fig5 = px.bar(
                time_by_group,
                x="grupo",
                y="total_time",
                title="Suma de allocated_time por Grupo (demo)"
            )
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No hay información de canales Busy / calltype para graficar tiempo de llamada.")

        # --------------------------
        # 6. Topología (Vista de Red Interactiva) - Ahora con grupos
        st.header("6. Topología (Vista de Red Interactiva)")

        if not channels_df.empty:
            # Crear un grafo usando NetworkX
            G = nx.Graph()

            # Obtener una lista única de grupos
            unique_groups = channels_df['grupo'].unique()

            # Utilizar una paleta de colores de matplotlib
            color_palette = plt.get_cmap('tab20').colors  # Puedes elegir otra paleta

            # Asignar colores a los grupos
            group_colors = {}
            for i, group in enumerate(unique_groups):
                group_colors[group] = mcolors.to_hex(color_palette[i % len(color_palette)])

            # Mostrar el mapeo de colores (opcional)
            st.sidebar.header("Mapa de Colores por Grupo")
            for group, color in group_colors.items():
                st.sidebar.markdown(f"<span style='color:{color}'>●</span> {group}", unsafe_allow_html=True)

            # Añadir nodos: todos los sitios únicos con atributos de grupo
            sitios = channels_df['sitio'].unique()
            for sitio in sitios:
                grupo = channels_df.loc[channels_df['sitio'] == sitio, 'grupo'].values[0]
                G.add_node(sitio, label=str(sitio), title=f"Grupo: {grupo}", color=group_colors.get(grupo, "#FFFFFF"))

            # Añadir aristas basadas en TargetID
            for _, row in channels_df.iterrows():
                sitio = row['sitio']
                target_id = row['target_id']

                # Verificar si target_id es un sitio
                if isinstance(target_id, int) and target_id in sitios:
                    G.add_edge(sitio, target_id)

            # Crear un objeto de Pyvis Network
            net = Network(height='600px', width='100%', bgcolor='#222222', font_color='white')

            # Configurar opciones del grafo
            net.set_options("""
            var options = {
              "nodes": {
                "font": {
                  "size": 14,
                  "color": "white"
                },
                "shape": "dot",
                "size": 20,
                "borderWidth": 2,
                "borderWidthSelected": 4
              },
              "edges": {
                "color": {
                  "color": "#ffffff"
                },
                "smooth": false
              },
              "physics": {
                "forceAtlas2Based": {
                  "gravitationalConstant": -50,
                  "centralGravity": 0.01,
                  "springLength": 100,
                  "springConstant": 0.08
                },
                "maxVelocity": 50,
                "solver": "forceAtlas2Based",
                "timestep": 0.35,
                "stabilization": {
                  "iterations": 150
                }
              }
            }
            """)

            # Convertir NetworkX graph a Pyvis
            net.from_nx(G)

            # Asignar colores y tooltips a los nodos
            for node in net.nodes:
                sitio = node['id']
                grupo = channels_df.loc[channels_df['sitio'] == sitio, 'grupo'].values[0]
                node['color'] = group_colors.get(grupo, "#FFFFFF")
                node['title'] = f"Sitio: {sitio}<br>Grupo: {grupo}"

            # Generar el HTML del grafo sin guardar a un archivo
            try:
                html_content = net.generate_html(notebook=False)
                # Mostrar el grafo en Streamlit
                html(html_content, height=600, scrolling=True)
            except Exception as e:
                st.error(f"Error al generar la topología: {e}")
        else:
            st.info("No hay información de canales para mostrar la topología.")

        # --------------------------
        # 7. Evolución del uptime (por hora de archivo)
        st.header("7. Evolución del Uptime (Hora)")
        st.write("""
        Se cuenta cuántos registros están activos (active=true) para cada hora
        según el nombre del archivo (por ej. 10.txt => Hora=10).
        """)

        if not registrations_df.empty:
            if "Hora" in registrations_df.columns:
                active_regs = registrations_df[registrations_df["active"] == "true"]
                df_hour = (
                    active_regs
                    .groupby("Hora")
                    .size()
                    .reset_index(name="count_active")
                )
                fig7 = px.line(
                    df_hour,
                    x="Hora",
                    y="count_active",
                    markers=True,
                    title="Evolución de registros activos (Hora)"
                )
                st.plotly_chart(fig7, use_container_width=True)
            else:
                st.warning("No se encontró la columna 'Hora' en registrations_df. Revisa la lógica.")
        else:
            st.info("No hay datos de registros para graficar la evolución del uptime por Hora.")

        # --------------------------
        # 8. Cantidad de dispositivos por Sitio y Hora
        st.header("8. Cantidad de Dispositivos por Sitio y Hora")
        st.write("""
        Se muestra cuántos registros (líneas) hay en 'Dynamic Registrations' para cada
        Hora (derivada del nombre de archivo) y Sitio.
        """)

        if not registrations_df.empty:
            if "Hora" in registrations_df.columns:
                # Eliminamos la exclusión de sitios 28,29,30
                regs_site_filtered = registrations_df.copy()

                df_counts = regs_site_filtered.groupby(["Hora", "sitio"]).size().reset_index(name="count")
                fig8 = px.bar(
                    df_counts,
                    x='Hora',
                    y='count',
                    color='sitio',
                    barmode='group',
                    text='count',
                    labels={
                        'Hora': 'Hora',
                        'count': 'Cantidad de Registros',
                        'sitio': 'Sitio'
                    },
                    title='Cantidad de Dispositivos (Registros) por Sitio y Hora'
                )
                fig8.update_traces(textposition='outside')
                fig8.update_layout(bargap=0.15, bargroupgap=0.0)
                st.plotly_chart(fig8, use_container_width=True)
            else:
                st.warning("No se encontró la columna 'Hora' en registrations_df. Revisa la lógica.")
        else:
            st.info("No hay datos de registros para graficar.")

        # --------------------------
        # 9. Gráficos de Grupos por Hora (subdivididos en rangos)
        #    - Haremos uno para 1xx, 2xx, 3xx, y 5xx-9xx
        #    - Filtraremos usando "grupo_num"

        st.header("9. Cantidad de Radios conectadas por hora a los distintos grupos")
        st.write("""
        Se generan gráficos separados para cada rango de grupos (1xx, 2xx, 3xx, 5xx-9xx).
        Cada gráfico muestra la cantidad de registros por Hora y Grupo dentro del rango especificado.
        """)

        if not registrations_df.empty:
            if "Hora" in registrations_df.columns and "grupo_num" in registrations_df.columns:
                # Filtramos solo aquellos registros que tienen un grupo_num válido
                regs_copy = registrations_df.dropna(subset=["grupo_num"]).copy()

                # Definimos los rangos de grupos, excluyendo 4xx si no es necesario
                grupo_ranges = [
                    {"label": "Planta Concentradora y Mina Esperanza (1xx)", "start": 100, "end": 200},
                    {"label": "Mina Tesoro y Planta Hidro (2xx)", "start": 200, "end": 300},
                    {"label": "Planta Encuentro (3xx)", "start": 300, "end": 400},
                    {"label": "Grupos Transversales (5xx-9xx)", "start": 500, "end": 1000},
                ]

                for ginfo in grupo_ranges:
                    label = ginfo["label"]
                    s = ginfo["start"]
                    e = ginfo["end"]

                    df_range = regs_copy[
                        (regs_copy["grupo_num"] >= s) &
                        (regs_copy["grupo_num"] < e)
                        ]

                    if df_range.empty:
                        st.info(f"No hay registros para grupos {label}.")
                        continue

                    st.subheader(f"{label} por Hora")

                    # Agrupamos por (Hora, grupo)
                    df_gcount = (
                        df_range
                        .groupby(["Hora", "grupo"])
                        .size()
                        .reset_index(name="count")
                    )

                    fig_g = px.bar(
                        df_gcount,
                        x="Hora",
                        y="count",
                        color="grupo",  # Usamos el nombre del grupo
                        barmode="group",
                        text="count",
                        labels={
                            "Hora": "Hora",
                            "count": "Cantidad de Registros",
                            "grupo": "Grupo"
                        },
                        title=f"Cantidad de Radios conectadas por Hora a los distintos grupos {label}"
                    )
                    fig_g.update_traces(textposition='outside')
                    fig_g.update_layout(bargap=0.15, bargroupgap=0.0)
                    st.plotly_chart(fig_g, use_container_width=True)
            else:
                st.warning("No se encontraron las columnas 'Hora' o 'grupo_num' en registrations_df. Revisa la lógica.")
        else:
            st.info("No hay registros en 'registrations_df' para mostrar gráficos de grupo por Hora.")


if __name__ == "__main__":
    main()
