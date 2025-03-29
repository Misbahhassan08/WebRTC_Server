
FROM python:3.9

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt


ENV PORT 8080


COPY . /app/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
