from wtforms import FileField, BooleanField, TextField
from flask_wtf import Form

class CSVForm(Form):
    csvf = FileField('file')
    rewrite = BooleanField('rewrite')
    join_cols = BooleanField('join_cols')

class CALCform(Form):
    expr = TextField('expr')

class DELform(Form):
    col = TextField('col')
