# Note that if we give an internal name, we are in our dict and modifying the external name won't affect us anymore 
from _tgt1 import BAR as bAR
print(bAR)
import _tgt1_mod
print(bAR)
#out: 0
#out: 0
