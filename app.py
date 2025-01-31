import streamlit as st
import pandas as pd
import plotly.express as px

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

st.set_page_config(page_title="Análisis de Diagnósticos CMSS", layout="wide")


def main():
    st.title("Herramienta de Análisis de Archivos de Diagnóstico (CMSS)")
    st.write("""
    Esta aplicación procesa uno o varios archivos `.txt` de diagnóstico, donde cada archivo
    se asocia a una hora específica (ej. `10.txt` => Hora=10). Se generan visualizaciones:
    1) Uso de canales
    2) Afiliaciones de Grupo
    3) Radios registradas (activas vs inactivas)
    4) Uso por sitios
    5) Tiempo de llamada por Grupo
    6) Topología (simplificada)
    7) Evolución del uptime (por hora de archivo)
    8) Cantidad de dispositivos por Sitio y Hora (excluyendo sitios 28,29,30)
    9) Gráficos de grupos (1xx, 2xx, 3xx, 4xx, 5xx-9xx) por hora
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
            aff_by_group = tgs_affiliations_df.groupby("grupo")["aff_count"].sum().reset_index(name="total_affs")
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
        # 6. Topología (simplificada)
        st.header("6. Topología (Vista Simplificada)")
        st.write("""
        En el archivo se ve que hay distintos sitios con su ID y estado.
        Aquí podríamos hacer un diagrama de red o un gráfico force-directed
        con librerías como networkx o pyvis.
        Para la demo, solo mostraremos una tabla simple con los sitios reconocidos.
        """)

        if not channels_df.empty:
            unique_sites = channels_df["sitio"].unique()
            df_sites = pd.DataFrame({"sitio": unique_sites})
            st.dataframe(df_sites)
            st.info("Para un diagrama topológico más elaborado, usar librerías como `networkx` y `pyvis`.")
        else:
            st.info("No hay info de sitios para mostrar la topología simplificada.")

        # --------------------------
        # 7. Evolución del uptime (por hora de archivo)
        st.header("7. Evolución del Uptime (por hora de archivo)")
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
                    title="Evolución de registros activos (por Hora de archivo)"
                )
                st.plotly_chart(fig7, use_container_width=True)
            else:
                st.warning("No se encontró la columna 'Hora' en registrations_df. Revisa la lógica.")
        else:
            st.info("No hay datos de registros para graficar la evolución del uptime por hora.")

        # --------------------------
        # 8. Cantidad de dispositivos por Sitio y Hora (excluyendo sitios 28,29,30)
        st.header("8. Cantidad de Dispositivos por Sitio y Hora (excluyendo 28,29,30)")
        st.write("""
        Se muestra cuántos registros (líneas) hay en 'Dynamic Registrations' para cada
        Hora (derivada del nombre de archivo) y Sitio (omitiendo sitios 28, 29 y 30).
        """)

        if not registrations_df.empty:
            if "Hora" in registrations_df.columns:
                # Omitimos sitios 28,29,30
                regs_site_filtered = registrations_df[~registrations_df["sitio"].isin([28, 29, 30])]

                df_counts = regs_site_filtered.groupby(["Hora", "sitio"]).size().reset_index(name="count")
                fig8 = px.bar(
                    df_counts,
                    x='Hora',
                    y='count',
                    color='sitio',
                    barmode='group',
                    text='count',
                    labels={
                        'Hora': 'Hora (archivo)',
                        'count': 'Cantidad de Registros',
                        'sitio': 'Sitio'
                    },
                    title='Cantidad de Dispositivos (Registros) por Sitio y Hora (excluyendo 28,29,30)'
                )
                fig8.update_traces(textposition='outside')
                fig8.update_layout(bargap=0.15, bargroupgap=0.0)
                st.plotly_chart(fig8, use_container_width=True)
            else:
                st.warning("No se encontró la columna 'Hora' en registrations_df. Revisa la lógica.")
        else:
            st.info("No hay datos de registros para graficar.")

        # --------------------------
        # 9. Gráficos de Grupos por Hora
        #    - Haremos uno para 1xx, 2xx, 3xx, 4xx, y 5xx-9xx
        #    - Filtraremos usando "grupo_num"

        st.header("9. Gráficos de Grupos por Hora (subdivididos en rangos)")
        st.write("""
        Se generan gráficos separados para cada rango de grupos (1xx, 2xx, 3xx, 4xx, 5xx-9xx).
        Cada gráfico muestra la cantidad de registros por Hora y Grupo dentro del rango especificado.
        """)

        if not registrations_df.empty:
            if "Hora" in registrations_df.columns and "grupo_num" in registrations_df.columns:
                # Filtramos solo aquellos registros que tienen un grupo_num válido
                regs_copy = registrations_df.dropna(subset=["grupo_num"]).copy()

                # Definimos los rangos de grupos, incluyendo 4xx
                grupo_ranges = [
                    {"label": "1xx (100-199)", "start": 100, "end": 200},
                    {"label": "2xx (200-299)", "start": 200, "end": 300},
                    {"label": "4xx (400-499)", "start": 400, "end": 500},
                    {"label": "5xx-9xx (500-999)", "start": 500, "end": 1000},
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

                    st.subheader(f"Grupos {label} por Hora")

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
                            "Hora": "Hora (archivo)",
                            "count": "Cantidad de Registros",
                            "grupo": "Grupo"
                        },
                        title=f"Registros por Hora (archivo) y Grupo {label}"
                    )
                    fig_g.update_traces(textposition='outside')
                    fig_g.update_layout(bargap=0.15, bargroupgap=0.0)
                    st.plotly_chart(fig_g, use_container_width=True)
            else:
                st.warning("No se encontraron las columnas 'Hora' o 'grupo_num' en registrations_df. Revisa la lógica.")
        else:
            st.info("No hay registros en 'registrations_df' para mostrar gráficos de grupo por hora.")


if __name__ == "__main__":
    main()
