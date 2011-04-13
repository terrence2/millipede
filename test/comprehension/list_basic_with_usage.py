package_directory = '/a/b//c/d//e/f'
package_parts = [p for p in package_directory.split('/') if p]
print(package_parts)
#out: ['a', 'b', 'c', 'd', 'e', 'f']
