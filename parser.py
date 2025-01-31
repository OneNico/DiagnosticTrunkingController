# parser.py
import re
import pandas as pd

def parse_diagnostic_file(file_content: str) -> dict:
    """
    Procesa el contenido de un archivo de diagnóstico y retorna
    varios DataFrames o diccionarios con la información relevante.

    Retorna un diccionario con, por ejemplo:
      {
        "channels_df": pd.DataFrame(...),
        "registrations_df": pd.DataFrame(...),
        "tgs_affiliations_df": pd.DataFrame(...),
        ...
      }
    """
    # Inicializamos estructuras donde guardaremos resultados
    channels_data = []
    registrations_data = []
    tg_affiliations_data = []

    # --- EJEMPLO 1: PARSEAR "Channel Status" ---
    # Buscamos secciones que empiezan con algo como "Site ID: X" hasta "Sites End" (simplificado)
    # Dentro, buscamos las líneas de canales:
    #   Channel 9 Logical: 9 SourceID: 50027 TargetID: 101 CallType:group-voice-call Status: Busy ...
    channel_pattern = re.compile(
        r"Channel\s+(\d+)\s+Logical:\s+(\d+)\s+SourceID:\s+(\S+)\s+TargetID:\s+(\S+)"
        r"\s+CallType:(\S+)\s+Status:\s+(\S+)\s+Allocated Time:\s+(\d+)", re.IGNORECASE
    )

    # Para capturar de qué "Site ID" estamos hablando, buscaremos
    # líneas tipo "Site ID: 2" y lo guardamos hasta que encontremos otro.
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

            channels_data.append({
                "site_id": int(current_site_id),
                "channel_number": int(channel_number),
                "logical": int(logical),
                "source_id": source_id,
                "target_id": target_id,
                "calltype": calltype,
                "status": status,
                "allocated_time": int(allocated_time),
            })

    # Convertimos a DataFrame
    channels_df = pd.DataFrame(channels_data)

    # --- EJEMPLO 2: PARSEAR "Dynamic Registrations" ---
    # Líneas típicas:
    #   source:32001 username: siteID:1 TGList:602  active:true timestamp:1738238968
    registration_pattern = re.compile(
        r"source:(\S+)\s+username:\s*(\S*)\s+siteID:(\S+)\s+TGList:(\S*)\s+active:(\S+)\s+timestamp:(\d+)",
        re.IGNORECASE
    )

    for line in lines:
        reg_match = registration_pattern.search(line)
        if reg_match:
            source_id = reg_match.group(1)
            username = reg_match.group(2)
            site_id = reg_match.group(3)
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

    # --- EJEMPLO 3: PARSEAR "Dynamically Affiliated TGs" ---
    # Líneas típicas (simplificado):
    #   TG:101 has 3 dyn affiliated sites: 1:190 2:19 29:1
    tg_aff_pattern = re.compile(
        r"TG:(\d+)\s+has\s+(\d+)\s+dyn\s+affiliated\s+sites:\s+(.*)", re.IGNORECASE
    )

    for line in lines:
        tg_match = tg_aff_pattern.search(line)
        if tg_match:
            tg_id = tg_match.group(1)
            num_sites = tg_match.group(2)
            raw_sites = tg_match.group(3)
            # raw_sites por ejemplo "1:190 2:19 29:1"
            # Podemos separarlo por espacios
            site_info = raw_sites.split()
            for s in site_info:
                # "1:190" => site=1, affiliated_count=190 (posible)
                if ":" in s:
                    site_part, aff_count = s.split(":")
                    tg_affiliations_data.append({
                        "tg_id": int(tg_id),
                        "site_id": int(site_part),
                        "aff_count": int(aff_count)
                    })

    tgs_affiliations_df = pd.DataFrame(tg_affiliations_data)

    # Agrega más parseos según necesites (p.ej. topología, licencias, etc.)

    return {
        "channels_df": channels_df,
        "registrations_df": registrations_df,
        "tgs_affiliations_df": tgs_affiliations_df
    }

def parse_multiple_files(uploaded_files) -> dict:
    """
    Procesa múltiples archivos. Devuelve un dict con dataframes combinados
    o varios dataframes en listas, etc.
    """
    all_channels = []
    all_regs = []
    all_tgs_aff = []

    for uploaded_file in uploaded_files:
        content = uploaded_file.read().decode("utf-8", errors="ignore")
        parsed = parse_diagnostic_file(content)

        all_channels.append(parsed["channels_df"])
        all_regs.append(parsed["registrations_df"])
        all_tgs_aff.append(parsed["tgs_affiliations_df"])

    # Concatenamos la info de todos los archivos
    channels_df = pd.concat(all_channels, ignore_index=True)
    registrations_df = pd.concat(all_regs, ignore_index=True)
    tgs_affiliations_df = pd.concat(all_tgs_aff, ignore_index=True)

    # Retornamos todo
    return {
        "channels_df": channels_df,
        "registrations_df": registrations_df,
        "tgs_affiliations_df": tgs_affiliations_df
    }
