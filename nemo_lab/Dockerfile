FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /lab
COPY nemo_lab/requirements.txt /lab/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY payloads.py /lab/payloads.py
COPY webapp/defenses.py webapp/grader.py /lab/webapp/
COPY nemo_lab /lab
CMD ["python", "bench.py"]
