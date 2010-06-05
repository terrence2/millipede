'''
The block/basic syntax tree (BST).

This simpler (almost trivial) syntax tree contains only the scope-containing
block level syntax elements (module, class, function/method).  It also 
aggregates all definitions of those elements at the top level.  These flat
lists are incredibly useful for implementing many function related linters.
'''
