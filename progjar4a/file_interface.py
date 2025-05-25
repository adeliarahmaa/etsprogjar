import os
import json
import base64
import threading
from glob import glob


class FileInterface:
    def __init__(self):
        os.chdir('files/')
        self.lock = threading.Lock()

    def list(self,params=[]):
        try:
            filelist = glob('*.*')
            return dict(status='OK',data=filelist)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def get(self,params=[]):
        try:
            filename = params[0]
            if (filename == ''):
                return None
            fp = open(f"{filename}",'rb')
            isifile = base64.b64encode(fp.read()).decode()
            fp.close()
            return dict(status='OK',data_namafile=filename,data_file=isifile)
        except Exception as e:
            return dict(status='ERROR',data=str(e))

    def upload(self,params=[]):
        try:
            filename = params[0]
            filedata = params[1]
            if (filename == ''):
                return None
            with self.lock:
                fp = open(f"{filename}",'wb')
                fp.write(base64.b64decode(filedata))
                fp.close()
            return dict(status='OK')
        except Exception as e:
            return dict(status='ERROR',data=str(e))



if __name__=='__main__':
    f = FileInterface()
    print(f.list())
    print(f.get(['pokijan.jpg']))