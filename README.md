# Group-2
import hashlib
 
hasher = hashlib.md5()
with open('myfile.jpg', 'rb') as afile:
    buf = afile.read()
    hasher.update(buf)
print(hasher.hexdigest())
