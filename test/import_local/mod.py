# 1) import and print BAR, import _tgt1_mod to modify bar, print BAR again and ensure it changed
import _tgt1
print(_tgt1.BAR)
import _tgt1_mod
print(_tgt1.BAR)
#out: 0
#out: 42
