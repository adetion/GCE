FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gce/ gce/
COPY GCE_main.py .
COPY config.yaml.example .
COPY narratives.yaml .

ENV GCE_API_KEY=""

EXPOSE 8080

ENTRYPOINT ["python", "GCE_main.py"]
CMD ["--config", "config.yaml", "--offline"]
