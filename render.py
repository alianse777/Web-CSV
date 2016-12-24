import numpy as np
import string, csv, traceback, re

class TableFrame():
    def __init__(self):
        while len(data) % len(columns) != 0:
            data.append("NaN")
        self.html = ""
        self.csize = None
        self.cols = columns
        self.table = np.array(columns)
        self.table = np.concatenate((self.table, data), axis=0)
        self.table.resize(self.table.size/len(columns), len(columns))
        try:
             import pyopencl as cl
             self.ctx = cl.create_some_context()
             self.queue = cl.CommandQueue(self.ctx)
             self.mf = cl.mem_flags
             self.ocl = True
        except ImportError:
             self.ocl = False

    def build(self):
        tb = "<style>text-align: center</style><table border=1 style='width:100%'>"
        if self.table.shape[0] < 1000:
            for row in self.table:
                tb += "<tr>"
                for col in row:
                    if col != "":
                        tb += "<td>%s</td>" % col
                tb += "</tr>"
        else:
            for row in self.table[0:14]:
                tb += "<tr>"
                for col in row:
                    if col != "":
                        tb += "<td>%s</td>" % col
                tb += "</tr>"
            tb += "</table><h3>...</h3>"
            tb += "<table border=1 style='width:100%'>"
            for row in self.table[self.table.shape[0] - 14: self.table.shape[0]]:
                tb += "<tr>"
                for col in row:
                    if col != "":
                        tb += "<td>%s</td>" % col
                tb += "</tr>"
        self.html = tb + "</table>"

    def show(self):
        return self.html

    def append(self, data, headers):
        data = np.array(data)
        data.resize(data.size, len(self.cols))
        self.table = np.concatenate((self.table, data), axis=0)

    def refactor(self, data, name=None):
        if name:
            data = [name] + data
        while len(data) < self.table.shape[0]:
            data.append('')
        if len(data) > self.table.shape[0]:
            data = data[0:self.table.shape[0]]
        data = np.array([data]).reshape(len(data), 1)
        try:
            self.table = np.hstack((self.table, data))
            return 0
        except ValueError:
            return -1

    def export(self):
        io = open("static/export.csv", "w")
        writer = csv.writer(io)
        writer.writerows(self.table)
        io.close()

    def getcol(self, name, dtype=None):
        size = self.csize
        try:
            index = list(self.table[0]).index(name)
        except ValueError:
            return -1
        col = []
        if size:
            for row in self.table[1:size+1]:
                col.append(row[index])
        else:
            for row in self.table[1:self.table.shape[0]]:
                col.append(row[index])
        if dtype:
            arr = np.array(col)
            return arr.astype(dtype)
        return col

    def delcol(self, name):
        try:
            index = np.where(self.table == name)[1][0]
            self.table = np.delete(self.table, index, 1)
            return 0
        except:
            return -1

    def calc(self, cols, expr, size=None):
        global OPENCL_SUPPORT
        size = self.table.shape[0]
        try:
            lmb = getlambda(expr, cols)
            vector = [np.array(self.getcol(c, dtype=np.float)) for c in cols]
            self.csize = None
            if self.ocl:
                 kernel = getkernel(expr, args)
                 return self.compute_opencl(kernel, *vector)
            else:
                 return list(map(lmb, *vector))
        except Exception:
            self.csize = None
            traceback.print_exc()
            return -1

    def compute_opencl(self, kernel, *args):
        prg = cl.Program(self.ctx, kernel).build()
        mf = cl.mem_flags
        buffers = []
        for arg in args:
            buffers.append(cl.Buffer(self.ctx, mf.READ_ONLY, hostbuf=arg))
        buffers.append(cl.Buffer(self.ctx, mf.WRITE_ONLY, args[0].nbytes))
        prg.run(self.queue, args[0].size(), None, *buffers)
        result = np.empty_like(args[0])
        cl.enqueue_copy(self.queue, result, buffers[-1])
        return result


def opencsv(fl):
    fl = open(fl, "r")
    data = []
    headers = []
    for hd in fl.readline().split(","):
        headers.append(hd.strip())
    for line in fl:
        for i in line.split(","):
            data.append(i.strip())
    fl.close()
    return data, headers

def getlambda(code, args):
    blacklist = ['eval', 'exec','import']
    lmb = "lambda "
    for word in blacklist:
        code = code.replace(word, "")
    for i in args:
        lmb += i+","
    lmb = lmb.rstrip(",") + ": "
    lmb += code
    return eval(lmb)

def getkernel(code, args):
    kernel = "__kernel void run(float *" + ', float *'.join(args) + ", float *result){"
    kernel += chr(10) + "int tid = get_global_id(0);"
    for a in args:
        code = re.sub(a, a + "[tid]", code)
    kernel += chr(10) + "result[tid] = " + code + ";"
    kernel += chr(10) + "}"
    return kernel
    

