import math
from flask import render_template
from flask_login import current_user


def update_pinecone_vector(rating, pinecone_id, vector, index, id, suid):
    """
    Update or insert a pinecone vector.

    @param rating - int between 0 and 5
    @param pinecone_id - the index of user's vector to be changed
    @param vector - dict with user's vector data from pinecone db
    @param index - the pinecone index which holds the vector to be changed
    @param id - id of movie to be updated
    @param suid - id of user to be updated
    """
    if int(rating) < 0 or int(rating) > 5:
        return (
            render_template(
                "404.html",
                error="400 Bad Request",
                message="Thy critique be between 0 and 5",
            ),
            400,
        )
    vector_meta = vector["metadata"]
    if id not in vector_meta["movies"]:
        vector_meta["movies"].append(str(id))
        vector_meta["ratings"].append(str(rating) + ".0")
    else:
        vector_meta["ratings"][vector_meta["movies"].index(id)] = (
            str(rating) + ".0"
        )
    vector["values"][pinecone_id] = int(rating)
    index.update(
        id=suid,
        values=vector["values"],
        set_metadata=vector_meta,
    )


def get_pinecone_vector(index, id, pinecone_map, suid):
    """
    Fetch the pinecone vector and remap the movie id to the index of the pinecone vector to be changed.

    @param index - pinecone index to be queried
    @param id - id of the movie to be processed
    @param pinecone_map - map of movie_ids to pinecone vector indexes
    @param suid - id of the current user

    @return the vector object from pinecone and a remapped movie id
    """
    pinecone_id = pinecone_map[int(id)]
    vector = index.fetch(ids=[suid])["vectors"][suid]
    return vector, pinecone_id


def movieController(id, request, df, index, pinecone_map):
    """
    Controller for movie. It is called by ajax to update or insert a pinecone. If user is authenticated it will return True otherwise it will return False

    @param id - id of movie to be updated
    @param request - Flask request object
    @param df - dataframe containing movie data
    @param index - pinecone index to be queried
    @param pinecone_map - map of movie_ids to pinecone vector indexes

    @return A webpage with the movie data and a recommendation carousel.
    """
    # This method is called by the user to update the pinecone.
    if current_user.id:
        exists = False
        suid = str(current_user.id)
        vector, pinecone_id = get_pinecone_vector(
            index, id, pinecone_map, suid
        )
        # Check if the user is authenticated
        if current_user.is_authenticated:
            # Check if the pinecone_id is present in the vector
            if vector["values"][pinecone_id] != 0:
                exists = True
        # POST method POST and upsert pinecone.
        if request.method == "POST":
            rating = request.form.get("rating")
            update_pinecone_vector(
                rating, pinecone_id, vector, index, id, suid
            )
    movie = df[df.movie_id == int(id)].to_dict(orient="records")[0]
    recommendation = movie["content_recs"]
    return render_template(
        "movie.html",
        movie=movie,
        recommendation=recommendation,
        exists=exists,
    )


def parse_pinecone_data(df, data):
    """
    Parse and return ratings for movies with the necessary additional data, such as the average rating or image URL.

    @param df - dataframe with additional movie data
    @param data - data returned by the Pinecone API

    @return A list with with the structure [movie_id, vote_average, original_title, image_url].
    """
    movies = data["movies"]
    movies = [
        i for i in movies if len(df[df.movie_id == int(i)]) > 0
    ]  # TODO: Fix this
    ratings = data["ratings"]
    recommendation = []
    # Add recommendation to recommendation list.
    for m, r in zip(movies, ratings):
        m = int(m)
        qc = df.query("movie_id == @m")
        # Add recommendation to recommendation list.
        if len(qc.values) > 0:
            q1 = qc.original_title.values[0]
            q2 = qc.image_url.values[0]
            recommendation.append([m, r, q1, q2])
        else:
            continue
    return recommendation


def ratingsController(df, index):
    """
    A controller for the ratings page. It will fetch the user's ratings from the pinecone index and
    return a list of ratings with the necessaryadditional data, such as the average rating or image URL.

    @param df - dataframe containing additional movie data
    @param index - pinecone index to be queried

    @return Renders a webpage with a movie carousel for all the movies the user has already rated.
    """
    suid = str(current_user.id)
    data = index.fetch(ids=[suid])["vectors"][suid]["metadata"]
    ratings = parse_pinecone_data(df, data)
    # images = [
    #     m, r, df.query('movie_id == @m').values[0]

    #     if len(df.query('movie_id == @i').values) > 0
    # ]
    # ratings = list(zip(movies, ratings, movie_names, images))
    nom = len(ratings)
    carousels = math.ceil(nom / 6) if nom > 6 else 1
    items = 6
    return render_template(
        "listing.html",
        recommendation=ratings,
        index="rating",
        carousels=carousels,
        items=items,
        nom=nom,
        heading="Thine most cherished cinema",
    )
