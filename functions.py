import pandas
import numpy as np
import traceback
import re

class OpenCL():
    def __init__(self):
        try:
            import pyopencl as cl
            self.ctx = cl.create_some_context()
            self.cl = cl
            self.success = True
        except ImportError:
            self.success = False
        if self.success:
            self.queue = cl.CommandQueue(self.ctx)
    
    def getkernel(self, args, code):
        kernel = "__kernel void run(__constant float *" + ', __constant float *'.join(args) + ", __global float *result){"
        kernel += chr(10) + "int tid = get_global_id(0);"
        for a in args:
            code = re.sub(a, a + "[tid]", code)
        kernel += chr(10) + "result[tid] = " + code + ";"
        kernel += chr(10) + "}"
        self.kernel = kernel
        
    def compute(self, *args):
        prg = self.cl.Program(self.ctx, self.kernel).build()
        mf = self.cl.mem_flags
        buffers = []
        for arg in args:
            buffers.append(self.cl.Buffer(self.ctx, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=arg))
        buffers.append(self.cl.Buffer(self.ctx, mf.WRITE_ONLY, args[0].nbytes))
        prg.run(self.queue, args[0].shape, None, *buffers)
        result = np.empty_like(args[0])
        self.cl.enqueue_copy(self.queue, result, buffers[-1])
        return result
    
def getlambda(args, code):
    blacklist = ['eval', 'exec','import']
    lmb = "lambda "
    for word in blacklist:
        code = code.replace(word, "")
    for i in args:
        lmb += i+","
    lmb = lmb.rstrip(",") + ": "
    lmb += code
    return eval(lmb)
