
FROM python:3.9

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt


ENV PORT 8080


COPY . /app/

CMD exec uvicorn --bind :$PORT --workers 1 --threads 8 main:app
