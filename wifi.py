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
    """Escanea redes WiFi cercanas y devuelve información detallada."""
    print("\n[+] Escaneando redes disponibles...")
    output, _ = run_command(f"iw dev {interface} scan", use_sudo=True)
    networks = []
    current_network = {}
    
    for line in output.splitlines():
        if "BSS" in line:
            if current_network:
                networks.append(current_network)
            current_network = {"BSSID": line.split()[1]}
        elif "SSID:" in line:
            current_network["SSID"] = line.split(":", 1)[1].strip()
        elif "freq:" in line:
            current_network["Channel"] = freq_to_channel(line.split(":")[1].strip())
        elif "signal:" in line:
            current_network["Signal"] = line.split(":")[1].strip()
    if current_network:
        networks.append(current_network)
    
    return networks

def create_wpa_supplicant_conf(ssid):
    """Crea un archivo de configuración para wpa_supplicant."""
    conf_content = f"""
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}

    conf_path = "/data/data/com.termux/files/home/wpa_supplicant.conf"
    with open(conf_path, "w") as conf_file:
        conf_file.write(conf_content)
    return conf_path

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
    print("Desarrollador: Tú")
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
    table = [[i+1, n["SSID"], n["BSSID"], n["Channel"], n["Signal"]] for i, n in enumerate(networks)]
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
    print(f"\n[+] Red seleccionada: {selected_network['SSID']} ({selected_network['BSSID']})")
    
    # Intentar asociarse usando wpa_supplicant
    output = run_wpa_supplicant(interface, selected_network["SSID"])
    print("\n[+] Salida de wpa_supplicant:")
    print(output)

if __name__ == "__main__":
    main()
