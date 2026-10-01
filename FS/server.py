from flask import Flask, request
import socket

app = Flask(__name__)


def fibonacci(n):
    if n == 0:
        return 0
    if n == 1:
        return 1

    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


@app.route("/register", methods=["PUT"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return "Bad Request\n", 400

    required = ["hostname", "ip", "as_ip", "as_port"]

    for field in required:
        if field not in data:
            return "Bad Request\n", 400

    hostname = data["hostname"]
    ip = data["ip"]
    as_ip = data["as_ip"]

    try:
        as_port = int(data["as_port"])
    except (ValueError, TypeError):
        return "Bad Request\n", 400

    message = (
        f"TYPE=A\n"
        f"NAME={hostname} VALUE={ip} TTL=10\n"
    )

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)

        sock.sendto(
            message.encode("utf-8"),
            (as_ip, as_port)
        )

        response, _ = sock.recvfrom(4096)
        print("AS response:", response.decode("utf-8"))

        sock.close()

    except Exception as e:
        print("Registration error:", e)
        return "Registration failed\n", 500

    return "Registration successful\n", 201


@app.route("/fibonacci", methods=["GET"])
def get_fibonacci():
    number = request.args.get("number")

    if number is None:
        return "Bad Request\n", 400

    try:
        n = int(number)
    except ValueError:
        return "Bad Request\n", 400

    if n < 0:
        return "Bad Request\n", 400

    result = fibonacci(n)

    return str(result) + "\n", 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=9090
    )

