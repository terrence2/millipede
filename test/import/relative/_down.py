from .relative import foo as pkg
pkg()
from .relative._foo import foo as tgt
tgt()
