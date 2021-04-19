import os
source = 'https://pypi.douban.com/simple'
modules = ['PyCryptodome==3.9.9', 'Elite', 'PyQt5', 'msgpack', 'structsock']

for m in modules:
    os.system('pip install {} -i {}'.format(m, source))