FROM python:3.12.6-alpine3.19

EXPOSE 3000

WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py server.py
COPY processes processes
COPY socketstdout socketstdout
COPY auth auth
COPY handler handler

ENTRYPOINT [ "python", "server.py" ]
