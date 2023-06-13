FROM python:3.10.7
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV PORT 5000
EXPOSE $PORT
ENV PAGE_SECRET ')J@NcRfUjXn2r5u8x/A?D(G+KaPdSgVk'
ENV PINECONE_API_KEY b1750a07-3687-490d-a821-78a063d9312f
CMD gunicorn --workers=4 --bind 0.0.0.0:$PORT app:app