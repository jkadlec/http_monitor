FROM python:3.7-alpine

RUN pip3 install pytest

COPY . /app

ENV PYTHONPATH=/app

CMD pytest /app/tests.py
