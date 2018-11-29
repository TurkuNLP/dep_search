from distutils.core import setup
from Cython.Build import cythonize

setup(name='py_tree',
      ext_modules=cythonize("py_tree.pyx"))

setup(name='DB',
      ext_modules=cythonize("DB.pyx"))

setup(name='Blobldb',
      ext_modules=cythonize("Blobldb.pyx"))

try:

    setup(name='kc_Blobldb',
          ext_modules=cythonize("kc_Blobldb.pyx"))
except:
       
    pass

try:

    setup(name='lmdb_Blobldb',
          ext_modules=cythonize("lmdb_Blobldb.pyx"))
except:
    pass