from multiprocessing import Pool
import time

def f(x,y):
    return x*y

if __name__ == '__main__':
    with Pool() as p:
        print(p.map(f, range(10),range(11,21)))
        

st=time.time()
#!python test.py
print (time.time()-st)

#st=time.time()
#list(map(f,range(10),range(11,21)))
#print (time.time()-st)