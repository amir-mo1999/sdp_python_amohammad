FROM python:3.10-slim

RUN python -m pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 5000

CMD ["flask", "--app", "backend", "run"]