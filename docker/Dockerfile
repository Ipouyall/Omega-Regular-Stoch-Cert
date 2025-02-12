FROM python:3.12

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y time

CMD ["bash"]
