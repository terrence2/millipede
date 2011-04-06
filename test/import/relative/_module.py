from . import _foo
# importing from package... the _foo in __init__.py will win over the module
print(type(_foo)) # function
