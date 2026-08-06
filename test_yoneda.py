import subprocess, sys, re, os

YONEDA = "./yoneda"
MD = 10
LEN = 6

def run(args, **kw):
    # run the yoneda program and capture its output
    result = subprocess.run([YONEDA]+[str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **kw)
    return result.stdout, result.stderr, result.returncode


# test functions go here

if __name__ == "__main__":
    if not os.path.isfile(YONEDA):
        sys.exit(f"Error: {YONEDA} not found. Please build it first with `make yoneda`.")

    #list of test functions to run    
    test = [

    ]
    
    failures =[]
    for t in test:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failures.append((t.__name__, str(e)))  
        except Exception as e:
            print(f"ERROR: {t.__name__}: {e}")
            failures.append((t.__name__, str(e))) 

    print(f"\n{len(test)-len(failures)}/{len(test)} tests.")    
    sys.exit(1 if failures else 0)  



