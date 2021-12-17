from flask import Flask, json, render_template, request
import json
from numpy import int64
import joblib
import numpy as np
import pandas as pd
import re
from nltk.corpus import stopwords

import matplotlib.pyplot as plt

from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split, cross_val_score, cross_val_predict, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import chi2, SelectKBest
from sklearn.svm import LinearSVC
from sklearn import metrics
from sklearn.metrics import plot_confusion_matrix


app = Flask(__name__)

UPLOAD_FOLDER = 'files'

@app.route("/")
def index():
    
    return render_template("index.html")
 
@app.route('/predict', methods=['POST'])
def predict():
    json_ = request.json

    p = re.compile(r'[^\w\s]+')

    json_ = [p.sub('', x) for x in json_]
    json_ = [each_string.lower() for each_string in json_]
    
    classifier = joblib.load('wellness-detection-model.pkl')
    prediction = classifier.predict(json_)
    return json.dumps(prediction.tolist())

if __name__ == "__main__":
    app.run()