# app.py
import streamlit as st
import pandas as pd
import plotly.express as px

from parser import parse_multiple_files

st.set_page_config(page_title="Análisis de Diagnósticos CMSS", layout="wide")

def main():
    st.title("Herramienta de Análisis de Archivos de Diagnóstico (CMSS)")

    st.write("""
    Esta aplicación procesa uno o varios archivos `.txt` de diagnóstico
    (formato Motorola CMSS) y genera visualizaciones:
    1. Uso de canales
    2. Afiliaciones de TG
    3. Radios registradas activas/inactivas
    4. Uso por sitios
    5. Tiempo de llamada por TG
    6. Topología (simplificada)
    7. Evolución del uptime (o cualquier otra métrica que se desee)
    """)

    # Subir uno o varios archivos
    uploaded_files = st.file_uploader("Sube uno o varios archivos .txt:",
                                      type=["txt"],
                                      accept_multiple_files=True)

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

        # ----------------------------------------------------------------------------
        # 1. Gráfico de uso de canales
        st.header("1. Gráfico de Uso de Canales")

        if not channels_df.empty:
            # Ejemplo: Contar cuántos canales están en Busy, Idle, etc.
            channel_status_count = channels_df.groupby(["status"]).size().reset_index(name="count")
            fig1 = px.bar(channel_status_count, x="status", y="count", title="Distribución de estados de canales")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No hay datos de canales en los archivos subidos.")

        # ----------------------------------------------------------------------------
        # 2. Gráfico de Afiliaciones de TG
        st.header("2. Afiliaciones de TG (dinámicas)")

        if not tgs_affiliations_df.empty:
            # Contar cuántas afiliaciones por TG (suma de sitios)
            aff_by_tg = tgs_affiliations_df.groupby("tg_id")["aff_count"].sum().reset_index(name="total_affs")
            fig2 = px.bar(aff_by_tg, x="tg_id", y="total_affs", title="Afiliaciones totales por TG")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No hay datos de afiliaciones TG en los archivos subidos.")

        # ----------------------------------------------------------------------------
        # 3. Radios registradas activas vs inactivas
        st.header("3. Radios registradas (activas vs inactivas)")

        if not registrations_df.empty:
            # Contar activos vs inactivos
            active_count = registrations_df.groupby("active").size().reset_index(name="count")
            fig3 = px.pie(active_count, names="active", values="count",
                          title="Radios registradas: Activas vs. Inactivas")
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("No hay datos de registros dinámicos en los archivos subidos.")

        # ----------------------------------------------------------------------------
        # 4. Gráfico de uso por sitios (ej: cuántos canales busy por sitio)
        st.header("4. Uso por sitios")

        if not channels_df.empty:
            # Ejemplo: contar cuántos canales "Busy" hay por site
            busy_channels_by_site = channels_df[channels_df["status"]=="Busy"] \
                                        .groupby("site_id").size().reset_index(name="count_busy")
            fig4 = px.bar(busy_channels_by_site, x="site_id", y="count_busy",
                          title="Cantidad de canales Busy por Sitio")
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No hay información de canales para ver uso por sitios.")

        # ----------------------------------------------------------------------------
        # 5. Tiempo de llamada por TalkGroup (ejemplo simplificado)
        st.header("5. Tiempo de llamada por TG (ejemplo)")

        if not channels_df.empty:
            # Fingimos que allocated_time es la duración (no siempre es así, ajústalo a tu real definicón)
            # Tomamos solo los channels en 'Busy' con calltype=group-voice-call
            voice_calls = channels_df[(channels_df["status"]=="Busy") &
                                      (channels_df["calltype"]=="group-voice-call")]
            # Sumamos allocated_time como "tiempo total"
            # Realmente, allocated_time puede no ser la duración, pero se ilustra cómo podrías agrupar
            tg_time = voice_calls.groupby("target_id")["allocated_time"].sum().reset_index(name="total_time")
            fig5 = px.bar(tg_time, x="target_id", y="total_time",
                          title="Suma de allocated_time por TG (simple demo)")
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No hay información de canales Busy / calltype para graficar tiempo de llamada.")

        # ----------------------------------------------------------------------------
        # 6. Topología (simplificada)
        st.header("6. Topología (Vista Simplificada)")
        st.write("""
        En el archivo se ve que hay `Site ID: 1, 2, 3, 4, etc.` con cierto estado (SYNCED).
        Aquí podríamos hacer un diagrama de red o un grafico force-directed con librerías como networkx.
        Para la demo, solo mostraremos una tabla simple con los sites reconocidos.
        """)

        if not channels_df.empty:
            unique_sites = channels_df["site_id"].unique()
            df_sites = pd.DataFrame({"site_id": unique_sites})
            st.dataframe(df_sites)
            st.info("Para un diagrama topológico más elaborado, usar librerías como `networkx` y `pyvis`.")
        else:
            st.info("No hay info de sitios para mostrar la topología simplificada.")

        # ----------------------------------------------------------------------------
        # 7. Evolución del uptime
        st.header("7. Evolución del Uptime (o alguna métrica en el tiempo)")
        st.write("""
        Tu archivo incluye campos como `Epoch time` o timestamps en `registrations_df`.
        Podríamos graficar cuántos registros se hacen a lo largo del tiempo. 
        """)

        if not registrations_df.empty:
            # Por ejemplo, contamos número de registros activos (active=true) en función del timestamp
            # (Se asume que timestamp es un unix-like integer; se podría convertir a datetime).
            active_regs = registrations_df[registrations_df["active"]=="true"].copy()
            # Convertir timestamp a datetime (si es un epoch real en segundos)
            active_regs["datetime"] = pd.to_datetime(active_regs["timestamp"], unit='s', errors='coerce')
            # Agrupamos por fecha/hora (resample), contamos registros
            # Para hacerlo, necesitamos un índice de tiempo
            active_regs.set_index("datetime", inplace=True)
            # Re-sample por hora/día, etc. (por simplicidad, 'H')
            count_over_time = active_regs.resample("H")["source_id"].count().reset_index(name="count_active")
            fig7 = px.line(count_over_time, x="datetime", y="count_active",
                           title="Evolución de registros activos a lo largo del tiempo (por hora)")
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No hay timestamps en los registros o no se puede graficar la evolución del uptime.")

if __name__ == "__main__":
    main()
