"""Experimental CSI collection, not a validated occupancy or breathing sensor.

Use --help for commands. Record empty and seated sessions separately. Thresholds
must be selected with local recordings and evaluated on held-out sessions.
Signal changes may come from pets, fans, or adjacent rooms rather than people.
"""
import argparse
from collections import deque
import json
import math
from pathlib import Path
import socket
import statistics
import time


def parse_sample(line):
    try:
        sample = json.loads(line)
    except (ValueError, UnicodeDecodeError):
        return None
    if not isinstance(sample, dict) or sample.get("type") != "csi":
        return None
    iq = sample.get("iq")
    if not isinstance(iq, list) or len(iq) != 128:
        return None
    if any(type(v) is not int or not -128 <= v <= 127 for v in iq):
        return None
    if type(sample.get("seq")) is not int or not 0 <= sample["seq"] < 2**32:
        return None
    if type(sample.get("first_word_invalid")) is not bool:
        return None
    return sample


def amplitudes(sample):
    # Always discard the first two complex carriers, keeping the vector layout
    # identical whether ESP-IDF marks the first word invalid or not.
    iq = sample["iq"]
    values = [math.hypot(iq[i], iq[i + 1]) for i in range(4, len(iq), 2)]
    scale = statistics.mean(values)
    if scale == 0:
        return None
    return [value / scale for value in values]


def variation(vectors):
    """Median per-carrier temporal standard deviation after gain normalization."""
    if len(vectors) < 2:
        return None
    if len({len(v) for v in vectors}) != 1 or not vectors[0]:
        raise ValueError("Carrier layouts must match")
    return statistics.median(statistics.pstdev(column) for column in zip(*vectors))


class Window:
    def __init__(self, seconds=10.0):
        self.seconds = seconds
        self.rows = deque()
        self.last_seq = None

    def add(self, sample, now):
        if self.rows and (now - self.rows[-1][0] > 0.5 or
                          sample["seq"] != (self.last_seq + 1) % 2**32):
            self.rows.clear()
        self.last_seq = sample["seq"]
        vector = amplitudes(sample)
        if vector is None:
            self.rows.clear()
            return
        self.rows.append((now, vector))
        while self.rows and now - self.rows[0][0] > self.seconds:
            self.rows.popleft()

    def score(self, now):
        if (len(self.rows) < 100 or now - self.rows[-1][0] > 0.5 or
                self.rows[-1][0] - self.rows[0][0] < self.seconds * 0.9):
            return None
        return variation([row[1] for row in self.rows])


def classify(score, threshold):
    # This is a signal-change heuristic, not proof of human presence.
    if score is not None and threshold is not None and score > threshold:
        return "possible presence (signal change)"
    return "uncertain"


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be finite and greater than zero")
    return number


def probe(args):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        destination = (args.host, args.udp_port)
        print(f"Sending {args.rate:g} packets/s to {destination}; Ctrl+C stops")
        while True:
            started = time.monotonic()
            sock.sendto(b"wifi-csi-probe" * 16, destination)
            time.sleep(max(0, 1 / args.rate - (time.monotonic() - started)))


def capture(args):
    import serial
    if args.plot:
        import matplotlib.pyplot as plt
        plt.ion()
        figure, axis = plt.subplots()
        line, = axis.plot([], [])
        axis.set(xlabel="Elapsed seconds", ylabel="CSI variation (not probability)")
        history = deque(maxlen=300)
    window = Window()
    start = time.monotonic()
    last_report = start
    # Exclusive creation prevents accidental overwriting of training recordings.
    with args.output.open("x", encoding="utf-8") as output, serial.Serial(
            args.port, args.baud, timeout=0.1) as port:
        pending = bytearray()
        while True:
            pending.extend(port.read(min(max(port.in_waiting, 1), 8192)))
            while b"\n" in pending:
                raw, _, rest = pending.partition(b"\n")
                pending = bytearray(rest)
                sample = parse_sample(raw)
                if sample is None:
                    continue
                now = time.monotonic()
                sample.update(label=args.label, host_time=time.time())
                output.write(json.dumps(sample, separators=(",", ":")) + "\n")
                window.add(sample, now)
            if len(pending) > 16384:
                pending.clear()  # Recover from corrupt or non-CSI serial input.
            now = time.monotonic()
            if now - last_report >= 1:
                score = window.score(now)
                print(json.dumps({"status": classify(score, args.threshold), "variation": score}))
                output.flush()
                last_report = now
                if args.plot:
                    history.append((now - start, score if score is not None else float("nan")))
                    line.set_data(*zip(*history))
                    axis.relim()
                    axis.autoscale_view()
            if args.plot:
                if not plt.fignum_exists(figure.number):
                    return
                plt.pause(0.001)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    sender = commands.add_parser("probe", help="Send traffic to the ESP32 IP printed at boot")
    sender.add_argument("host")
    sender.add_argument("--udp-port", type=int, default=5005)
    sender.add_argument("--rate", type=positive, default=50)
    sender.set_defaults(run=probe)
    recorder = commands.add_parser("capture", help="Record USB serial CSI; run probe separately")
    recorder.add_argument("--port", required=True, help="USB serial device")
    recorder.add_argument("--baud", type=int, default=921600)
    recorder.add_argument("--output", type=Path, required=True, help="New JSONL recording path")
    recorder.add_argument("--label", choices=["empty", "seated", "moving", "unknown"], default="unknown")
    recorder.add_argument("--threshold", type=positive, help="Experimental locally calibrated variation threshold; omitted means uncertain")
    recorder.add_argument("--plot", action="store_true")
    recorder.set_defaults(run=capture)
    args = parser.parse_args()
    try:
        args.run(args)
    except KeyboardInterrupt:
        pass
    except (OSError, ImportError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
