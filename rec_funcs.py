import numpy as np
import pandas as pd
from surprise import Reader
from surprise import Dataset
from surprise import SVD


def weighted_rating(x, m, C):
    v = x['vote_count']
    R = x['vote_average']
    return round((v/(v+m) * R) + (m/(m+v) * C), 2)


def get_rec(df, name, ind, cs_mat):
    cos_sims = np.delete(cs_mat[name, :], name)
    cos_index = ind[ind != name]
    return pd.Series(cos_sims, cos_index.values).sort_values(ascending=False)


def train_svd(ratings):
    reader = Reader(rating_scale=(0, 10))
    data = Dataset.load_from_df(
        ratings[['userId', 'tmdbId', 'rating']], reader)
    trainset = data.build_full_trainset()
    svd = SVD()
    svd.fit(trainset)
    return svd


def minmax(df):
    df_norm = (df-df.min())/(df.max()-df.min())
    return df_norm*11


def get_basic_rec(fdf, top_25=None, count=10):
    if top_25:
        movies = fdf.reindex(
            top_25)[['original_title', 'vote_count', 'vote_average', "image_url", "movie_id"]]
    else:
        movies = fdf[['original_title', 'vote_count',
                      'vote_average', "image_url", "movie_id"]]
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
    qualified = qualified.sort_values('wr', ascending=False).head(count)
    return qualified


def merge_res(textrec, featrec):
    dfrc = textrec.to_frame().merge(featrec.rename(1), left_index=True, right_index=True)
    dfrc[0] = minmax(dfrc[0])
    return dfrc.sum(1).sort_values(ascending=False)


def get_better_rec(df, name, ind, cs_mat_f, cs_mat, count=10):
    txtrec = get_rec(df, name, ind, cs_mat)
    featrec = get_rec(df, name, ind, cs_mat_f)
    top_25 = merge_res(txtrec, featrec).index[1:26].tolist()
    return get_basic_rec(df, top_25, count)


def get_hybrid(alg, df, indices, cs_mat, cs_mat_f, ratings, userId, count=10):
    seen_list = list(set(ratings[ratings['userId'] == userId].tmdbId))
    full_content_rec = []
    for movie in seen_list:
        if movie < len(indices):
            full_content_rec += list(get_better_rec(df,
                                     int(movie), indices, cs_mat_f, cs_mat).index)
    full_content_rec = list(set(full_content_rec))
    full_content_rec_names = [df.loc[i]["original_title"]
                              for i in full_content_rec]
    rec_preds = []
    for rec in full_content_rec:
        rec_preds.append(alg.predict(userId, rec).est)
    final_recommendations = pd.Series(
        rec_preds, index=full_content_rec_names).sort_values(ascending=False)
    return df[(df.original_title.isin(final_recommendations.index)) & (~df.movie_id.isin(seen_list))][['original_title', "vote_average", "image_url", "movie_id"]].head(count)
