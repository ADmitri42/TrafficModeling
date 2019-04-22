from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize

extensions = [
    Extension("utilities", ["utilities.pyx"]),
    # Everything but primes.pyx is included here.
    Extension("cars", ["cars.pyx"]),
]

setup(
    ext_modules = (cythonize(extensions, annotate=True))
)
