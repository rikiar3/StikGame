import logging
import socket
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import qrcode
import vgamepad as vg
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

APP_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
app = Flask(__name__, template_folder=str(APP_DIR / "templates"))
app.config["SECRET_KEY"] = "local-gamepad-server"
socketio = SocketIO(app, async_mode="threading")

players: dict[str, "Player"] = {}
players_lock = threading.RLock()

BUTTONS = {
    "up": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    "down": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    "left": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    "right": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
    "triangle": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    "circle": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    "cross": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    "square": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    "l1": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    "r1": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    "select": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    "start": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
}
TRIGGERS = {"l2", "r2"}


@dataclass
class Player:
    number: int
    gamepad: Any
    pressed: set[str] = field(default_factory=set)


@app.get("/")
def index():
    return render_template("index.html")


def apply_stick_axis(value: Any) -> float:
    try:
        axis = max(-1.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return 0.0
    return 0.0 if abs(axis) < 0.08 else axis


@socketio.on("connect")
def on_connect():
    sid = request.sid
    try:
        gamepad = vg.VX360Gamepad()
        with players_lock:
            occupied = {player.number for player in players.values()}
            number = next(candidate for candidate in range(1, len(occupied) + 2) if candidate not in occupied)
            players[sid] = Player(number=number, gamepad=gamepad)
    except Exception:
        logger.exception("Tidak dapat membuat virtual gamepad untuk %s", sid)
        return

    logger.info("Player %s terhubung (%s)", number, sid)


@socketio.on("identify")
def on_identify():
    with players_lock:
        player = players.get(request.sid)
        if player is None:
            emit("controller_error", {"message": "Gamepad virtual gagal dibuat. Periksa ViGEmBus dan log server."})
            return
        number = player.number
    emit("player_assigned", {"player": number})


@socketio.on("input")
def on_input(payload):
    if not isinstance(payload, dict):
        return

    with players_lock:
        player = players.get(request.sid)
        if player is None:
            return

        requested = payload.get("buttons", [])
        if not isinstance(requested, list):
            requested = []
        active = {name for name in requested if isinstance(name, str) and name in BUTTONS}
        active_triggers = {name for name in requested if isinstance(name, str) and name in TRIGGERS}

        for name in active - player.pressed:
            player.gamepad.press_button(button=BUTTONS[name])
        for name in player.pressed - active:
            player.gamepad.release_button(button=BUTTONS[name])
        player.pressed = active

        stick = payload.get("leftStick", {})
        if not isinstance(stick, dict):
            stick = {}
        player.gamepad.left_joystick_float(
            x_value_float=apply_stick_axis(stick.get("x", 0)),
            y_value_float=apply_stick_axis(stick.get("y", 0)),
        )
        right_stick = payload.get("rightStick", {})
        if not isinstance(right_stick, dict):
            right_stick = {}
        player.gamepad.right_joystick_float(
            x_value_float=apply_stick_axis(right_stick.get("x", 0)),
            y_value_float=apply_stick_axis(right_stick.get("y", 0)),
        )
        player.gamepad.left_trigger(value=255 if "l2" in active_triggers else 0)
        player.gamepad.right_trigger(value=255 if "r2" in active_triggers else 0)
        player.gamepad.update()


@socketio.on("disconnect")
def on_disconnect(_reason=None):
    with players_lock:
        player = players.pop(request.sid, None)
        if player is not None:
            player.gamepad.reset()
            player.gamepad.update()
            logger.info("Player %s terputus (%s); slot tersedia kembali", player.number, _reason)


def local_ip() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
        if not address.startswith("127."):
            return address
    except OSError:
        pass
    finally:
        probe.close()

    try:
        addresses = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
        for address in addresses:
            candidate = address[4][0]
            if not candidate.startswith("127."):
                return candidate
    except OSError:
        pass
    return "127.0.0.1"


def print_qr(url: str) -> None:
    print(f"\nBuka URL ini dari HP yang berada di jaringan Wi-Fi yang sama:\n  {url}\n")
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_ascii(out=sys.stdout, tty=True, invert=True)
    except (OSError, UnicodeError):
        logger.warning("QR tidak dapat ditampilkan di terminal; gunakan URL di atas.")


if __name__ == "__main__":
    host = "0.0.0.0"
    port = 5000
    url = f"http://{local_ip()}:{port}"
    print_qr(url)
    print("Tekan Ctrl+C untuk menghentikan server. Gunakan hanya di jaringan tepercaya.\n")
    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True)