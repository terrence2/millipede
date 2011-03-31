from .. import foo as pkg
pkg()
from .._foo import foo as tgt
tgt()
