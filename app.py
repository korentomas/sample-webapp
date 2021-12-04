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
    
    # Load current count
    f = open("count.txt", "r")
    count = int(f.read())
    f.close()

    # Increment the count
    count += 1

    # Overwrite the count
    f = open("count.txt", "w")
    f.write(str(count))
    f.close()
    
    # Render HTML with count variable
    return render_template("index.html", count=count)

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
        userstoscrap = ('\n'.join('{}' for _ in range(len(userstoscrap))).format(*userstoscrap))
        
        # save the file
        return render_template("index.html", filename=uploaded_file.filename, userstoscrap = userstoscrap)
    else:
        return render_template("index.html")
 
if __name__ == "__main__":
    app.run()