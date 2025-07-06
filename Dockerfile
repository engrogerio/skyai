FROM alpine:latest

WORKDIR /app

COPY . /app

CMD [ "uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "443", "--ssl-certfile" "./cert.pem", "--ssl-keyfile", "./key.pem", "main.py" ]