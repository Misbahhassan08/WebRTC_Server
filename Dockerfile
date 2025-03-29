# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.9

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy local code to the container image.
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . .

CMD exec uvicorn --bind :$PORT --workers 1 --threads 8 main:app