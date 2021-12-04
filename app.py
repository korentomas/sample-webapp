from flask import Flask, render_template, request, redirect, url_for
import os
from os.path import join, dirname, realpath
from numpy import int64
import pandas as pd

app = Flask(__name__)

UPLOAD_FOLDER = 'files'
app.config['UPLOAD_FOLDER'] =  UPLOAD_FOLDER

@app.route("/")
def index():
    
    return render_template("index.html")

def parseCSV(filePath):
    csvData = pd.read_csv(filePath)
    csvData['Instagram id'] = csvData['Instagram id'].astype(str)
    
    df_scraped = pd.read_csv(r'scrapedId.csv',low_memory=False)
    
    csvData = csvData.loc[~csvData["Instagram id"].isin(df_scraped.Id),:]

    userstoscrap = csvData.Username.values
    return userstoscrap

@app.route("/", methods=['POST'])
def uploadFiles():
    # get the uploaded file
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
        # set the file path
        uploaded_file.save(file_path)
        userstoscrap = parseCSV(file_path)
        userslen = len(userstoscrap)
        userstoscrap = ('\n'.join('{}' for _ in range(len(userstoscrap))).format(*userstoscrap))
        
        # save the file
        return render_template("index.html", filename=uploaded_file.filename, userstoscrap = userstoscrap, userslen=userslen)
    else:
        return render_template("index.html")
 
if __name__ == "__main__":
    app.run()