import os
import glob
import time

limit = time.time() - 60*60
for f in glob.glob('./res/*'):

     if os.stat(f).st_mtime < limit:
         os.remove(f)


