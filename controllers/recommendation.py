import math
from flask import render_template
from functions.colaborative import make_recommendations
from flask_login import current_user


def searchController(df, query):
    """
    Search for movies that match the query string and return a list of them.

    @param df - a dataframe with with the structure [movie_id, vote_average, original_title, image_url]
    @param query - string to search for in a movie's title

    @return A webpage with the search results.
    """
    if query == "":
        return (
            render_template(
                "404.html",
                error="400 Bad Request",
                message="Thy query be empty",
            ),
            400,
        )
    sdf = df[df["original_title"].str.lower().str.contains(query, na=False)]
    listed = sdf[
        ["movie_id", "vote_average", "original_title", "image_url"]
    ].values.tolist()
    nom = len(listed)
    carousels = math.ceil(nom / 6) if nom > 6 else 1
    items = 6
    return render_template(
        "listing.html",
        recommendation=listed,
        carousels=carousels,
        items=items,
        nom=nom,
        heading="Thy search results",
    )


def indexController(request, df, index, basic_recommendation):
    """
    Controller for the index page. If the request is a POST searches for recommendations and returns the search results.

    @param request - the Flask request to be processed
    @param df - the dataframe that contains the pictures to be indexed
    @param index - the pinecone index to be queried
    @param basic_recommendation - the basic recommendations for any user (and anons)

    @return A webpage with a carousel of recommendations.
    """
    # This view shows the recommendation page.
    if request.method == "POST":
        query = request.form.get("query").lower()
        return searchController(df, query)
    else:
        # Returns a recommendation object for the current user.
        if current_user.is_authenticated:
            recommendation = make_recommendations(df, index)
        else:
            recommendation = basic_recommendation
        carousels = 2
        items = len(recommendation) // (carousels)
        return render_template(
            "listing.html",
            recommendation=recommendation,
            carousels=carousels,
            items=items,
            nom=len(recommendation),
            heading="A Shakespearean Recommendation",
            index="index",
            message="""Hark! This repository of moving pictures is a veritable treasure trove,
                                        where thou mayst procure a fresh array of films to regale thyself and
                                        thy companions on a Friday eve. Let it be known, however, that no such
                                        thing as "Netflix and chill" shall be permitted!""",
        )
