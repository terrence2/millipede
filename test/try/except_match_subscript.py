A = [SystemError, ZeroDivisionError, AssertionError]

try:
	raise ZeroDivisionError
except A[1]:
	print("catch")
#out: catch
