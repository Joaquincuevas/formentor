# Controlador simulado (MQTT)

Emula una ESP32-CAM real hablando el mismo contrato MQTT, para desarrollar y
demostrar el Sistema de Administración **sin tener el hardware**.

## Uso

```bash
cd simulator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python controller_sim.py --id ctrl-demo1 --lockers 3 --broker localhost
```

Necesita un broker MQTT (Mosquitto local o `broker.hivemq.com`). El `--id` debe
coincidir con un controlador creado en el Sistema de Administración.

## Comandos interactivos

```
open 1 2 0 5 1     # intenta abrir el casillero 1 con la clave [2,0,5,1]
close 1            # cierra el casillero 1
keys               # muestra las claves recibidas del admin
quit
```

## Prueba de punta a punta (sin hardware)

1. `brew services start mosquitto`
2. Backend: `python manage.py runserver` + `python manage.py seed_demo`
3. Simulador: `python controller_sim.py --id ctrl-demo1 --lockers 3`
   → el admin lo marca como conectado y le envía las claves.
4. En el frontend, edita la clave de un casillero → verás el mensaje llegar al
   simulador. Usa `open ...` con esa clave → el evento aparece en el dashboard.
