a = [4]

a[0] |= 12
print(a[0])
a[0] |= 2
print(a[0])
#out: 12
#out: 14

a[0] ^= 10
print(a[0])
#out: 4

a[0] &= 6
print(a[0])
a[0] &= 2
print(a[0])
#out: 4
#out: 0

a[0] += 42
print(a[0])
#out: 42

a[0] -= 43
print(a[0])
#out: -1

a[0] *= 25
print(a[0])
#out: -25

a[0] /= 5
print(a[0])
#out: -5.0

a[0] //= 2
print(a[0])
#out: -3.0

a[0] = -5
a[0] //= 2
print(a[0])
#out: -3

a[0] **= 3
print(a[0])
#out: -27

a[0] *= -1
a[0] %= 7
print(a[0])
#out: 6

a[0] = -27
a[0] %= 7
print(a[0])
#out: 1
