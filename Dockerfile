FROM python:3.8.0
COPY . /app
WORKDIR /app
RUN apt-get update && \
    apt-get install -y build-essential
RUN pip install cython
RUN pip install -r requirements.txt
EXPOSE $PORT
CMD gunicorn --workers=4 --bind 0.0.0.0:$PORT app:app