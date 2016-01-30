
class Cell():
    def __init__(self,group,x,y):
        self._group = group
        self._x = x
        self._y = y

class CellGroup():
    pass

class Board():
    pass

def main():
    new_cell = Cell(1,2)
    print(new_cell)

if __name__ == "__main__": main()