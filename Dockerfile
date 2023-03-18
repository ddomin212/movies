FROM python:3.8.0
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE $PORT
CMD ["conda install -c conda-forge scikit-surprise", "gunicorn --workers=4 --bind 0.0.0.0:$PORT app:app"]