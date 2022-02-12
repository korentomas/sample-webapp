from typing import Type
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
 
@app.route("/part1")
def part1():
    return render_template("part1.html")

@app.route("/part2")
def part2():
    return render_template("part2.html")

# @app.route("/part2test")
# def part2test():
#     return render_template("part2test.html")


def removedec(n):
    x = re.match("^(.*?)\.", n)
    if x :
      return(x.group(1))

def parseCSVPB(filePath):
    csvData = pd.read_csv(filePath,low_memory=False)
    print(csvData.id)
    csvData = csvData.loc[csvData.id.notnull(),:]
    csvData['id'] = csvData['id'].astype(str)
    csvData['id'] = csvData['id'].apply(removedec)

    df_scraped = pd.read_csv(r'scrapedId.csv',low_memory=False)
    csvData = csvData.loc[~csvData["id"].isin(df_scraped.id),:]

    userstoscrap = csvData.username.values
    csvDataId = csvData[['id']]

    df_scraped = df_scraped.append(csvDataId)
    df_scraped = df_scraped.drop_duplicates(keep='first')
    
    df_scraped.to_csv(r'scrapedId.csv', index=False)
    return userstoscrap

def parseCSV(filePath):
    csvData = pd.read_csv(filePath)
    csvData['id'] = csvData['id'].astype(str)
    csvData = csvData.dropna(subset=['bio'])
    csvData = csvData[~csvData['bio'].str.isnumeric().fillna(True)]
    
    # si csvData no tiene filas significa que todos los ids ya fueron scrapeados.

    bios = csvData['bio']
    bios = [p.sub('', x) for x in bios.tolist()]

    r = requests.post(url = API_ENDPOINT, json=bios)
    
    csvData['wellness'] = json.loads(r.text)
    csvData['wellness'] = csvData['wellness'].replace(['0','1'],['not wellness','wellness'])

    columns = ['Link','Username','Nombre','Bio','Seguidores','Label','Engagement Rate','Seguidos','Website','id','Nro Posteos','category']

    newdf = csvData[['link', 'username', 'fullName', 'bio', 'follower_count', 'wellness', 'engagement_rate', 'following_count','website', 'id', 'posts', 'category_name']]
    newdf = newdf.set_axis(columns, axis=1, inplace=False)
    
    newdf = newdf.drop_duplicates(keep='first')

    return newdf

def parseCSVnew(filePath, filePathPB):
    csvData = pd.read_csv(filePath, low_memory=False)
    csvData = csvData.loc[csvData.id.notnull(),:]
    csvData['id'] = csvData['id'].astype(str)
    csvData['id'] = csvData['id'].apply(removedec)
    csvData = csvData.dropna(subset=['bio'])
    csvData = csvData[~csvData['bio'].str.isnumeric().fillna(True)]
    
    # si csvData no tiene filas significa que todos los ids ya fueron scrapeados.

    sourceData = pd.read_csv(filePathPB, low_memory=False)
    sourceData = sourceData.loc[sourceData['query'].notnull(),:]
    sourceData.id = sourceData.id.astype(str)
    sourceData.id = sourceData.id.apply(removedec)
    sourceData['query'] = sourceData['query'].apply(lambda x: re.match(r'(?:(?:http|https):\/\/)?(?:www\.)?(?:instagram\.com|instagr\.am)\/([A-Za-z0-9-_\.]+)', x).group(1))
    sourceData = sourceData[['query', 'id','profileUrl', 'username']]


    bios = csvData['bio']
    bios = [p.sub('', x) for x in bios.tolist()]

    r = requests.post(url = API_ENDPOINT, json=bios)
    
    csvData['wellness'] = json.loads(r.text)
    csvData['wellness'] = csvData['wellness'].replace(['0','1'],['not wellness','wellness'])

    columns = ['Link','Username','Nombre','Bio','Seguidores','Label','Engagement Rate','Seguidos','Website','id','Nro Posteos','category']

    newdf = csvData[['link', 'username', 'fullName', 'bio', 'follower_count', 'wellness', 'engagement_rate', 'following_count','website', 'id', 'posts', 'category_name']]
    newdf = newdf.set_axis(columns, axis=1, inplace=False)
    
    newdf = newdf.drop_duplicates(keep='first')

    attach_source = []
    for _, row in newdf.iterrows():
        attach_source.append(sourceData.loc[sourceData.username == row.Username,'query'].values)
    newdf['Source'] = attach_source

    return newdf

@app.route("/part1", methods=['POST'])
def uploadFilesPB():
    # get the uploaded file
    uploaded_file = request.files['filePB']
    if uploaded_file.filename != '':
        filename=uploaded_file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # set the file path
        uploaded_file.save(file_path)
        userstoscrap = parseCSVPB(file_path)
        userslen = len(userstoscrap)
        userstoscrap = ('\n'.join('{}' for _ in range(len(userstoscrap))).format(*userstoscrap))

        # save the file
        return render_template("part1.html", filename=filename, userslen=userslen, userstoscrap=userstoscrap)
    else:
        return render_template("part1.html")



# @app.route("/part2", methods=['POST'])
# def uploadFiles():
#     # get the uploaded file
#     uploaded_file = request.files['file']
#     if uploaded_file.filename != '':
#         filename=uploaded_file.filename
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         # set the file path
#         uploaded_file.save(file_path)
#         labeled_df = parseCSV(file_path)
        
#         labeled_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'labeled_data.csv')

#         labeled_df.to_csv(labeled_file_path, index=False)

#         uploadCsv(labeled_file_path)

#         # save the file
#         return render_template("part2.html", filename=filename, labeled_file_path=labeled_file_path)
#     else:
#         return render_template("part2.html")

@app.route("/part2", methods=['POST'])
def uploadFilesTest():
    # get the uploaded file
    uploaded_file = request.files['file']
    uploaded_filePB = request.files['filePB']
    if uploaded_file.filename != '' and uploaded_filePB.filename != '':

        filename=uploaded_file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)

        filenamePB=uploaded_filePB.filename
        file_pathPB = os.path.join(app.config['UPLOAD_FOLDER'], filenamePB)
        uploaded_filePB.save(file_pathPB)

        labeled_df = parseCSVnew(file_path, file_pathPB)
        # set the file path

        labeled_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'labeled_data.csv')

        labeled_df.to_csv(labeled_file_path, index=False)

        uploadCsv(labeled_file_path)

        # save the file
        return render_template("part2.html", filename=filename, labeled_file_path=labeled_file_path)
    else:
        return render_template("part2.html")

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


@app.route('/pbDone',methods=['POST'])
def githubIssue():
    data = request.json
    #print(data)
    try:
        #print(data['resultObject']['csvURL'])
        if list(data['resultObject'].keys())[0] == 'csvURL':
            resultFile = pd.read_csv(data['resultObject']['csvURL'], low_memory=False)
            print(resultFile.head())
        else:
            print('no se, está raro:', data)
    except ValueError or TypeError:
        print('eror:', ValueError, TypeError)
    return data


if __name__ == "__main__":
    app.run()

