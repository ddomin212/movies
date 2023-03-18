FROM python:3.8.0
COPY . /app
WORKDIR /app
RUN yum install gcc -y
RUN pip install -r requirements.txt
EXPOSE $PORT
CMD gunicorn --workers=4 --bind 0.0.0.0:$PORT app:app