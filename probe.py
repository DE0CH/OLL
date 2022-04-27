from multiprocessing import Pool

def f(x, y):
    return x*y

if __name__ == '__main__':
    with Pool(5) as p:
        print(p.starmap(f, zip([1, 2, 3], [1, 2, 4])))