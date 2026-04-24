FROM python:3.12-slim
RUN apt-get update && apt-get install -y curl iproute2
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "app.py"]

