FROM python:3.12

WORKDIR /app

COPY src/system /app/system
COPY src/benchmark /app/benchmark
COPY src/runner_check.py /app/runner_check.py
COPY requirements.txt /app/requirements.txt

RUN apt-get update
RUN apt-get install -y libgmp-dev libmpfr-dev libmpc-dev

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y time

CMD ["bash"]
