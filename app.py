from flask import Flask, render_template, request
import numpy as np
import math
import pandas as pd
import pickle
import bz2

app = Flask(__name__)
fdf = pickle.load(open('data.pkl', 'rb'))
cs_mat_data = bz2.BZ2File("csf", 'rb')
cs_mat_f = pickle.load(cs_mat_data)
cs_mat_data = bz2.BZ2File("cs", 'rb')
cs_mat = pickle.load(cs_mat_data)
ind = pickle.load(open('ind.pkl', 'rb'))
# ----functions for recommendation system----


def weighted_rating(x, m, C):
    v = x['vote_count']
    R = x['vote_average']
    return round((v/(v+m) * R) + (m/(m+v) * C), 2)


def get_rec(name, ind, cs_mat):
    idx = ind[name]
    cos_sims = np.delete(cs_mat[idx, :], idx)
    cos_index = ind.drop(name, 0)
    return pd.Series(cos_sims, cos_index.values).sort_values(ascending=False)


def minmax(df):
    df_norm = (df-df.min())/(df.max()-df.min())
    return df_norm*11


def merge_res(textrec, featrec):
    dfrc = textrec.to_frame().merge(featrec.rename(1), left_index=True, right_index=True)
    dfrc[0] = minmax(dfrc[0])
    return dfrc.sum(1).sort_values(ascending=False)


def get_better_recommend(name, ind, cs_mat_f, cs_mat):
    txtrec = get_rec(name, ind, cs_mat)
    featrec = get_rec(name, ind, cs_mat_f)
    top_25 = merge_res(txtrec, featrec).index[1:26].tolist()
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
                recommendation, ind, cs_mat_f, cs_mat)[["original_title", "wr"]].values.tolist()
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
