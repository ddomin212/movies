from flask_login import current_user


def query_pinecone_uid(uid, index):
    """
    Query pinecone database by user id. This is used for finding the most relevant database entries for a given user using the dot product similarity metric.

    @param uid - The user id to query.
    @param index - The pinecone index to query.

    @return A list of pinecone database queries with top 5 results. Each query is a dictionary with key / value pairs
    """
    fetch_response = index.fetch(ids=[str(uid)])
    query_vector = fetch_response["vectors"][str(uid)]["values"]
    q = index.query(query_vector, top_k=5, include_metadata=True)
    return q


def parse_pinecone_query(df, q, seen_list):
    """
    Parse pinecone query and return list of movies.

    @param df - database of movies to extract final data from.
    @param q - query from Pinecone's API.
    @param seen_list - list of already seen movies.

    @return list of recommended movies data, sorted by rating in descending order.
    """
    content_recs = {}
    # Returns a list of content recs for each match in the query.
    for i in q["matches"]:
        # Returns a list of content recs for each movie.
        for m, r in list(
            zip(i["metadata"]["movies"], i["metadata"]["ratings"])
        ):
            # Add a string to the list of content recs for the given m.
            if int(m) not in seen_list:
                content_recs[m] = content_recs.get(m, []) + [
                    int(r.split(".")[0])
                ]
    movies = [
        df[df.movie_id == int(k)].values.tolist()[0]
        for k, _ in sorted(content_recs.items(), key=lambda x: -(sum(x[1])))
        if len(df[df.movie_id == int(k)].values.tolist()) > 0
    ][:12]
    return movies


def get_hybrid(index, df, seen_list, userId):
    """
    Get pinecone recommendations for a user. This is a wrapper around query_pinecone_uid and parse_pinecone_query

    @param index - Pinecone index to query.
    @param df - Dataframe containing the movies.
    @param seen_list - list of already seen movies.
    @param userId - id of the user to query.
    """
    q = query_pinecone_uid(userId, index)
    final = parse_pinecone_query(df, q, seen_list)
    return final


def make_recommendations(df, index):
    """
    Make recommendations for the current user. This is a wrapper around get_hybrid for convenience.

    @param df - Dataframe containing the movies.
    @param index - Pinecone index to query.

    @return A dataframe with with the structure [movie_id, vote_average, original_title, image_url].
    """
    fetch_response = index.fetch(ids=[str(current_user.id)])
    query_vector = fetch_response["vectors"][str(current_user.id)]["metadata"][
        "movies"
    ]
    movies = [int(i) for i in query_vector]
    recommendation = get_hybrid(
        index,
        df[["movie_id", "vote_average", "original_title", "image_url"]],
        movies,
        current_user.id,
    )
    return recommendation
