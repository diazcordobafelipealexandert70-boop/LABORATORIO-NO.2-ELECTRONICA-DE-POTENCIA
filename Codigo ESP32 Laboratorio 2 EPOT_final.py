import bluetooth # Modulo Bluetooth para ESP32
import utime # Modulo de tiempo (microsegundos)
from machine import Pin # Control de pines en ESP32

# ── Definción de Pines ──────────────────────────────

CRUCE_CERO = Pin(2, Pin.IN, Pin.PULL_UP) # Pin que recibe el pulso del 4N25 que señala en cruce por cero (usa logica inversa PULL_UP)
PULSO      = Pin(21, Pin.OUT) # Pin por donde sale el pulso que activa el SCR
ANG_DISPARO = 90 # Angulo de disparo por defecto

# ── Anti-rebote ────────────────────────
ultimo_cruce     = 0 # Guarda el tiempo del ultimo cruce por cero 
TIEMPO_MINIMO_US = 8333	# Tiempo en microsegundos de un semiciclo de la señal de voltaje

# ── Interrupción cruce cero ────────────
# Esta funcion se ejecuta cada vez que el Pin 2 recibe un pulso
# Se encarga de calcular el tiempo de disparo y enviar el pulso al SCR
def disparo(pin):
    global ultimo_cruce # Sirve para modificar el valor predeterminado de la variable desde esta función
    ahora = utime.ticks_us() # Guarda el tiempo actual en microsegundos.
    if utime.ticks_diff(ahora, ultimo_cruce) < TIEMPO_MINIMO_US: # Sirve como filtro para enviar un pulso por cada periodo de la señal
        return
    ultimo_cruce = ahora # Actualiza el tiempo del ultimo cruce valido.
    if ANG_DISPARO >= 23 and ANG_DISPARO < 180:
        t = int(ANG_DISPARO * 8333 / 180)-2000# Usando regla de 3, se calcula el tiempo de disparo a partir del angulo recibido por Bluetooth
        utime.sleep_us(t) # Es el tiempo de espera que hay desde el cruce por cero, hasta enviar el pulso al SCR (retardo que controla la potencia)
        PULSO.on() # Envia pulso al SRC 
        utime.sleep_us(500) # Mantiene el pulso por 500 microsegundos
        PULSO.off() # Apaga el pulso
    elif ANG_DISPARO >= 0 and ANG_DISPARO <= 22:
        t = int(ANG_DISPARO * 8333 / 180)
        utime.sleep_us(t) # Es el tiempo de espera que hay desde el cruce por cero, hasta enviar el pulso al SCR (retardo que controla la potencia)
        PULSO.on() # Envia pulso al SRC 
        utime.sleep_us(500) # Mantiene el pulso por 500 microsegundos
        PULSO.off() # Apaga el pulso
    else:
        PULSO.off() # Apaga el pulso


CRUCE_CERO.irq(trigger=Pin.IRQ_FALLING, handler=disparo) # Interrupcion que se ejecuta cada vez que el pin 2 recibe un pulso y llama a la función de disparo

# ── Comunciacion Bluetooth ───────────────────────────
ble = bluetooth.BLE() # Activa el Bluetooth fisico del ESP32
ble.active(True) 

UART_UUID = bluetooth.UUID("6E400001-B5B3-F393-E0A9-E50E24DCCA9E") # codigo de identificación (envia datos en serial)
UART_TX   = (bluetooth.UUID("6E400003-B5B3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_NOTIFY) # Canal de transmision del ESP32 con el PC 
UART_RX   = (bluetooth.UUID("6E400002-B5B3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE) # Canal de recepcion del ESP32 con el PC 
((tx, rx),) = ble.gatts_register_services([(UART_UUID, (UART_TX, UART_RX))]) # Etiquetas para identificar cada canal 

conn_handle = None # Indentificador de conexion activa

def ble_irq(event, data): # Funcion que recibe los datos por Bluetooth
    global conn_handle, ANG_DISPARO # Permite modificar variables que estan fuera de la funcion desde adentro 
    if event == 1: #  Computador conectado
        conn_handle = data[0]
    elif event == 2: # Computador desconectado
        conn_handle = None # Indentificador de conexion activa
        anunciar()   # llama a la funcion anunciar
    elif event == 3: # Dato recibido
        try:
            buf = ble.gatts_read(rx) # lee los datos por el canar RX
            ANG_DISPARO = float(buf.decode().strip()) # pasa el dato recibido a la varaible ANG_DISPARO
        except:
            pass

def anunciar(): # funcion que permite comunicar que el dispositivo esta disponible para conectarse 
    nombre = b"ESP32-SCR" # nombre en bytes
    payload = bytes([len(nombre) + 1, 0x09]) + nombre # Guarda el nombre del dispositivo
    ble.gap_advertise(100000, adv_data=payload)

ble.irq(ble_irq)
anunciar()

# ── Loop principal ─────────────────────
while True:
    utime.sleep_ms(100) 

