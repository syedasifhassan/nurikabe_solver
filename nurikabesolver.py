
import itertools
from collections import deque
import time


class Cell():
    def __init__(self,group,x,y):
        self._x = x
        self._y = y
        self._liberties = []
        self._connections = []
        self._group = group
        group.add_member(self)
    
    def __str__(self):
        return self._group.get_display_char(self)
    
    @property
    def x(self):
        return self._x
    @property
    def y(self):
        return self._y
    @property
    def coords(self):
        return [self._x,self._y]
    @property
    def liberties(self):
        return self._liberties
    @property
    def liberty_coords(self):
        return [each_cell.coords for each_cell in self._liberties]
    @property
    def group(self):
        return self._group
    @group.setter
    def group(self,new_group):
        if self._group is new_group: return
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
        self._group.set_changed()
    def add_connection(self,new_connection):
        self.del_liberty(new_connection)
        if new_connection not in self._connections: self._connections.append(new_connection)
    def mutually_connect_to(self,new_connection):
        print("    cell at",self.coords,"mutually connecting to cell at",new_connection.coords)
        self.add_connection(new_connection)
        new_connection.add_connection(self)
    def mutually_disconnect_from(self,lost_liberty):
        print("    cell at",self.coords,"mutually disconnecting from cell at",lost_liberty.coords)
        self.del_liberty(lost_liberty)
        lost_liberty.del_liberty(self)

    def become_nurikabe(self):
        print("becoming nurikabe cell at",self.coords)
        if type(self.group) is Nurikabe: return
        print("  searching through",len(self.liberties),"liberties",self.liberty_coords)
        for each_liberty in list(self.liberties):
            print("  cell at",self.coords,"has a liberty of type",type(each_liberty.group),"at",each_liberty.coords)
            if type(each_liberty.group) is Island:
                self.mutually_disconnect_from(each_liberty)
            if type(each_liberty.group) is Nurikabe:
                self.mutually_connect_to(each_liberty)
                if type(self.group) is Unassigned:
                    self.group=each_liberty.group
                else:
                    self.group.merge_with(each_liberty.group)
                each_liberty.group.prevent_pool(self,each_liberty)
                self.group.prevent_pool(each_liberty,self)
        if type(self.group) is Unassigned:
            self.group.board.create_new_nurikabe(self)
                
    def become_island(self, count=None):
        print("becoming island cell at",self.coords)
        if type(self.group) is Island: return
        print("  searching through",len(self.liberties),"liberties",self.liberty_coords)
        for each_liberty in list(self.liberties):
            print("  cell at",self.coords,"has a liberty of type",type(each_liberty.group),"at",each_liberty.coords)
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
        self._liberties = []
        if starting_cell is not None:
            starting_cell.group = self
#         self.set_changed()

    def __str__(self):
        return str(type(self)) + str([each_cell.coords for each_cell in self._members])
    def get_display_char(self,requesting_cell):
        return ' '

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
#         self.update_liberties()
        
    def add_member(self,new_cell):
        self._members.append(new_cell)
        self.set_changed()
    def del_member(self,lost_member):
        self._members.remove(lost_member)
        self.set_changed()
    
    @property
    def liberties(self):
        return self._liberties
    @property
    def liberty_coords(self):
        return [each_cell.coords for each_cell in self._liberties]
    
    def update_liberties(self):
        print("  updating liberties for group",str(self))
        self._liberties = []
        for cell in self._members:
            for liberty in cell.liberties:
                if liberty not in self._liberties:
                    self._liberties.append(liberty)
    
    def merge_with(self,other_group):
        print("      merging",str(self),"with",str(other_group))
        L = len(self._members)
        while self._members:
            L-= 1
            self._members[L].group = other_group
#             self._members[0].group = other_group
        self.board.del_group(self)
        
    def update(self):
        pass

class Island(CellGroup):
    def __init__(self,board,starting_cell,count=None):
        super().__init__(board,starting_cell)
        self._starting_cell = starting_cell
        self._count=count

    def get_display_char(self, requesting_cell):
        if (self._starting_cell is requesting_cell) and self.count is not None:
            return str(self.count)
        return 'O'
    
    @property
    def starting_cell(self):
        return self._starting_cell
    @property
    def count(self):
        return self._count

    def merge_with(self,other_group):
        # Note: assuming we're not trying to merge two groups both having a count.
        if self.count is not None:
            other_group.merge_with(self)
        else:
            super().merge_with(self,other_group)
    
    def is_complete(self):
        if len(self._members)==self._count: return True
        return False
    def close_completed(self):
        if self.is_complete():
            print("  island",str(self),'complete!')
            for each_liberty in self.liberties:
                self.board.queue_nurikabe_cell(each_liberty)
            self.board.island_closed(self)
            return True
        return False
    
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
        print("updating group",str(self))
        self._changed=False
        if self.close_completed(): return
        liberties = self.liberties
        print("  island",str(self),"has",len(liberties),"liberties",self.liberty_coords)
        if len(liberties)==1:
            print("    island",str(self),"has only one liberty",liberties[0].coords)
            self.board.queue_island_cell(liberties[0])
        # check for a fork with a common neighbor
#         if len(liberties)==2:
#             if self.missing_cell_count()==1:
#                 for each_liberty in liberties[0].liberties:
#                     if each_liberty in liberties[1].liberties:
#                         each_liberty.become_nurikabe()
        # check for another island too close
        if self.count is not None:
            for each_liberty in liberties:
                for next_liberty in each_liberty.liberties:
                    if next_liberty.group is not self and type(next_liberty.group) is Island and next_liberty.group.count is not None:
                        print("    ",str(self),"and",str(next_liberty.group),"share liberty",each_liberty.coords)
                        self.board.queue_nurikabe_cell(each_liberty)
    
class Nurikabe(CellGroup):        
    def get_display_char(self, requesting_cell):
        return 'X'
    
    def prevent_pool(self,new_cell,joining_cell):
        for connected_cell in joining_cell.connections:
            if connected_cell is new_cell: continue
            for overlapping_liberty in connected_cell.liberties:
                if overlapping_liberty in new_cell.liberties:
                    print("      preventing pool in",str(self))
                    self.board.queue_island_cell(overlapping_liberty)

    def update(self):
        print("updating group",str(self))
        self._changed=False
        liberties = self.liberties
        print("  nurikabe",str(self),"has",len(liberties),"liberties",self.liberty_coords)
        if self.board.count_nurikabe() > 1:
            if len(liberties)==1:
                print("  nurikabe at",self._members[0].coords,"has only one liberty",liberties[0].coords)
                self.board.queue_nurikabe_cell(liberties[0])

class Unassigned(CellGroup):
    def get_display_char(self, requesting_cell):
        return '-'
    def set_changed(self):
        pass
    def del_member(self,lost_member):
        self._members.remove(lost_member)
        # don't need to update liberties


class Board():
    def __init__(self,board_str_lines):
        self._Y = len(board_str_lines)
        self._X = len(board_str_lines[0]) #Assumed here that every line has the same number of chars
        self._islands = []
        self._orphan_islands = []
        self._complete_islands = []
        self._nurikabe = []
        self._unassigned = [Unassigned(self)]
        self._island_cell_queue = deque()
        self._nurikabe_cell_queue = deque()
        print("initializing board")
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
        print("  initial island liberty update")
        self.update_group_liberties()

    def __str__(self):
        board_rows = [[' ' for i in range(0,10 + 3*self._X)] for j in range(0,self._Y)]
        for each_group in itertools.chain(self._islands,self._complete_islands,self._orphan_islands,self._nurikabe,self._unassigned):
            for each_cell in each_group.members:
                board_rows[each_cell.y][each_cell.x] = str(each_cell)
                board_rows[each_cell.y][each_cell.x + self._X + 5]= str(len(each_cell.liberties))
                board_rows[each_cell.y][each_cell.x + 2*self._X + 10]= str(len(each_cell.group.liberties))
        board_lines = []
        for each_row in board_rows:
            board_lines.append(' '.join(each_row))
        return '\n'+'\n'.join(board_lines)

    def count_nurikabe(self):
        return len(self._nurikabe)

    def create_new_nurikabe(self, starting_cell):
        print("  creating new nurikabe group at",starting_cell.coords)
        new_nurikabe = Nurikabe(self, starting_cell)
        self._nurikabe.append(new_nurikabe)
        # if there was only one nurakabe, it had no reason to grow so it would have ignored an update.  so tell it to wake up.
        if len(self._nurikabe)==2:
            self._nurikabe[0].update()

    def create_new_island(self, starting_cell, count=None):
        print("  creating new island group at",starting_cell.coords)
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

    def queue_nurikabe_cell(self,queue_cell):
        if queue_cell not in self._nurikabe_cell_queue:
            print("      queuing nurikabe cell",queue_cell.coords)
            self._nurikabe_cell_queue.append(queue_cell)

    def queue_island_cell(self,queue_cell):
        if queue_cell not in self._island_cell_queue:
            print("      queuing island cell",queue_cell.coords)
            self._island_cell_queue.append(queue_cell)

    def island_closed(self,closed_island):
        self._islands.remove(closed_island)
        self._complete_islands.append(closed_island)

    def is_solved(self):
        if self.count_nurikabe()>1:
            return False
        if self._islands or self._orphan_islands:
            return False
        if self._unassigned[0].members:
            return False
        return True

    def quick_reach_check(self):
        pass
            
    def solve(self):
        start_time = time.clock()
        self.update()
        self.clear_cell_queue()
        self.quick_mark_cant_reach()
        print(self)
        if self.is_solved():
            print("solved!  :)")
        else:
            print("not solved!  :(")
        elapsed_time = time.clock()-start_time
        print ("elapsed time: {:.3f} ms.".format(elapsed_time*1000))
        

    def quick_mark_cant_reach(self):
        print("checking quick can't reach")
        for each_cell in self._unassigned[0].members:
            can_be_reached = False
            for each_island in self._islands:
                if each_island.quick_can_reach(each_cell):
                    can_be_reached = True
            if not can_be_reached:
                self.queue_nurikabe_cell(each_cell)
        self.clear_cell_queue()
    
    def clear_cell_queue(self):
        print()
        print("clearing island cell queue",[each_cell.coords for each_cell in self._island_cell_queue])
        print("clearing nurikabe cell queue",[each_cell.coords for each_cell in self._nurikabe_cell_queue])
        while self._island_cell_queue or self._nurikabe_cell_queue:
            while self._nurikabe_cell_queue:
                print()
                print("popping nurikabe cell",self._nurikabe_cell_queue[0].coords,"from queue",[each_cell.coords for each_cell in self._nurikabe_cell_queue])
                self._nurikabe_cell_queue.popleft().become_nurikabe()
                print(self)
                self.update()
            while self._island_cell_queue:
                print()
                print("popping island cell",self._island_cell_queue[0].coords,"from queue",[each_cell.coords for each_cell in self._island_cell_queue])
                self._island_cell_queue.popleft().become_island()
                print(self)
                self.update()

    def update_group_liberties(self):
        for each_group in itertools.chain(self._islands,self._nurikabe,self._orphan_islands):
            if each_group.changed:
                each_group.update_liberties()
        
    def update(self):
        print()
        print("updating board")
        changed=True
        while changed:
            changed=False
            self.update_group_liberties()
            for each_group in itertools.chain(self._islands,self._nurikabe,self._orphan_islands):
                if each_group.changed:
                    changed=True
                    each_group.update()


def main():
    board_str = '''\
3--
---
3--\
'''
    board_str2 = '''\
2--
---
3--\
'''
    board_str3 = '''\
6-7---1
-------
-------
-------
1------
--3--1-
1------\
'''
    board_str4 = '''\
2-3-3--
-------
------3
3--3---
--2----
----2--
-------\
'''
    board_str5 = '''\
2--1-3---1-4-2--1-2-
--------------------
2-2-1-1-3-----3-1---
-------3---------2-2
-2--3-----1-2-------
---3-----1----4---2-
-----2----2--1------
4------2-2----2-----
----1------3----2-1-
--2--1--2-2--------2
1---3-1------2-3-4--
-----------1--------
4-----1-1-1---------
-----7-1---1-1--1---
3--3----2-1-2-1--5--
---------------2----
---------2-2-2------
2---1-----------3---
--1-----------1----1
1---1-2--2--1-------\
'''
    this_board = Board(board_str_lines=board_str4.split('\n'))
    print(this_board)
    this_board.solve()

    
if __name__ == "__main__": main()