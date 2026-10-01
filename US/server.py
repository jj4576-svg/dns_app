from flask import Flask, request
import socket
import requests

app = Flask(__name__)


def query_authoritative_server(hostname, as_ip, as_port):
    message = f"TYPE=A\nNAME={hostname}\n"

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(3)

    try:
        sock.sendto(
            message.encode("utf-8"),
            (as_ip, as_port)
        )

        response, _ = sock.recvfrom(4096)
        response = response.decode("utf-8")

    finally:
        sock.close()

    if response.strip() == "ERROR":
        return None

    # Expected response:
    # TYPE=A
    # NAME=fibonacci.com VALUE=127.0.0.1 TTL=10

    for part in response.split():
        if part.startswith("VALUE="):
            return part.split("=", 1)[1]

    return None


@app.route("/fibonacci", methods=["GET"])
def fibonacci():
    hostname = request.args.get("hostname")
    fs_port = request.args.get("fs_port")
    number = request.args.get("number")
    as_ip = request.args.get("as_ip")
    as_port = request.args.get("as_port")

    if not all([hostname, fs_port, number, as_ip, as_port]):
        return "Bad Request\n", 400

    try:
        fs_port = int(fs_port)
        as_port = int(as_port)
        int(number)
    except ValueError:
        return "Bad Request\n", 400

    try:
        fs_ip = query_authoritative_server(
            hostname,
            as_ip,
            as_port
        )
    except Exception as e:
        print("DNS query error:", e)
        return "DNS query failed\n", 500

    if fs_ip is None:
        return "Hostname not found\n", 404

    try:
        url = f"http://{fs_ip}:{fs_port}/fibonacci?number={number}"

        response = requests.get(
            url,
            timeout=3
        )

        return response.text, response.status_code

    except Exception as e:
        print("Fibonacci server error:", e)
        return "Fibonacci server unavailable\n", 500


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8080
    )

