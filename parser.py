import re
import pandas as pd


def parse_diagnostic_file(file_content: str) -> dict:
    """
    Procesa el contenido de un archivo de diagnóstico y retorna
    varios DataFrames con la información relevante.

    No asignamos hora aquí. Eso se hará en parse_multiple_files
    en función del nombre del archivo.
    """
    channels_data = []
    registrations_data = []
    tg_affiliations_data = []

    # --- PARSEO Channels ---
    channel_pattern = re.compile(
        r"Channel\s+(\d+)\s+Logical:\s+(\d+)\s+SourceID:\s+(\S+)\s+TargetID:\s+(\S+)"
        r"\s+CallType:(\S+)\s+Status:\s+(\S+)\s+Allocated Time:\s+(\d+)",
        re.IGNORECASE
    )
    site_id_pattern = re.compile(r"Site ID:\s+(\d+)", re.IGNORECASE)

    current_site_id = None
    lines = file_content.splitlines()

    for line in lines:
        site_match = site_id_pattern.search(line)
        if site_match:
            current_site_id = site_match.group(1)

        channel_match = channel_pattern.search(line)
        if channel_match and current_site_id is not None:
            channel_number = channel_match.group(1)
            logical = channel_match.group(2)
            source_id = channel_match.group(3)
            target_id = channel_match.group(4)
            calltype = channel_match.group(5)
            status = channel_match.group(6)
            allocated_time = channel_match.group(7)

            # Convertimos target_id a int si es posible
            try:
                target_id_converted = int(target_id)
            except ValueError:
                target_id_converted = target_id  # si no es numérico, lo dejamos como string

            channels_data.append({
                "site_id": int(current_site_id),
                "channel_number": int(channel_number),
                "logical": int(logical),
                "source_id": source_id,
                "target_id": target_id_converted,
                "calltype": calltype,
                "status": status,
                "allocated_time": int(allocated_time),
            })

    channels_df = pd.DataFrame(channels_data)

    # --- PARSEO Dynamic Registrations ---
    registration_pattern = re.compile(
        r"source:(\S+)\s+username:\s*(\S*)\s+siteID:(\S+)\s+TGList:(\S*)\s+active:(\S+).*?timestamp:(\d+)",
        re.IGNORECASE
    )

    for line in lines:
        reg_match = registration_pattern.search(line)
        if reg_match:
            source_id = reg_match.group(1)
            username = reg_match.group(2)
            site_id = int(reg_match.group(3))
            tg_list = reg_match.group(4)
            active = reg_match.group(5)
            timestamp = reg_match.group(6)
            registrations_data.append({
                "source_id": source_id,
                "username": username,
                "site_id": site_id,
                "tg_list": tg_list,
                "active": active,
                "timestamp": int(timestamp),
            })

    registrations_df = pd.DataFrame(registrations_data)

    # --- PARSEO Dynamically Affiliated TGs ---
    tg_aff_pattern = re.compile(
        r"TG:(\d+)\s+has\s+(\d+)\s+dyn\s+affiliated\s+sites:\s+(.*)",
        re.IGNORECASE
    )

    for line in lines:
        tg_match = tg_aff_pattern.search(line)
        if tg_match:
            tg_id = int(tg_match.group(1))
            raw_sites = tg_match.group(3)
            site_info = raw_sites.split()
            for s in site_info:
                if ":" in s:
                    site_part, aff_count = s.split(":")
                    tg_affiliations_data.append({
                        "tg_id": tg_id,
                        "site_id": int(site_part),
                        "aff_count": int(aff_count)
                    })

    tgs_affiliations_df = pd.DataFrame(tg_affiliations_data)

    return {
        "channels_df": channels_df,
        "registrations_df": registrations_df,
        "tgs_affiliations_df": tgs_affiliations_df
    }


def parse_multiple_files(uploaded_files) -> dict:
    """
    Procesa múltiples archivos. Devuelve un dict con dataframes combinados
    y les aplica la lógica de renombre y mapeo:
    - 'site_id' -> 'sitio'
    - 'tg_list' -> 'grupo_num' y 'grupo' (en registrations_df)
    - 'tg_id' -> 'grupo_num' y 'grupo' (en tgs_affiliations_df)
    - 'target_id' se mantiene para topología
    - Extra: asignar "Hora" en base al nombre del archivo (ej: '10.txt' => hora=10).
    """
    all_channels = []
    all_regs = []
    all_tgs_aff = []

    # Diccionarios de mapeo
    site_map = {
        1: "SULFUROS",
        2: "OXIDOS",
        3: "OXE",
        4: "ES"
    }

    grupo_map = {
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
    307: 'ENC-AREA SECA',
    308: 'ENC-AREA HUMEDA',
    309: 'ENC-RIPIOS',
    310: 'ENC-MANTENC MEC'
    311: 'ENC-MANTENC ELEC'
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

    # Regex para extraer el número de hora del nombre de archivo, ejemplo "10.txt" => 10
    hour_pattern = re.compile(r"(\d+)\.txt$", re.IGNORECASE)

    for uploaded_file in uploaded_files:
        filename = uploaded_file.name  # nombre: ej. "10.txt"
        match_hour = hour_pattern.search(filename)
        hour_value = None
        if match_hour:
            hour_value = int(match_hour.group(1))

        content = uploaded_file.read().decode("utf-8", errors="ignore")
        parsed = parse_diagnostic_file(content)

        # Si encontramos hora, la asignamos en registrations_df como nueva columna
        if hour_value is not None:
            parsed["registrations_df"]["Hora"] = hour_value

        all_channels.append(parsed["channels_df"])
        all_regs.append(parsed["registrations_df"])
        all_tgs_aff.append(parsed["tgs_affiliations_df"])

    # Concatenamos la info de todos los archivos
    if all_channels:
        channels_df = pd.concat(all_channels, ignore_index=True)
    else:
        channels_df = pd.DataFrame()

    if all_regs:
        registrations_df = pd.concat(all_regs, ignore_index=True)
    else:
        registrations_df = pd.DataFrame()

    if all_tgs_aff:
        tgs_affiliations_df = pd.concat(all_tgs_aff, ignore_index=True)
    else:
        tgs_affiliations_df = pd.DataFrame()

    # Renombramos y mapeamos site_id -> sitio
    for df in [channels_df, registrations_df, tgs_affiliations_df]:
        if "site_id" in df.columns:
            df.rename(columns={"site_id": "sitio"}, inplace=True)
            df["sitio"] = df["sitio"].apply(lambda x: site_map[x] if x in site_map else x)

    # Crear 'grupo_num' y 'grupo' sin renombrar 'target_id'
    if "target_id" in channels_df.columns:
        # Asignar 'grupo_num' basado en 'target_id'
        channels_df["grupo_num"] = channels_df["target_id"].apply(
            lambda x: x if isinstance(x, int) else (int(x) if isinstance(x, str) and x.isdigit() else x)
        )
        channels_df["grupo"] = channels_df["grupo_num"].apply(
            lambda x: grupo_map[x] if (isinstance(x, int) and x in grupo_map) else (
                'Grupo 400-499' if isinstance(x, int) and 400 <= x < 500 else x
            )
        )

    # Renombramos tg_list -> grupo_num y mapear a grupo en registrations_df
    if "tg_list" in registrations_df.columns:
        registrations_df.rename(columns={"tg_list": "grupo_num"}, inplace=True)
        # Separar múltiples IDs si existen
        registrations_df['grupo_num'] = registrations_df['grupo_num'].astype(str).str.split(',')
        registrations_df = registrations_df.explode('grupo_num')
        registrations_df['grupo_num'] = pd.to_numeric(registrations_df['grupo_num'], errors='coerce')
        # Mapear a grupo usando grupo_map o asignar 'Grupo 400-499' si está en el rango
        registrations_df["grupo"] = registrations_df["grupo_num"].apply(
            lambda x: grupo_map[x] if (pd.notnull(x) and x in grupo_map) else (
                'Grupo 400-499' if isinstance(x, int) and 400 <= x < 500 else x
            )
        )

    # Renombramos tg_id -> grupo_num y mapear a grupo en tgs_affiliations_df
    if "tg_id" in tgs_affiliations_df.columns:
        tgs_affiliations_df.rename(columns={"tg_id": "grupo_num"}, inplace=True)
        tgs_affiliations_df["grupo_num"] = pd.to_numeric(tgs_affiliations_df["grupo_num"], errors='coerce')
        # Mapear a grupo usando grupo_map o asignar 'Grupo 400-499' si está en el rango
        tgs_affiliations_df["grupo"] = tgs_affiliations_df["grupo_num"].apply(
            lambda x: grupo_map[x] if (pd.notnull(x) and x in grupo_map) else (
                'Grupo 400-499' if isinstance(x, int) and 400 <= x < 500 else x
            )
        )

    return {
        "channels_df": channels_df,
        "registrations_df": registrations_df,
        "tgs_affiliations_df": tgs_affiliations_df
    }
