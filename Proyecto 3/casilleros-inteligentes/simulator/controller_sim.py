"""Controlador de casilleros SIMULADO por MQTT.

Emula el comportamiento de la ESP32-CAM real para poder desarrollar y demostrar el
Sistema de Administracion sin tener el hardware. Habla exactamente el mismo contrato
MQTT que el firmware (ver docs/mqtt.md), asi que el admin no distingue si esta
hablando con un simulador o con una ESP32 real.

Que hace:
  - Al arrancar publica sync/request anunciando cuantos casilleros tiene.
  - Se suscribe a keys, model y sync/response y los aplica en memoria.
  - Manda heartbeat cada 60 s (configurable).
  - Por consola puedes simular que alguien ingresa una clave: si coincide con la
    del casillero, publica un evento 'open'; si no, 'denied'.

Uso:
    python controller_sim.py --id ctrl-demo1 --lockers 3 --broker localhost

Comandos en consola (mientras corre):
    open <locker> <g1> <g2> <g3> <g4>   ej: open 1 2 0 5 1
    close <locker>
    keys                                muestra las claves actuales
    quit
"""
import argparse
import json
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SimController:
    def __init__(self, controller_id, n_lockers, broker, port, heartbeat):
        self.id = controller_id
        self.n_lockers = n_lockers
        self.heartbeat = heartbeat
        self.keys = {i: None for i in range(1, n_lockers + 1)}  # locker -> [g,g,g,g]
        self.open_state = {i: False for i in range(1, n_lockers + 1)}
        self.model_version = None

        self.client = mqtt.Client(client_id=self.id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.will_set(self._t("heartbeat"), payload="", retain=False)
        self.client.connect(broker, port, keepalive=60)

    def _t(self, suffix):
        return f"casilleros/{self.id}/{suffix}"

    # ---- MQTT ----
    def _on_connect(self, client, userdata, flags, rc):
        print(f"[{self.id}] conectado al broker (rc={rc})")
        for sub in ("keys", "model", "sync/response"):
            client.subscribe(self._t(sub))
        self.announce()

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode() or "{}")
        except json.JSONDecodeError:
            return
        topic = msg.topic.split("/")[-1]
        if msg.topic.endswith("sync/response"):
            for lk in payload.get("lockers", []):
                self.keys[lk["locker"]] = lk.get("key")
            self.model_version = payload.get("model_version")
            print(f"[{self.id}] sync recibido. claves={self.keys} "
                  f"modelo=v{self.model_version}")
        elif topic == "keys":
            self.keys[payload["locker"]] = payload["key"]
            print(f"[{self.id}] clave actualizada casillero "
                  f"{payload['locker']} -> {payload['key']}")
        elif topic == "model":
            self.model_version = payload.get("model_version")
            print(f"[{self.id}] modelo actualizado a v{self.model_version} "
                  f"({payload.get('model_url')})")

    # ---- acciones del controlador ----
    def announce(self):
        self.client.publish(self._t("sync/request"), json.dumps({
            "controller_id": self.id,
            "active_lockers": self.n_lockers,
            "firmware": "sim-0.1.0",
        }))
        print(f"[{self.id}] anunciado ({self.n_lockers} casilleros)")

    def try_open(self, locker, attempt):
        expected = self.keys.get(locker)
        if expected is None:
            print(f"  casillero {locker} sin clave asignada aun")
            return
        if list(attempt) == list(expected):
            self.open_state[locker] = True
            self._event(locker, "open")
            print(f"  ✓ casillero {locker} ABIERTO")
        else:
            self._event(locker, "denied")
            print(f"  ✗ clave incorrecta (esperada {expected})")

    def close(self, locker):
        self.open_state[locker] = False
        self._event(locker, "close")
        print(f"  casillero {locker} cerrado")

    def _event(self, locker, action):
        self.client.publish(self._t("event"), json.dumps({
            "locker": locker, "action": action, "ts": now_iso(),
        }))

    def _heartbeat_loop(self):
        while True:
            self.client.publish(self._t("heartbeat"),
                                json.dumps({"ts": now_iso(), "rssi": -60}))
            time.sleep(self.heartbeat)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", default="ctrl-demo1")
    ap.add_argument("--lockers", type=int, default=3)
    ap.add_argument("--broker", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--heartbeat", type=int, default=60)
    args = ap.parse_args()

    ctrl = SimController(args.id, args.lockers, args.broker, args.port, args.heartbeat)
    ctrl.client.loop_start()
    threading.Thread(target=ctrl._heartbeat_loop, daemon=True).start()

    print("\nComandos: open <lk> <g1 g2 g3 g4> | close <lk> | keys | quit\n")
    try:
        while True:
            parts = input("> ").strip().split()
            if not parts:
                continue
            cmd = parts[0]
            if cmd == "quit":
                break
            elif cmd == "keys":
                print(" ", ctrl.keys)
            elif cmd == "open" and len(parts) == 6:
                ctrl.try_open(int(parts[1]), [int(x) for x in parts[2:6]])
            elif cmd == "close" and len(parts) == 2:
                ctrl.close(int(parts[1]))
            else:
                print("  comando invalido")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        ctrl.client.loop_stop()
        print("\nsimulador detenido")


if __name__ == "__main__":
    main()
