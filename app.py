from flask import Flask, render_template, request
import numpy as np
import math
import pandas as pd
import pickle
import bz2

app = Flask(__name__)
fdf = pickle.load(open('data.pkl', 'rb'))
cs_mat_data = bz2.BZ2File("BinaryData", 'rb');
cs_mat = pickle.load(cs_mat_data);
ind = pickle.load(open('ind.pkl', 'rb'))
# ----functions for recommendation system----


def weighted_rating(x, m, C):
    v = x['vote_count']
    R = x['vote_average']
    return round((v/(v+m) * R) + (m/(m+v) * C), 2)


def get_better_recommend(name, ind, cs_mat):
    idx = ind[name]
    cos_sims = np.delete(cs_mat[idx, :], idx)
    cos_index = ind[ind != idx]
    top_25 = pd.Series(cos_sims, cos_index.values).sort_values(
        ascending=False).index[1:26].tolist()
    movies = fdf.reindex(
        top_25)[['original_title', 'vote_count', 'vote_average']]
    vote_counts = movies[movies['vote_count'].notnull()
                         ]['vote_count'].astype('int')
    vote_averages = movies[movies['vote_average'].notnull(
    )]['vote_average'].astype('int')
    C = vote_averages.mean()
    m = vote_counts.quantile(0.60)
    qualified = movies[(movies['vote_count'] >= m) & (
        movies['vote_count'].notnull()) & (movies['vote_average'].notnull())]
    qualified['vote_count'] = qualified['vote_count'].astype('int')
    qualified['vote_average'] = qualified['vote_average'].astype('int')
    qualified['wr'] = qualified.apply(
        (lambda x: weighted_rating(x, m, C)), axis=1)
    qualified = qualified.sort_values('wr', ascending=False).head(10)
    return qualified
# ----------app-------------


@app.route('/', methods=['GET', 'POST'])
def recommendation_wizard():
    if request.method == 'POST':
        recommendation = request.form['recommendationInput']
        try:
            recommendation = get_better_recommend(
                recommendation, ind, cs_mat)[["original_title", "wr"]].values.tolist()
        except KeyError:
            return render_template('404rec.html')
        return render_template('result.html', recommendation=recommendation)
    else:
        return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True)
