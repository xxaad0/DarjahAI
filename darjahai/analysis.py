from flask import Blueprint, render_template, request,redirect,url_for,flash
from flask_login import login_user, logout_user, login_required, current_user

from .models import User, Character, Tasks, SubTasks

from .extensions import db

from sqlalchemy.exc  import IntegrityError

from sqlalchemy import text

import pandas as pd

import numpy as np

import math
from nltk.corpus import stopwords
import nltk

from typing import List
import re

from collections import Counter

from sklearn.cluster import KMeans

import uuid

from .models import TaskTopTerm
from sqlalchemy import func, desc

EMPTY_ANALYSIS = {"top_terms": [], "cluster_info": [], "cluster_counts": {}, "run_id": None}

def get_tasks(session,user_id:int) -> pd.DataFrame:
    sql= text("""
              select id as task_pk,
              task_name,
              task_category,
              task_status,
              task_priority,
              task_description,
              task_location
              from tasks
              where user_id =:user_id
              order by task_date_created DESC;
              """)
    
    rows = session.execute(sql,{"user_id":user_id}).mappings().all()
    
    df= pd.DataFrame(rows)

    if df.empty:
        return  pd.DataFrame(columns=[
            "task_pk",
            "task_name",
            "task_category",
            "task_status",
            "task_priority",
            "task_description",
            "task_location",
            ])
    
    df["task_name"]= df["task_name"].fillna("")
    df["task_category"]= df["task_category"].fillna("")
    df["task_status"]= df["task_status"].fillna("")
    df["task_priority"]=df["task_priority"].fillna("")
    df["task_description"]=df["task_description"].fillna("")
    df["task_location"] = df["task_location"].fillna("")
    df["text"] = df["task_name"].str.strip() + " " + df["task_category"].str.strip()+ " "+ df["task_status"].str.strip() +" " +  df["task_priority"].str.strip()+" " +  df["task_description"].str.strip()+" " +  df["task_location"].str.strip()
    return df

def tokenize(text:str)-> List[str]:

    if  not isinstance(text,str) or not text.strip():
        return []
    
    text_cleaned= re.sub(r"[^\w\s]", "", text)

    tf_count = text_cleaned.lower().split()

    return tf_count

def vocab(texts_tokens: list[list[str]]) -> tuple[list[str], dict[str,int]]:
    every_token =[t for text in texts_tokens for t in text]

    vocab = sorted(set(every_token))

    conv_to_idx= {term: i for i,term in enumerate(vocab)}

    return vocab, conv_to_idx

def idf(df_tf):

    N= df_tf.shape[0]

    df_t = (df_tf>0).sum(axis=0)
    
    idf = np.log((N + 1) / (df_t + 1)) + 1


    return idf


def builder(session,user_id:int)-> dict:

    run_id = str(uuid.uuid4())


    t1= get_tasks(session,user_id)
    if t1.empty:
        return dict(EMPTY_ANALYSIS)
    

    t1["tokens"] = t1["text"].apply(tokenize)
    texts_tokens= t1["tokens"].tolist()

    vocab_list, term_to_idx = vocab(texts_tokens)

    if not vocab_list:
        return dict(EMPTY_ANALYSIS)
    
    v= len(vocab_list)
    n= len(texts_tokens)

    tf_counts= np.zeros((n,v))

    for i, doc in enumerate(t1["tokens"]):
        counts = Counter(doc)
        for term,c  in counts.items():
            j = term_to_idx[term]
            tf_counts[i,j]=c

    vec_idf= idf(tf_counts)

    tfidf= tf_counts*vec_idf

    cluster_info, labels = cluster_tf_idf(tfidf,vocab_list,k=5,top_words=5)
    t1["cluster"]= labels

    term_scores= tfidf.mean(axis=0)

    x= 20

    idx_top= np.argsort(term_scores)[::-1][:x]

    top_terms= []

    for j in idx_top:
        top_terms.append({"term": vocab_list[j], "score": float(term_scores[j])})
    
    cluster_counts= t1["cluster"].value_counts().sort_index().to_dict()
    
    return {"top_terms":top_terms,"cluster_info":cluster_info,"cluster_counts":cluster_counts,"run_id":run_id}

def cluster_tf_idf(tfidf: np.ndarray,vocab_list: list[str], k: int = 5, top_words: int=8):
    n = tfidf.shape[0]

    if n < 2:
        return [], np.zeros(n, dtype=int)

    
    k  = max(1,min(k,n))

    norms = np.linalg.norm(tfidf,axis=1,keepdims=True)

    tfidf_norms = tfidf/(norms+ 1e-12)

    km = KMeans(n_clusters=k,random_state=42,n_init="auto")

    labels = km.fit_predict(tfidf_norms)

    centers = km.cluster_centers_

    keywords_cluster= []
    for c in range(k):

        index_top= np.argsort(centers[c])[::-1][:top_words]
        keywords= [vocab_list[j] for j in index_top]
        keywords_cluster.append({"cluster":c,"keywords":keywords})

    return keywords_cluster,labels

def save_top_terms(user_id:int,run_id:str,top_terms:list[dict])-> None:
    if not run_id or not top_terms: return

    rows = []

    for i in top_terms:
        term = i.get("term")
        score= i.get("score")
        
        if score is None:
            continue
        if not term:
            continue

        try:
            score_f= float(score)
        except (TypeError,ValueError):
            continue

        rows.append(TaskTopTerm(user_id=user_id,task_version=run_id,task_term=term,task_score=score_f,))

    if not rows: return

    db.session.add_all(rows)

def run_analysis_latest(user_id:int):

    return (
        db.session.query(
        TaskTopTerm.task_version
        )
        .filter(TaskTopTerm.user_id==user_id)
        .order_by(TaskTopTerm.task_computed_at.desc())
        .limit(1).scalar()
        )

def termstorun(user_id:int,run_id:str,limit=20):

    return (
        db.session.query(
        TaskTopTerm
        )
        .filter(TaskTopTerm.user_id==user_id,TaskTopTerm.task_version==run_id)
        .order_by(TaskTopTerm.task_score.desc())
        .limit(limit).all()
        )

def runhistory(user_id: int, limit:int=10):

        return (
        db.session.query(
            TaskTopTerm.task_version,
            func.max(TaskTopTerm.task_computed_at).label("computed_at"),
        )
        .filter(TaskTopTerm.user_id==user_id)
        .group_by(TaskTopTerm.task_version)
        .order_by(desc("computed_at"))
        .limit(limit).all()
        )