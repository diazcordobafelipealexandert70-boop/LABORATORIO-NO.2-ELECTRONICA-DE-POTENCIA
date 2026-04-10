import bluetooth
import utime
from machine import Pin

# ── Pines ──────────────────────────────
CRUCE_CERO = Pin(2, Pin.IN, Pin.PULL_UP)
PULSO      = Pin(21, Pin.OUT)

# ── Variable compartida ────────────────
ANG_DISPARO = 90

# ── Anti-rebote ────────────────────────
ultimo_cruce     = 0
TIEMPO_MINIMO_US = 8333

# ── Interrupción cruce cero ────────────
def disparo(pin):
    global ultimo_cruce
    ahora = utime.ticks_us()
    if utime.ticks_diff(ahora, ultimo_cruce) < TIEMPO_MINIMO_US:
        return
    ultimo_cruce = ahora
    t = int(ANG_DISPARO * 8333 / 180)
    utime.sleep_us(t)
    PULSO.on()
    utime.sleep_us(500)
    PULSO.off()

CRUCE_CERO.irq(trigger=Pin.IRQ_FALLING, handler=disparo)

# ── BLE UART ───────────────────────────
ble = bluetooth.BLE()
ble.active(True)

UART_UUID = bluetooth.UUID("6E400001-B5B3-F393-E0A9-E50E24DCCA9E")
UART_TX   = (bluetooth.UUID("6E400003-B5B3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_NOTIFY)
UART_RX   = (bluetooth.UUID("6E400002-B5B3-F393-E0A9-E50E24DCCA9E"), bluetooth.FLAG_WRITE | bluetooth.FLAG_WRITE_NO_RESPONSE)
((tx, rx),) = ble.gatts_register_services([(UART_UUID, (UART_TX, UART_RX))])

conn_handle = None

def ble_irq(event, data):
    global conn_handle, ANG_DISPARO
    if event == 1:                          # Conectado
        conn_handle = data[0]
    elif event == 2:                        # Desconectado
        conn_handle = None
        anunciar()                          # Vuelve a anunciar
    elif event == 3:                        # Dato recibido
        try:
            buf = ble.gatts_read(rx)
            ANG_DISPARO = float(buf.decode().strip())
        except:
            pass

def anunciar():
    nombre = b"ESP32_lab2"
    payload = bytes([len(nombre) + 1, 0x09]) + nombre
    ble.gap_advertise(100000, adv_data=payload)

ble.irq(ble_irq)
anunciar()

# ── Loop principal ─────────────────────
while True:
    utime.sleep_ms(100)
