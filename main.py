from flask import Flask, render_template, redirect, flash, request, Response, send_from_directory, jsonify
from pandas import DataFrame
import pandas
import os, time, random
from forms import *
import re

from functions import *

app = Flask(__name__)
app.config['CSRF_ENABLED'] = True
app.config['SECRET_KEY'] = "jk3k43l"

MAX_UID = 1
DATASETS = [] # Stores DataFrames for multiuser mode
while len(DATASETS) <= MAX_UID:
    DATASETS.append(DataFrame())
uid = 0 


@app.route("/table")
def table():
    global uid
    if uid != None:
        if DATASETS[uid].shape[1] > 0:
            return DATASETS[uid].head(50).to_html(classes=['main_table'])
        else:
            return ""
    else:
        return ""
  
@app.route("/")
def index():
    if uid is None:
        redirect("/login")
    return render_template("index.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    global uid, DATASETS
    if uid == None:
        redirect("/login")
    form = CSVForm()
    fnm = ""
    if form.validate_on_submit():
        try:
            fileid = "uploads/csv-%s.csv" % (time.time()+random.randint(1,100))
            form.csvf.data.save(fileid)
            if form.rewrite.data == False and DATASETS[uid].shape[0] != 0:
                tmp = pandas.read_csv(fileid, engine='c')
                if form.join_cols.data == False:
                    if len(tmp.columns) == len(DATASETS[uid].columns):
                        DATASETS[uid] = pandas.concat([DATASETS[uid], tmp])
                else:
                        DATASETS[uid] = pandas.concat([DATASETS[uid], tmp], axis=1)
            else:
                DATASETS[uid] = pandas.read_csv(fileid)
            os.remove(fileid)
            fnm = "Uploaded!"
        except Exception as e:
            fnm = "Wrong file content! Error: %s" % str(e)
    return render_template("upload.html", form=form, filename=fnm)

@app.route("/calc", methods=["GET","POST"])
def calc():
    global DATASETS, uid
    if uid == None:
        return redirect("/login")
    form = CALCform()
    result = ""
    if form.validate_on_submit():
        data = form.expr.data
        if data:
            args = re.findall("\w", data)
            cols = DATASETS[uid].columns
            if not all([i in cols for i in args]):
                result = "Missing columns!"
            else:
                method = calculate(args, data)
                result = "Calculated! Using method: %s" % method
    return render_template("calc.html", form=form, result=result)

@app.route("/export.csv")
def export():
    global DATASETS, uid
    if uid != None:
        DATASETS[uid].to_csv(os.path.dirname(os.path.realpath(__file__))+'/static/export.csv')
        return send_from_directory(os.path.dirname(os.path.realpath(__file__))+'/static', 'export.csv')
    else:
        return "Nothing to export!"

@app.route("/delete", methods=['GET','POST'])
def delete():
    global DATASETS, uid
    if uid == None:
        return redirect("/login")
    form = DELform()
    if form.validate_on_submit():
        if uid != None and form.col.data:
            del DATASETS[uid][form.col.data]
            return render_template("delete.html", form=form, result="Deleted!")
        return render_template("delete.html", form=form, result="Nothing to delete!")
    return render_template("delete.html", form=form, result="")

@app.route('/jquery.js', methods=['GET'])
def jq():
     return send_from_directory(os.path.dirname(os.path.realpath(__file__))+'/static', 'jquery.js')


@app.route('/info.json')
def info():
    global uid
    if uid != None:
        data = {'len':DATASETS[uid].shape[0]*DATASETS[uid].shape[1],'cols':DATASETS[uid].shape[1],'rows':DATASETS[uid].shape[0]}
    else:
        data = {'len':0,'cols':0,'rows':0}
    return jsonify(data)

def calculate(args, expr):
    global DATASETS, uid
    data = []
    result = np.array([])
    is_opencl = False
    for a in args:
        arr = np.asarray(DATASETS[uid][a])
        if not (arr.dtype == np.int or arr.dtype == np.float):
            is_opencl = False
            data.append(arr)
        else:
            data.append(arr.astype(np.float32))
        
    if is_opencl:
        ocl = OpenCL()
        if ocl.success:
            ocl.getkernel(args, expr)
            result = ocl.compute(*data)
        method = "OpenCL"
    else:
        lmb = getlambda(args, expr)
        result = np.array(list(map(lmb, *data)))
        method = "IOMAP"
    
    df_new = DataFrame(result.reshape(result.size, 1), columns = ['result(%s)' % expr])
    DATASETS[uid] = pandas.concat([DATASETS[uid], df_new], axis=1)
    return method

# run the app
app.run(debug=True, host="0.0.0.0")

