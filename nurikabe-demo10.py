
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
    def add_member(self,new_cell):
        self._members.append(new_cell)

class Island(CellGroup):
    pass

class Nurikabe(CellGroup):
    pass

class Unassigned(CellGroup):
    pass

class Board():
    def __init__(self):
        self._islands = []
        self._nurikabe = []
        self._unassigned = [Unassigned(self)]
        new_cell = Cell(self._unassigned[0],0,0)

def main():
    new_board = Board()
    print(new_board)
    print(new_board._unassigned[0])
    print(new_board._unassigned[0]._members[0])
    print(new_board._unassigned[0]._members[0]._x,new_board._unassigned[0]._members[0]._y)

if __name__ == "__main__": main()