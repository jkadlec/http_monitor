FROM python:3.7-alpine

COPY . /app
ENV PYTHONPATH=/app

CMD python3 /app/main.py $INPUT_FILE
