import os
import pinecone


def init_pinecone():
    index_name = "movie-testing"

    # initialize connection to pinecone (get API key at app.pinecone.io)
    pinecone.init(
        api_key=os.getenv("PINECONE_API_KEY"),
        environment="us-central1-gcp",  # find next to api key in console
    )
    index = pinecone.Index(index_name)

    return index
