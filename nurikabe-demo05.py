
class Cell():
    def __init__(self,group,x,y):
        self._group = group
        group.add_member(self)
        self._x = x
        self._y = y

class CellGroup():
    def __init__(self,board):
        self._board = board
        self._members = []

class Board():
    def __init__(self):
        self._islands = []
        self._nurikabe = []
        self._unassigned = []

def main():
    pass

if __name__ == "__main__": main()