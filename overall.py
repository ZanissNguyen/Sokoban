from solver import *

if __name__ == "__main__":
    
    for tc in range(1,40+1):
        # print(tc)
        for method in ['BrFS', 'A_star']:
            solver(tc, method)