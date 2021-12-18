from flask import Flask, json, render_template, request
import json
import joblib
import numpy as np
import pandas as pd
import re
import os
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

p = re.compile(r'[^\w\s]+')

app = Flask(__name__)

API_ENDPOINT = "https://klouser-test.herokuapp.com/predict"

UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

@app.route("/")
def index():
    
    return render_template("index.html")
 
def parseCSV(filePath):
    csvData = pd.read_csv(filePath)
    csvData['id'] = csvData['id'].astype(str)
    df_scraped = pd.read_csv(r'scrapedId.csv',low_memory=False)
    csvData = csvData.loc[~csvData["id"].isin(df_scraped.Id),:]
    csvData = csvData.dropna(subset=['bio'])
    csvData = csvData[~csvData['bio'].str.isnumeric().fillna(True)]
    

    bios = csvData['bio']
    bios = [p.sub('', x) for x in bios.tolist()]

    r = requests.post(url = API_ENDPOINT, json=bios)
    csvData['wellness'] = json.loads(r.text)
    csvData['wellness'] = csvData['wellness'].replace(['0','1'],['not wellness','wellness'])

    columns = ['Link','Username','Nombre','Bio','Seguidores','Label','Engagement Rate','Seguidos','Website','id','Nro Posteos','category']

    newdf = csvData[['link', 'username', 'fullName', 'bio', 'follower_count', 'wellness', 'engagement_rate', 'following_count','website', 'id', 'posts', 'category_name']]
    newdf = newdf.set_axis(columns, axis=1, inplace=False)
    
    return newdf

@app.route("/", methods=['POST'])
def uploadFiles():
    # get the uploaded file
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        filename=uploaded_file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # set the file path
        uploaded_file.save(file_path)
        labeled_df = parseCSV(file_path)
        
        labeled_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'labeled_data.csv')

        labeled_df.to_csv(labeled_file_path, index=False)

        uploadCsv(labeled_file_path)

        # save the file
        return render_template("index.html", filename=filename, labeled_file_path=labeled_file_path)
    else:
        return render_template("index.html")

@app.route('/predict', methods=['POST'])
def predict():
    json_ = request.json

    json_ = [p.sub('', x) for x in json_]
    json_ = [each_string.lower() for each_string in json_]
    
    classifier = joblib.load('wellness-detection-model.pkl')
    prediction = classifier.predict(json_)
    return json.dumps(prediction.tolist())

def uploadCsv(labeled_file_path):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
            "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

    credentials = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
    client = gspread.authorize(credentials)

    spreadsheet = client.open('test')

    with open(labeled_file_path, 'r',encoding="latin-1") as file_obj:
        content = file_obj.read()
        client.import_csv(spreadsheet.id, data=content)

if __name__ == "__main__":
    app.run()

