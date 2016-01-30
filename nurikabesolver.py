
import itertools

class Cell():
    def __init__(self,group,x,y):
        self._group = group
        group.add_member(self)
        self._x = x
        self._y = y
        self._liberties = []
        self._connections = []
    
    def __str__(self):
        if (type(self._group) is Island) and (self._group.starting_cell is self):
            return str(self._group.count)
        return str(self._group)
    
    @property
    def x(self):
        return self._x
    @property
    def y(self):
        return self._y
    @property
    def liberties(self):
        return self._liberties
    @property
    def group(self):
        return self._group
    @group.setter
    def group(self,new_group):
        self._group.del_member(self)
        self._group = new_group
        new_group.add_member(self)
    @property
    def connections(self):
        return self._connections
    
    def has_liberty(self,liberty):
        if liberty in self._liberties: return True
    def add_liberty(self,new_liberty):
        if new_liberty not in self._liberties: self._liberties.append(new_liberty)
    def del_liberty(self,lost_liberty):
        self._liberties.remove(lost_liberty)
        self._group.set_changed
    def add_connection(self,new_connection):
        self.del_liberty(new_connection)
        if new_connection not in self._connections: self._connections.append(new_connection)
    def mutually_connect_to(self,new_connection):
        self.add_connection(new_connection)
        new_connection.add_connection(self)
    def mutually_disconnect_from(self,lost_liberty):
        self.del_liberty(lost_liberty)
        lost_liberty.del_liberty(self)

    def become_nurikabe(self):
        if type(self.group) is Nurikabe: return
        for each_liberty in self.liberties:
            if type(each_liberty.group) is Island:
                self.mutually_disconnect_from(each_liberty)
            if type(each_liberty.group) is Nurikabe:
                self.mutually_connect_to(each_liberty)
                if type(self.group) is Unassigned:
                    self.group=each_liberty.group
                else:
                    self.group.merge_with(each_liberty.group)
                each_liberty.group.prevent_pool(self,each_liberty)
        if type(self.group) is Unassigned:
            self.group.board.create_new_nurikabe(self)
                
    def become_island(self, count=None):
        if type(self.group) is Island: return
        for each_liberty in self.liberties:
            if type(each_liberty.group) is Nurikabe:
                self.mutually_disconnect_from(each_liberty)
            if type(each_liberty.group) is Island:
                self.mutually_connect_to(each_liberty)
                if type(self.group) is Unassigned:
                    self.group=each_liberty.group
                else:
                    self.group.merge_with(each_liberty.group)
        if type(self.group) is Unassigned:
            self.group.board.create_new_island(self)
        
class CellGroup():
    def __init__(self,board,starting_cell=None):
        self._board = board
        self._members = []
        if starting_cell is not None:
            starting_cell.group = self

    @property
    def board(self):
        return self._board
    @property
    def members(self):
        return self._members
    @property
    def changed(self):
        return self._changed
    def set_changed(self):
        # only self can turn the update flag off
        self._changed = True
        
    def add_member(self,new_cell):
        self._members.append(new_cell)
        self._changed = True
    def del_member(self,lost_member):
        self._members.remove(lost_member)
    
    @property
    def liberties(self):
        liberties = []
        for cell in self._members:
            for liberty in cell.liberties:
                if liberty not in liberties:
                    liberties.append(liberty)
        return liberties
    
    def merge_with(self,other_group):
        for each_member in self._members:
            each_member.group = other_group
        self.board.del_group(self)
        

    
class Island(CellGroup):
    def __init__(self,board,starting_cell,count=None):
        super().__init__(board,starting_cell)
        self._starting_cell = starting_cell
        self._count=count

    def __str__(self):
        return 'O'
    
    @property
    def starting_cell(self):
        return self._starting_cell
    @property
    def count(self):
        return self._count

    def merge_with(self,other_group):
        if self.count is not None:
            other_group.merge_with(self)
        else:
            super().merge_with(self,other_group)
    
    def is_complete(self):
        if len(self._members)==self._count: return True
        return False
    def close_completed(self):
        if self.is_complete():
#             print('complete!')
            for each_liberty in self.liberties:
                each_liberty.become_nurikabe()
    
    def missing_cell_count(self):
        return self._count - len(self._members)
    
    def quick_can_reach(self,test_cell):
        delta_x = self._starting_cell.x - test_cell.x
        delta_y = self._starting_cell.y - test_cell.y
        steps_to_reach = abs(delta_x) + abs(delta_y)
        # i.e. steps_to_reach + 1 <= self._count
        if steps_to_reach < self._count: return True
        return False
    
    def update(self):
        self._changed=False
        self.close_completed()
        liberties = self.liberties
        if len(liberties)==1:
            liberties[0].become_island()
        # check for a fork with a common neighbor
#         if len(liberties)==2:
#             if self.missing_cell_count()==1:
#                 for each_liberty in liberties[0].liberties:
#                     if each_liberty in liberties[1].liberties:
#                         each_liberty.become_nurikabe()
        # check for another island too close
        for each_liberty in liberties:
            for next_liberty in each_liberty.liberties:
                if type(next_liberty.group) is Island and next_liberty.group.count is not None:
                    each_liberty.become_nurikabe()
    
class Nurikabe(CellGroup):
    def __init__(self,board,starting_cell):
        super().__init__(board,starting_cell)
        self._pool_queue = []
        
    def __str__(self):
        return 'X'
    
    def prevent_pool(self,new_cell,joining_cell):
        for connected_cell in joining_cell.connections:
            if connected_cell is new_cell: continue 
            for overlapping_liberty in connected_cell.liberties:
                if overlapping_liberty in new_cell.liberties:
                    self._pool_queue.append(overlapping_liberty)
    def clear_pool_queue(self):
        for each_cell in self._pool_queue:
            each_cell.become_island()

    def update(self):
        self._changed=False
        self.clear_pool_queue()
        if self.board.count_nurikabe() > 1:
            liberties = self.liberties
            if len(liberties)==1:
                liberties[0].become_nurikabe()

class Unassigned(CellGroup):
    def __str__(self):
        return '-'

class Board():
    def __init__(self,board_str_lines):
        self._N = len(board_str_lines)
        self._islands = []
        self._orphan_islands = []
        self._nurikabe = []
        self._unassigned = [Unassigned(self)]
        board_rows = []
        y=0
        for line in board_str_lines:
#             print(line)
            board_row = []
            x=0
            for character in line:
                new_cell = Cell(self._unassigned[0],x,y)
                board_row.append(new_cell)
                if x>0:
                    previous_cell = board_row[x-1]
                    new_cell.add_liberty(previous_cell)
                    previous_cell.add_liberty(new_cell)
                if y>0:
                    above_cell = board_rows[y-1][x]
                    new_cell.add_liberty(above_cell)
                    above_cell.add_liberty(new_cell)
                if character.isdigit():
                    self.create_new_island(new_cell, count = int(character))
                x += 1
            board_rows.append(board_row)
            y += 1

    def __str__(self):
        board_rows = [[' ' for i in range(0,self._N)] for j in range(0,self._N)]
        for each_group in itertools.chain(self._islands,self._nurikabe,self._unassigned):
            for each_cell in each_group.members:
                board_rows[each_cell.y][each_cell.x] = str(each_cell)
        board_lines = []
        for each_row in board_rows:
            board_lines.append(' '.join(each_row))
        return '\n'.join(board_lines)+'\n'

    def count_nurikabe(self):
        return len(self._nurikabe)

    def create_new_nurikabe(self, starting_cell):
        new_nurikabe = Nurikabe(self, starting_cell)
        self._nurikabe.append(new_nurikabe)

    def create_new_island(self, starting_cell, count=None):
        new_island = Island(self, starting_cell,count)
        if count is None:
            self._orphan_islands.append(new_island)
        else:
            self._islands.append(new_island)
        
    def del_group(self,empty_group):
        if type(empty_group) is Island:
            self._orphan_islands.remove(empty_group)
        if type(empty_group) is Nurikabe:
            self._nurikabe.remove(empty_group)
            
    def solve(self):
        # insert: quick reach check
        changed=True
        while changed:
            changed=False
            for each_group in itertools.chain(self._islands,self._nurikabe):
                if each_group.changed:
                    changed=True
                    each_group.update()

def main():
    board_str = '''\
1--
---
1-3\
'''
    this_board = Board(board_str_lines=board_str.split('\n'))
    print(this_board)
    this_board.solve()
    print(this_board)

    

if __name__ == "__main__": main()