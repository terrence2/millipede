try:
	1 // 0
except AttributeError:
	print(1)
except AssertionError:
	print(2)
except KeyError:
	print(3)
except:
	print('all')

#out: all
