import socket
import json
import os

HOST = "0.0.0.0"
PORT = 53533
DB_FILE = "dns_records.json"


def load_records():
    if not os.path.exists(DB_FILE):
        return {}

    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_records(records):
    with open(DB_FILE, "w") as f:
        json.dump(records, f, indent=2)


def parse_message(message):
    fields = {}

    for line in message.strip().splitlines():
        for part in line.strip().split():
            if "=" in part:
                key, value = part.split("=", 1)
                fields[key] = value

    return fields


def make_dns_response(name, value, ttl):
    return (
        "TYPE=A\n"
        f"NAME={name} VALUE={value} TTL={ttl}\n"
    )


records = load_records()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"Authoritative Server listening on UDP port {PORT}")

while True:
    data, client_address = sock.recvfrom(4096)

    try:
        message = data.decode("utf-8")

        print("\nReceived:")
        print(message)

        fields = parse_message(message)

        record_type = fields.get("TYPE")
        name = fields.get("NAME")

        if record_type != "A" or not name:
            sock.sendto(b"ERROR", client_address)
            continue

        # Registration request
        if "VALUE" in fields:
            value = fields["VALUE"]
            ttl = fields.get("TTL", "10")

            records[name] = {
                "TYPE": "A",
                "VALUE": value,
                "TTL": ttl
            }

            save_records(records)

            response = make_dns_response(name, value, ttl)
            sock.sendto(response.encode("utf-8"), client_address)

            print(f"Registered {name} -> {value}")

        # DNS query
        else:
            if name not in records:
                sock.sendto(b"ERROR", client_address)
                continue

            record = records[name]

            response = make_dns_response(
                name,
                record["VALUE"],
                record["TTL"]
            )

            sock.sendto(response.encode("utf-8"), client_address)

            print(f"Returned {name} -> {record['VALUE']}")

    except Exception as e:
        print("Error:", e)
        sock.sendto(b"ERROR", client_address)

