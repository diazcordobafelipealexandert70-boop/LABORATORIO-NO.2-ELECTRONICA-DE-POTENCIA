import tkinter as tk #librerias que permite crear la interfaz del slider
from tkinter import DoubleVar # permite actualizar el slider con el valor escrito en la ventana 
import asyncio #libreria para manejar operaciones que necesitan esperar sin congelar el programa.
import threading # permite correr dos cosas al mismo tiempo 
from bleak import BleakClient, BleakScanner # Librerias para la comunicacion con Bluetooth

UART_RX_UUID = "6E400002-B5B3-F393-E0A9-E50E24DCCA9E" # Canal que usa el ESP32 para recibir los datos
ESP32_NAME   = "ESP32-SCR" # Nombre del ESP32

client_ble = None # Indicador de comunicacion activa
loop_ble   = None

async def conectar(): # Funcion asincronica que busca al ESP32 para conectarse
    global client_ble # Modificar el indicador de comunicacion activa desde dentro la funcion 
    while True:
        try: # Escirbe en la interfaz que estaa buscando el ESP32
            lbl.config(text="Buscando...", fg="orange")
            devices = await BleakScanner.discover(timeout=5.0) # Espera durante 5 seg 
            for d in devices:
                # Recorre los dispositivos encontrados 
                if ESP32_NAME in (d.name or ""):
                    # Si encuentra el ESP32 se conecta y lo muestra en la interfaz
                    client_ble = BleakClient(d.address)
                    await client_ble.connect()
                    lbl.config(text="Conectado ✓", fg="green")
                    return
        except:
            pass
        await asyncio.sleep(2) # Si no encontro el ESP32 espera 2 seg antes de volver a buscar

async def enviar(angulo): # La funcion envia los datos al ESP32, solo si la conexion esta activa
    global client_ble
    if client_ble and client_ble.is_connected:
        try: # Escribe el angulo en el canal RX
            await client_ble.write_gatt_char(
                UART_RX_UUID,
                f"{angulo}\n".encode()
            )
        except: # si el envio fallo, el esp32 se desconecto, lo muestra en la interfaz
            lbl.config(text="Desconectado", fg="red")
            client_ble = None

def hilo_ble(): #Crea un motor asyncio propio para este hilo
    global loop_ble
    loop_ble = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_ble)
    loop_ble.run_until_complete(conectar()) # Llama a la funcion conectar y se ejecuta hasta que el esp32 se conecte
    loop_ble.run_forever()

def al_mover(val): # Esta funcion se ejecuta cada vez que se mueve el slider. 
    if loop_ble:
        asyncio.run_coroutine_threadsafe(
            enviar(round(float(val), 1)), loop_ble # envia el angulo seleccionado con el slider
        )

# ── Interfaz Slider ────────────────────────────
# Crear ventana del slider
root = tk.Tk()
root.title("Ángulo de Disparo")
root.geometry("500x130")

valor = DoubleVar() # variable que fuinciona para el Slider y el Entry

# Parametros de la interfaz del Slider
tk.Scale(root, from_=0, to=180, orient='horizontal', 
         variable=valor, length=400, width=30,
         command=al_mover).pack()

tk.Entry(root, textvariable=valor).pack() # Crear una caja de texto entry 

lbl = tk.Label(root, text="Buscando...", fg="orange") # texto que muestra el estado de conexion
lbl.pack()

threading.Thread(target=hilo_ble, daemon=True).start()

root.mainloop()