
import itertools
from collections import deque
import time


class Cell():
    def __init__(self,group,x,y):
        self._x = x
        self._y = y
        self._liberties = set([])
        self._connections = set([])
        self._possible_pools = set([])
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
        if self._group is not None:
            self._group.del_member(self)
        self._group = new_group
        new_group.add_member(self)
    @property
    def connections(self):
        return self._connections
    @property
    def possible_pools(self):
        return self._possible_pools
    def add_possible_pool(self,new_possible_pool):
        self._possible_pools.add(new_possible_pool)
    def remove_possible_pool(self,possible_pool):
        self._possible_pools.discard(possible_pool)
    def delete_all_possible_pools(self):
        while self._possible_pools:
            each_pool = self._possible_pools.pop()
            each_pool.delete()
    def check_possible_pools(self):
        for each_pool in self._possible_pools:
            each_pool.check_for_forced_island()
    @staticmethod
    def get_all_possible_pools_from_cells(cells):
        all_possible_pools = set([])
        for each_cell in cells:
            all_possible_pools.update(each_cell.possible_pools)
        return all_possible_pools
    
    def has_liberty(self,liberty):
        if liberty in self._liberties: return True
    def add_liberty(self,new_liberty):
        if new_liberty not in self._liberties: self._liberties.add(new_liberty)
    def del_liberty(self,lost_liberty):
        self._liberties.remove(lost_liberty)
        self._group.set_changed()
    def add_connection(self,new_connection):
        self.del_liberty(new_connection)
        if new_connection not in self._connections: self._connections.add(new_connection)
    def mutually_connect_to(self,new_connection):
#         print("    cell at",self.coords,"mutually connecting to cell at",new_connection.coords)
        self.add_connection(new_connection)
        new_connection.add_connection(self)
    def mutually_disconnect_from(self,lost_liberty):
#         print("    cell at",self.coords,"mutually disconnecting from cell at",lost_liberty.coords)
        self.del_liberty(lost_liberty)
        lost_liberty.del_liberty(self)

    def become_nurikabe(self):
#         print("becoming nurikabe cell at",self.coords)
        if type(self.group) is Nurikabe: return
#         print("  searching through",len(self.liberties),"liberties",self.liberty_coords)
        for each_liberty in list(self.liberties):
#             print("  cell at",self.coords,"has a liberty of type",type(each_liberty.group),"at",each_liberty.coords)
            if type(each_liberty.group) is Island or type(each_liberty.group) is OrphanIsland:
                self.mutually_disconnect_from(each_liberty)
            if type(each_liberty.group) is Nurikabe:
                self.mutually_connect_to(each_liberty)
                if type(self.group) is Unassigned:
                    self.group=each_liberty.group
                else:
                    if each_liberty.group is not self.group:
                        self.group.merge_with(each_liberty.group)
#                 each_liberty.group.prevent_pool(self,each_liberty)
#                 self.group.prevent_pool(each_liberty,self)
        if type(self.group) is Unassigned:
            self.group.board.create_new_nurikabe(self)
        self.check_possible_pools()
                
    def become_island(self, count=None):
#         print("becoming island cell at",self.coords)
        if type(self.group) is Island: return
#         print("  searching through",len(self.liberties),"liberties",self.liberty_coords)
        self.delete_all_possible_pools()
        # to avoid problems keeping track of required orphans, join any adjacent islands first
        for each_liberty in list(self.liberties):
#             print("  cell at",self.coords,"has a liberty of type",type(each_liberty.group),"at",each_liberty.coords)
            if type(each_liberty.group) is Island:
                self.mutually_connect_to(each_liberty)
                if self.group == each_liberty.group: continue
                if type(self.group) is Unassigned:
                    self.group=each_liberty.group
                else:
                    self.group.merge_with(each_liberty.group)
        for each_liberty in list(self.liberties):
#             print("  cell at",self.coords,"has a liberty of type",type(each_liberty.group),"at",each_liberty.coords)
            if type(each_liberty.group) is Nurikabe:
                self.mutually_disconnect_from(each_liberty)
            if type(each_liberty.group) is OrphanIsland:
                self.mutually_connect_to(each_liberty)
                if self.group == each_liberty.group: continue
                if type(self.group) is Unassigned:
                    self.group=each_liberty.group
                else:
                    self.group.merge_with(each_liberty.group)
        if type(self.group) is Unassigned:
            self.group.board.create_new_orphan_island(self)
        
class CellGroup():
    def __init__(self,board):
        self._board = board
        self._members = set([])
        self._liberties = set([])

    def __str__(self):
        return str(type(self)) + str([each_cell.coords for each_cell in self._members])
    @staticmethod
    def count_to_character(count):
        if count<10:
            return str(count)
        return chr(count - 10 + ord('a'))
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
        self._members.add(new_cell)
        self.set_changed()
    
    @property
    def liberties(self):
        return self._liberties
    @property
    def liberty_coords(self):
        return [each_cell.coords for each_cell in self._liberties]
    
    def update_liberties(self):
#         print("  updating liberties for group",str(self))
        self._liberties.clear()
        for cell in self._members:
            self._liberties.update(cell.liberties)
    
class ExclusiveGroup(CellGroup):
    def __init__(self,board):
        super().__init__(board)
        self._paths = None
    @property
    def paths(self):
        return self._paths
    def get_display_char(self,requesting_cell):
        return ' '
    def add_member(self,new_cell):
        super().add_member(new_cell)
        self._paths=None
    def del_member(self,lost_member):
        self._members.discard(lost_member)
        if self._members:
            self.set_changed()
        else:
            self._paths=None #should only delete members when merging, so no need to remove paths until group is empty
            self.board.del_group(self)

    def merge_with(self,other_group):
#         print("      merging",str(self),"with",str(other_group))
        while self._members:
            self._members.pop().group = other_group
        
    def update(self):
        pass
    
    def extend_paths_to(self,length):
#         print()
#         print("extending/building paths for",self)
        if not self.liberties:
            self._paths = None
            return
        if self._paths is None:
            self._paths = deque([])
            self.add_path(set([]))
        else:
            for each_path in self._paths:
                each_path.update_liberties()
        first_path = None
        while first_path is None or self._paths[0] is not first_path:
            if not self.paths:
                print("Error! no paths left to extend in",self)
            if first_path is None:
                first_path = self._paths[0]
            next_path = self._paths.popleft()
            if not next_path.terminated and len(next_path.members)<length:
                next_path.extend()
            else:
                self._paths.append(next_path)
            if first_path not in self._paths:
                first_path = None
                
    def path_is_duplicate(self,members):
        for each_path in self._paths:
#             print("      checking new path",[each_cell.coords for each_cell in members],"for duplication of existing path",each_path)
            if each_path.members == members:
#                 print("duplicate path")
                return True
        return False

    def add_path(self,members):
        if not self.path_is_duplicate(members):
            self._paths.append(self.make_new_path(members))
#             print(self._paths)
    def add_path_left(self,members,absorbed_orphans=None):
        if not self.path_is_duplicate(members):
            if absorbed_orphans is None:
                self._paths.appendleft(self.make_new_path(members))
            else:
                self._paths.appendleft(self.make_new_path(members,absorbed_orphans))
#             print(self._paths)
    def make_new_path(self,members,absorbed_orphans = None):
        return None
    
    def remove_path(self,path):
        self._paths.remove(path)
        
    def all_paths_terminated(self):
        if self._paths is None: return False
        for each_path in self._paths:
            if not each_path.terminated:
                return False
        return True
    
    def invalidate_paths(self,changing_cell):
        if self._paths is None: return False
        for each_path in self._paths:
            if changing_cell in each_path.members.union(each_path.liberties):
                self._paths = None
                return True
        return False
    def all_paths_are_blocked_by_path(self,other_path):
        if self._paths is None: return False
        cells_blocked = other_path.members
        for each_path in self._paths:
            if not each_path.members.intersection(cells_blocked):
                return False
        return True 
        

class Island(ExclusiveGroup):
    def __init__(self,board,count):
        super().__init__(board)
        self._count=count
        self._starting_cell = None
        self._required_absorbed_orphans = set([])

    def get_display_char(self, requesting_cell):
        if (self.starting_cell is requesting_cell):
            return CellGroup.count_to_character(self.count)
        return 'O'

    @staticmethod
    def character_to_count(character):
        if character.isdigit():
            return int(character)
        else:
            if character.isalpha():
                return ord(character)-ord('a')+10
        return False

    @property
    def starting_cell(self):
        return self._starting_cell
    @property
    def count(self):
        return self._count
    @property
    def required_absorbed_orphans(self):
        return self._required_absorbed_orphans
    def add_required_absorbed_orphan(self,new_orphan):
        if new_orphan not in self._required_absorbed_orphans:
#             print("  adding new required orphan",new_orphan,"to",self)
            self._required_absorbed_orphans.add(new_orphan)
            if self._paths is not None:
                P = len(self._paths)
                while P:
                    P-=1
                    each_path = self._paths[P]
#                     print("    checking path",each_path)
                    if new_orphan not in each_path.absorbed_orphans:
                        if each_path.terminated or each_path.get_path_length()+len(new_orphan.members)+1>self.missing_cell_count():
#                             print("      nope, removing it")
                            self._paths.remove(each_path)
    def replace_required_orphans(self,old_orphan,new_orphan):
        if old_orphan in self.required_absorbed_orphans:
            self._required_absorbed_orphans.remove(old_orphan)
            self._required_absorbed_orphans.add(new_orphan)
            # this occurrence is so rare, just invalidate the paths so they will be recalculated
            self._paths = None

    def add_member(self,new_cell):
        if not self._members:
            self._starting_cell = new_cell
        super().add_member(new_cell)

    def merge_with(self,other_group):
        if type(other_group) is OrphanIsland:
            if other_group in self._required_absorbed_orphans:
                self._required_absorbed_orphans.remove(other_group)
            other_group.merge_with(self)
        else:
            print("Error! tried to merge island",self,"with non-orphan island",other_group)
    
    def is_complete(self):
        if len(self._members)==self._count: return True
        return False
    def close_completed(self):
        if self.is_complete():
            print("  island",str(self),'complete!')
            for each_liberty in self.liberties:
                self.board.queue_nurikabe_cell(each_liberty)
            self.board.island_closed(self)
            self._liberties.clear()
            return True
        return False
    
    def missing_cell_count(self):
        return self._count - len(self._members)
    
    def update(self):
        print("updating group",str(self))
        self._changed=False
        if self.close_completed(): return
        liberties = self.liberties
#         print("  island",str(self),"has",len(liberties),"liberties",self.liberty_coords)
        # Note: path overlap logic will do a more sophisticated version of these three checks, so they can be removed (but this is faster)
        if len(liberties)==1:
            for each_liberty in liberties:
#                 print("    island",str(self),"has only one liberty",each_liberty.coords)
                self.board.queue_island_cell(each_liberty)
        # check for a fork with a common neighbor
        if len(liberties)==2:
            if self.missing_cell_count()==1:
                overlap = None
                for each_liberty in liberties:
                    if overlap is None:
                        overlap = each_liberty.liberties
                    else:
                        overlap = overlap & each_liberty.liberties
                if overlap:
                    for each_liberty in overlap:
#                         print("    found fork at",each_liberty.coords,"in",str(self))
                        self.board.queue_nurikabe_cell(each_liberty)
        # check for another island too close
        for each_liberty in liberties:
            for next_liberty in each_liberty.liberties:
                if next_liberty.group is not self and type(next_liberty.group) is Island:
#                     print("    ",str(self),"and",str(next_liberty.group),"share liberty",each_liberty.coords)
                    self.board.queue_nurikabe_cell(each_liberty)
    
    def make_new_path(self,members,absorbed_orphans=None):
        return IslandPath(self.board,self,members,absorbed_orphans)
    def path_overlaps(self):
        common = Path.common_to_all_paths(self.paths)
        for each_cell in common:
            # problem: this forgets that the new island cell must connect to this island - need to remember that and tell the new orphan island (if any)
            self.board.queue_island_cell(each_cell)
        common = Path.common_neighbor_to_all_paths(self.paths)
        for each_cell in common:
            self.board.queue_nurikabe_cell(each_cell)
    def remove_paths_blocking_nurikabe_liberties(self,each_nurikabe):
        if self._paths is None: return False
        removed_something = False
        P = len(self._paths)
        while P:
            P-=1
            each_path = self._paths[P]
            if not each_nurikabe.liberties - each_path.members:
#                 print("  removing",each_path,"from",self)
                removed_something = True
                self._paths.remove(each_path)
#         if removed_something:
#             self.path_overlaps()
        return removed_something
    def remove_paths_excluding_other_island_paths(self,other_island):
        if self._paths is None: return False
        removed_something = False
        P = len(self._paths)
        while P:
            P-=1
            each_path = self._paths[P]
            if other_island.all_paths_are_blocked_by_other_island_path(each_path):
#                 print("  removing",each_path,"from",self)
                removed_something = True
                self._paths.remove(each_path)
        return removed_something
    def remove_paths_excluding_nurikabe_paths(self,other_nurikabe):
        if self._paths is None: return False
        removed_something = False
        P = len(self._paths)
        while P:
            P-=1
            each_path = self._paths[P]
            if other_nurikabe.all_paths_are_blocked_by_path(each_path):
#                 print("  removing",each_path,"from",self)
                removed_something = True
                self._paths.remove(each_path)
        return removed_something
    def all_paths_are_blocked_by_other_island_path(self,other_path):
        if self._paths is None: return False
        cells_blocked = other_path.cells_blocked
        for each_path in self._paths:
            if not each_path.members.intersection(cells_blocked):
                return False
        return True 
    def remove_paths_containing_blocked_cells(self,blocked_cells):
        if self._paths is None: return False
        removed_something = False
        P = len(self._paths)
        while P:
            P-=1
            each_path = self._paths[P]
            if each_path.members.intersection(blocked_cells):
#                 print("  removing",each_path,"from",self)
                removed_something = True
                self._paths.remove(each_path)
        return removed_something
    @property
    def cells_blocked(self):
        return Path.common_cells_blocked_by_all_paths(self.paths)
    
class Nurikabe(ExclusiveGroup):        
    def get_display_char(self, requesting_cell):
        return 'X'
    
#     def prevent_pool(self,new_cell,joining_cell):
#         for connected_cell in joining_cell.connections:
#             if connected_cell is new_cell: continue
#             for overlapping_liberty in connected_cell.liberties:
#                 if overlapping_liberty in new_cell.liberties:
#                     print("      preventing pool at",overlapping_liberty.coords,"in",str(self))
#                     self.board.queue_island_cell(overlapping_liberty)

    def update(self):
        print("updating group",str(self))
        self._changed=False
        liberties = self.liberties
#         print("  nurikabe",str(self),"has",len(liberties),"liberties",self.liberty_coords)
        if self.board.count_nurikabe() > 1:
            if len(liberties)==1:
                for each_liberty in liberties:
#                     print("  nurikabe has only one liberty",each_liberty.coords)
                    self.board.queue_nurikabe_cell(each_liberty)
    def make_new_path(self,members):
        return NurikabePath(self.board,self,members)
    def path_overlaps(self):
        common = Path.common_to_all_paths(self.paths)
        for each_cell in common:
            self.board.queue_nurikabe_cell(each_cell)
    def remove_paths_excluding_island_paths(self,other_island):
        if self._paths is None: return False
        removed_something = False
        P = len(self._paths)
        while P:
            P-=1
            each_path = self._paths[P]
            if other_island.all_paths_are_blocked_by_path(each_path):
#                 print("  removing",each_path,"from",self)
                removed_something = True
                self._paths.remove(each_path)
        return removed_something


class TemporaryExclusiveGroup(ExclusiveGroup):
    def __init__(self,board):
        self._quick_can_reach_islands = None
        self._can_reach_islands = None
        super().__init__(board)
    def add_member(self,new_cell):
        super().add_member(new_cell)
        self._quick_can_reach_islands = None
        self._can_reach_islands = None
    def calculate_quick_can_reach(self):
        self._quick_can_reach_islands = []
        for each_island in self.board.islands:
            can_reach = False
            M = len(self._members)
            for each_member in self._members:
                delta_x = each_island.starting_cell.x - each_member.x
                delta_y = each_island.starting_cell.y - each_member.y
                steps_to_reach = abs(delta_x) + abs(delta_y)
                if steps_to_reach + M <= each_island.count: can_reach= True
            if can_reach:
                self._quick_can_reach_islands.append(each_island)
        
    def calculate_can_reach(self):
#         print("  calculating slow can reach for",self)
        self._can_reach_islands = []
        if self._quick_can_reach_islands is None:
            self.calculate_quick_can_reach()
        for each_island in self._quick_can_reach_islands:
            if each_island.is_complete(): continue
#             print("    checking",each_island)
            can_reach = False
            if each_island.paths is None: 
#                 print("      no paths yet")
                self._can_reach_islands = None
                return
            for each_path in each_island.paths:
                if not each_path.terminated:
#                     print("      paths not yet all terminated")
                    self._can_reach_islands = None
                    return
#                 print("      checking",each_path)
                if can_reach: continue
                if self.members.intersection(self.get_relevant_members_from_path(each_path)) == self.members:
                    can_reach=True
            if can_reach:
                self._can_reach_islands.append(each_island)

    def get_relevant_members_from_path(self,possible_path):
        # to be safe, get absorbed orphans too
        return possible_path.all_members
                    
    def can_reach_island(self,possible_island):
        # will return a quick answer if full answer is not available yet, so it errs on the side of True
        if self._can_reach_islands is None:
            if self._quick_can_reach_islands is None:
                self.calculate_quick_can_reach()
            if possible_island in self._quick_can_reach_islands:
                return True
        else:
            if possible_island in self._can_reach_islands:
                return True
        return False
        
        
class Unassigned(TemporaryExclusiveGroup):
    def get_display_char(self, requesting_cell):
        return '-'
    def get_can_reach_islands(self):
        return self._can_reach_islands
    def get_relevant_members_from_path(self,possible_path):
        # for Unassigned, save time by not bothering with absorbed orphans
        return possible_path.members
    def can_reach_any_island(self):
        # will return a quick answer if full answer is not available yet, so it errs on the side of True
        if self._can_reach_islands is None:
            if self._quick_can_reach_islands is None:
                self.calculate_quick_can_reach()
            if self._quick_can_reach_islands:
                return True
        else:
            if self._can_reach_islands:
                return True
        return False


class OrphanIsland(TemporaryExclusiveGroup):
    def __init__(self,board,can_reach_islands=None):
        self._can_reach_islands = can_reach_islands
        self._must_reach_island = None
        super().__init__(board)
    def get_display_char(self, requesting_cell):
        return 'O'
    def get_mandatory_island(self):
        if self._can_reach_islands is None:
            if self._quick_can_reach_islands is None:
                self.calculate_quick_can_reach()
            if len(self._quick_can_reach_islands) == 1:
                return self._quick_can_reach_islands[0]
        else:
            if len(self._can_reach_islands) == 1:
                return self._can_reach_islands[0]
        return None
            
    def update(self):
        print("updating group",str(self))
        self._changed=False
        liberties = self.liberties
#         print("  orphan island",str(self),"has",len(liberties),"liberties",self.liberty_coords)
        if len(liberties)==1:
            for each_liberty in liberties:
#                 print("    orphan island",str(self),"has only one liberty",each_liberty.coords)
                self.board.queue_island_cell(each_liberty)
    def merge_with(self,other_group):
        # rare possibility, but it could happen
        if type(other_group) is OrphanIsland:
            self.board.replace_required_orphans(self,other_group)
        super().merge_with(other_group)


class Path(CellGroup):
    def __init__(self,board,group,starting_cells):
        super().__init__(board)
        self._group = group
        self._terminated = False
        while starting_cells:
            self.add_member(starting_cells.pop())
        self.update_liberties()
        self.check_terminated()
    def __str__(self):
        if self.terminated:
            return super().__str__() + " terminated"
        return super().__str__()
    @property
    def all_members(self):
        return self.members
    @property
    def cells_blocked(self):
        return self.members
    def get_path_length(self):
        return len(self.members)
    @property
    def group(self):
        return self._group
    @property
    def terminated(self):
        return self._terminated
    def check_terminated(self):
        pass
            
    def extend(self):
        pass
    
    @classmethod
    def common_to_all_paths(cls,paths):
        common = set([])
        if paths:
            common.update(paths[0].members)
            P = len(paths)
            while P>1:
                P-=1
                common.intersection_update(paths[P].members)
        return common
    @classmethod
    def common_neighbor_to_all_paths(cls,paths):
        common = set([])
        if paths:
            for each_path in paths:
                if not each_path.terminated:
                    return common
            common.update(paths[0].liberties)
            P = len(paths)
            while P>1:
                P-=1
                common.intersection_update(paths[P].liberties)
        return common
    @classmethod
    def common_cells_blocked_by_all_paths(cls,paths):
        common = set([])
        if paths:
            common.update(paths[0].cells_blocked)
            P = len(paths)
            while P>1:
                P-=1
                common.intersection_update(paths[P].cells_blocked)
        return common
        


class IslandPath(Path):
    def __init__(self,board,group,starting_cells,absorbed_orphans=None):
        if absorbed_orphans is None:
            self._absorbed_orphans = set([])
        else:
            self._absorbed_orphans = absorbed_orphans
        super().__init__(board,group,starting_cells)
    def __str__(self):
        return super().__str__() + " with orphans "+str([str(each_orphan) for each_orphan in self.absorbed_orphans])
    @property
    def all_members(self):
        all_members = self.members.copy()
        for each_orphan in self._absorbed_orphans:
            all_members.update(each_orphan.members)
        return all_members
    @property
    def cells_blocked(self):
        cells_blocked = self.all_members
        if self.terminated:
            cells_blocked.update(self.liberties)
        return cells_blocked
    @property
    def absorbed_orphans(self):
        return self._absorbed_orphans
    def get_absorbed_orphan_count(self,orphan_set=None):
        if orphan_set is None:
            orphan_set = self._absorbed_orphans
        count = 0
        for each_orphan in orphan_set:
            count += len(each_orphan.members)
        return count
    def get_path_length(self):
        return len(self.members)+self.get_absorbed_orphan_count()
    def check_terminated(self):
        if self.group.missing_cell_count() == self.get_path_length():
            self._terminated = True
    def update_liberties(self):
        super().update_liberties()
        self._liberties.update(self.group.liberties)
        for each_orphan in self._absorbed_orphans:
            self._liberties.update(each_orphan.liberties)
        self._liberties.difference_update(self.members)
        self._liberties.difference_update(self.group.members)
        for each_orphan in self._absorbed_orphans:
            self._liberties.difference_update(each_orphan.members)
        
    def extend(self):
#         print("  extending path",self)
        for each_liberty in self.liberties:
            if type(each_liberty.group) is Unassigned:
#                 print("    trying liberty",each_liberty.coords)
                can_extend = True
                new_absorbed_orphans = set([])
                for each_next_liberty in each_liberty.liberties:
                    if each_next_liberty in self.members: continue
                    if type(each_next_liberty.group) is Island:
                        if each_next_liberty.group is not self.group:
                            can_extend = False
                    else:
                        if type(each_next_liberty.group) is OrphanIsland:
                            if each_next_liberty.group not in self._absorbed_orphans:
                                new_absorbed_orphans.update([each_next_liberty.group])
                new_path_length = self.get_path_length() + 1 + self.get_absorbed_orphan_count(new_absorbed_orphans)
                missing_required_orphans = self.group.required_absorbed_orphans - self._absorbed_orphans - new_absorbed_orphans
                # check that the path length is not exceeded, or is impossible given missing orphans (note: must add not only the size of the missing orphans, but one extra cell to connect to one or more missing orphans iff there is at least one missing orphan - hence the int(bool(missing_required_orphans)))
                if new_path_length + self.get_absorbed_orphan_count(missing_required_orphans)+int(bool(missing_required_orphans))>self.group.missing_cell_count():
                    can_extend=False
                if can_extend:
                    new_path_members = self.members.copy()
                    new_path_members.add(each_liberty)
                    new_path_absorbed_orphans = self._absorbed_orphans.copy()
#                     print("    making new path",self,"with",each_liberty.coords)
                    new_path_absorbed_orphans.update(new_absorbed_orphans)
                    if new_path_length == self.group.missing_cell_count():
                        # if terminated, check for pool
                        # Note: this rough calculation of the set of liberties that would turn nurikabe 
                        #   might include island cells or orphan island cells but that's ok because they won't get counted when pool checking
                        nurikabe_neighbors = self.liberties.copy()
                        nurikabe_neighbors.update(each_liberty.liberties)
                        nurikabe_neighbors.difference_update(new_path_members)
                        for each_pool in Cell.get_all_possible_pools_from_cells(nurikabe_neighbors):
                            if each_pool.check_if_path_causes_pool(nurikabe_neighbors):
                                continue
                    self.group.add_path_left(new_path_members,absorbed_orphans = new_path_absorbed_orphans)


class NurikabePath(Path):
    def check_terminated(self):
        for each_cell in self.liberties:
            if type(each_cell.group) is Nurikabe and each_cell.group is not self.group:
                self._terminated = True
                return
    def update_liberties(self):
        super().update_liberties()
        self._liberties.update(self.group.liberties)
        self._liberties.difference_update(self.members)
        self._liberties.difference_update(self.group.members)
            
    def extend(self):
#         print("  extending path",self)
        for each_liberty in self.liberties:
            if type(each_liberty.group) is Unassigned:
#                 print("    trying liberty",each_liberty.coords)
                new_path_members = self.members.copy()
                new_path_members.add(each_liberty)
                for each_pool in Cell.get_all_possible_pools_from_cells(new_path_members):
                    if each_pool.check_if_path_causes_pool(new_path_members):
                        continue
                self.group.add_path_left(new_path_members)


class PossiblePool(CellGroup):
    def update_liberties(self):
        pass
    def add_member(self, new_cell):
        CellGroup.add_member(self, new_cell)
        new_cell.add_possible_pool(self)
    def delete(self):
        for each_cell in self.members:
            each_cell.remove_possible_pool(self)
        self._members.clear()
        self.board.del_group(self)
    def check_for_forced_island(self):
        if self.count_nurikabe_cells()==3:
            for each_cell in self.members:
                if type(each_cell.group) is Unassigned:
                    self.board.queue_island_cell(each_cell)
    def check_if_path_causes_pool(self,path_nurikabe_cells):
        if self.count_nurikabe_cells(path_nurikabe_cells)==4:
            return True
        return False
    def count_nurikabe_cells(self,path_nurikabe_cells=None):
        count = 0
        for each_cell in self.members:
            if type(each_cell.group) is Nurikabe:
                count +=1
        if path_nurikabe_cells is not None:
            overlap = self.members.intersection(path_nurikabe_cells)
            for each_cell in overlap:
                if type(each_cell.group) is Unassigned:
                    count +=1
        return count

class Board():
    def __init__(self,board_str_lines):
        self._Y = len(board_str_lines)
        self._X = len(board_str_lines[0]) #Assumed here that every line has the same number of chars
        self._islands = []
        self._orphan_islands = []
        self._complete_islands = []
        self._nurikabe = []
        self._unassigned = []
        self._possible_pools = []
        self._island_cell_queue = deque()
        self._nurikabe_cell_queue = deque()
        self._current_island_path_length = 0
        self._current_nurikabe_path_length = 0
        print("initializing board")
        board_rows = []
        y=0
        for line in board_str_lines:
#             print(line)
            board_row = []
            x=0
            for character in line:
                new_group = None
                count = Island.character_to_count(character)
                if count:
                    new_group = Island(self, count = count)
                    self._islands.append(new_group)
                else:
                    new_group = Unassigned(self)
                    self._unassigned.append(new_group)
                new_cell = Cell(new_group,x,y)
                board_row.append(new_cell)
                if x>0:
                    previous_cell = board_row[x-1]
                    new_cell.add_liberty(previous_cell)
                    previous_cell.add_liberty(new_cell)
                if y>0:
                    above_cell = board_rows[y-1][x]
                    new_cell.add_liberty(above_cell)
                    above_cell.add_liberty(new_cell)
                    if x>0:
                        pool_cell1 = new_cell
                        pool_cell2 = board_row[x-1]
                        pool_cell3 = above_cell
                        pool_cell4 = board_rows[y-1][x-1]
                        if type(pool_cell1.group) is not Island and type(pool_cell2.group) is not Island and type(pool_cell3.group) is not Island and type(pool_cell4.group) is not Island:
                            possible_pool = PossiblePool(self)
                            possible_pool.add_member(pool_cell1)
                            possible_pool.add_member(pool_cell2)
                            possible_pool.add_member(pool_cell3)
                            possible_pool.add_member(pool_cell4)
                            self._possible_pools.append(possible_pool)
                x += 1
            board_rows.append(board_row)
            y += 1
#         print("  initial island liberty update")
        self.update_group_liberties()
    @property
    def islands(self):
        return self._islands
    
    def __str__(self):
        board_rows = [[' ' for i in range(0,10 + 3*self._X)] for j in range(0,self._Y)]
#         group_color_map = {Island:"\033[1;38m",OrphanIsland:"\033[1;31m",Nurikabe:"\033[1;m",Unassigned:"\033[1;47m"}
#         group_color_suffix = "\033[1;m"
        group_color_suffix = ""
        for each_group in itertools.chain(self._islands,self._complete_islands,self._orphan_islands,self._nurikabe,self._unassigned):
#             group_color_prefix = group_color_map[type(each_group)]
            group_color_prefix = ""
            for each_cell in each_group.members:
                board_rows[each_cell.y][each_cell.x] = group_color_prefix+str(each_cell)+group_color_suffix
                board_rows[each_cell.y][each_cell.x + self._X + 5]= str(len(each_cell.liberties))
                board_rows[each_cell.y][each_cell.x + 2*self._X + 10]= CellGroup.count_to_character(len(each_cell.group.liberties))
        board_lines = []
        for each_row in board_rows:
            board_lines.append(' '.join(each_row))
        return '\n'+'\n'.join(board_lines)

    def count_nurikabe(self):
        return len(self._nurikabe)

    def create_new_nurikabe(self, starting_cell):
#         print("  creating new nurikabe group at",starting_cell.coords)
        new_group = Nurikabe(self)
        self._nurikabe.append(new_group)
        starting_cell.group = new_group
        # if there was only one nurakabe, it had no reason to grow so it would have ignored an update.  so tell it to wake up.
        if len(self._nurikabe)==2:
            self._nurikabe[0].update()

    def create_new_orphan_island(self, starting_cell):
#         print("  creating new orphan island group at",starting_cell.coords)
        new_group = OrphanIsland(self,can_reach_islands=starting_cell.group.get_can_reach_islands())
        self._orphan_islands.append(new_group)
        starting_cell.group = new_group
        
    def del_group(self,empty_group):
        if type(empty_group) is OrphanIsland:
            self._orphan_islands.remove(empty_group)
        if type(empty_group) is Nurikabe:
            self._nurikabe.remove(empty_group)
        if type(empty_group) is Unassigned:
            self._unassigned.remove(empty_group)
        if type(empty_group) is PossiblePool:
            self._possible_pools.remove(empty_group)
        

    def queue_nurikabe_cell(self,queue_cell):
        if type(queue_cell.group) is Unassigned and queue_cell not in self._nurikabe_cell_queue:
            print("      queuing nurikabe cell",queue_cell.coords)
            self._nurikabe_cell_queue.append(queue_cell)

    def queue_island_cell(self,queue_cell):
        if type(queue_cell.group) is Unassigned and queue_cell not in self._island_cell_queue:
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
        if self._unassigned:
            return False
        return True
            
    def solve(self):
        start_time = time.clock()
        self.update()
        self.clear_cell_queue()
        self.mark_cant_reach() #only quick at this point, since no path info has been calculated
        self.clear_cell_queue()
        print()
        print("starting path iteration..............................................")
        solution_steps = [self.close_completed_islands,
                          self.remove_island_paths_excluding_other_island_paths,
                          self.remove_nurikabe_paths_excluding_island_paths_and_vice_versa,
                          self.calculate_slow_can_reach,
                          self.mark_cant_reach,
                          self.mark_must_reach,
                          self.island_path_overlaps,
                          self.nurikabe_path_overlaps,
                          self.build_island_paths,
                          self.build_nurikabe_paths,
                          self.increment_nurikabe_path_length,
                          self.increment_island_path_length]
        self._current_island_path_length = 1
        self._current_nurikabe_path_length = 1
        solution_step_index = 0
        while not self.is_solved() and solution_step_index<len(solution_steps):
            print("on step",solution_step_index,solution_steps[solution_step_index].__name__)
            if solution_steps[solution_step_index]():
                # a solution step function should return true if it changed something important without queuing cells - e.g. incrementing path lengths
                solution_step_index = 0
                continue
            if self.has_queued_cells():
                self.clear_cell_queue()
                solution_step_index = 0
                continue
            solution_step_index +=1
        print(self)
        if self.is_solved():
            print("solved!  :)")
        else:
            print("not solved!  :( ",len(self._unassigned),"unassigned cells")
        elapsed_time = time.clock()-start_time
        print ("elapsed time: {:.3f} ms.".format(elapsed_time*1000))
        
    def get_max_island_path_length(self):
        length = 0
        for each_island in self._islands:
            if each_island.missing_cell_count() > length:
                length = each_island.missing_cell_count()
        return length

    def close_completed_islands(self):
        for each_island in self._islands:
            each_island.close_completed()

    def mark_cant_reach(self):
        # will default to quick can reach - must manually call calculate_can_reach_islands() on each group for more exact info taking into account available island paths
        for each_unassigned in self._unassigned:
            if not each_unassigned.can_reach_any_island():
                for each_cell in each_unassigned.members:
                    self.queue_nurikabe_cell(each_cell)

    def mark_must_reach(self):
        for each_orphan in self._orphan_islands:
            mandatory_island = each_orphan.get_mandatory_island()
            if mandatory_island is not None:
                if each_orphan not in mandatory_island.required_absorbed_orphans:
                    mandatory_island.add_required_absorbed_orphan(each_orphan)
                    mandatory_island.path_overlaps()
    
    def replace_required_orphans(self,old_orphan,new_orphan):
        for each_island in self._islands:
            each_island.replace_required_orphans(old_orphan,new_orphan)
    
    def calculate_slow_can_reach(self):
#         print()
#         print("calculating slow can reach")
        for each_unassigned in itertools.chain(self._unassigned,self._orphan_islands):
            each_unassigned.calculate_can_reach()
        
    def build_island_paths(self):
        if self.all_island_paths_terminated(): return
        print("  building island paths of length",self._current_island_path_length)
        length = self._current_island_path_length
        for each_island in self._islands:
            each_island.extend_paths_to(length)

    def all_island_paths_terminated(self):
        for each_group in self._islands:
            if not each_group.all_paths_terminated():
                return False
        return True

    def build_nurikabe_paths(self):
        if len(self._nurikabe)==1: return
        if self.all_nurikabe_paths_terminated(): return
        print("  building nurikabe paths of length",self._current_nurikabe_path_length)
        length = self._current_nurikabe_path_length
        for each_nurikabe in self._nurikabe:
            each_nurikabe.extend_paths_to(length)
        self.brief_report_paths()

    def all_nurikabe_paths_terminated(self):
        for each_group in self._nurikabe:
            if not each_group.all_paths_terminated():
                return False
        return True

    def increment_island_path_length(self):
        if self._current_island_path_length < self.get_max_island_path_length():
            self._current_island_path_length += 1
            return True

    def increment_nurikabe_path_length(self):
#         if self._current_island_path_length > self._current_nurikabe_path_length or self._current_island_path_length>=self.get_max_island_path_length():
#             if self._current_nurikabe_path_length < len(self._unassigned):
#                 self._current_nurikabe_path_length += 1
#                 return True
        if self._current_nurikabe_path_length < 2*self._current_island_path_length:
            self._current_nurikabe_path_length += 1
            return True

    def super_brief_report_paths(self):
        self.super_brief_report_island_paths()
        self.super_brief_report_nurikabe_paths()
    def brief_report_paths(self):
        self.brief_report_island_paths()
        self.brief_report_nurikabe_paths()

    def report_paths(self):
        self.report_island_paths()
        self.report_nurikabe_paths()

    def brief_report_island_paths(self):
        print()
        for each_island in self._islands:
            if each_island.paths is None:
                print("no paths for island",each_island)
            else:
                print(len(each_island.paths),"paths for island",each_island)

    def super_brief_report_island_paths(self):
        count = 0
        for each_island in self._islands:
            if each_island.paths is not None:
                count += len(each_island.paths)
        print(count,"island paths built")

    def report_island_paths(self):
        print()
        for each_island in self._islands:
            print("built paths for island",each_island)
            if each_island.paths is None:
                print("  no paths")
            else:
                for each_path in each_island.paths:
                    print("  path",each_path)

    def report_nurikabe_paths(self):
        print()
        for each_nurikabe in self._nurikabe:
            print("built paths for nurikabe",each_nurikabe)
            if each_nurikabe.paths is None:
                print("  no paths")
            else:
                for each_path in each_nurikabe.paths:
                    print("  path",each_path)
                    
    def brief_report_nurikabe_paths(self):
        print()
        for each_nurikabe in self._nurikabe:
            if each_nurikabe.paths is None:
                print("no paths for nurikabe",each_nurikabe)
            else:
                print(len(each_nurikabe.paths),"paths for nurikabe",each_nurikabe)
    def super_brief_report_nurikabe_paths(self):
        count = 0
        for each_nurikabe in self._nurikabe:
            if each_nurikabe.paths is not None:
                count += len(each_nurikabe.paths)
        print(count,"nurikabe paths built")


    def island_path_overlaps(self):
        for each_island in self._islands:
            each_island.path_overlaps()

    def nurikabe_path_overlaps(self):
        for each_nurikabe in self._nurikabe:
            each_nurikabe.path_overlaps()

    def remove_island_paths_blocking_nurikabe_liberties(self):
#         self.report_paths()
#         print("removing island paths that block all nurikabe liberties")
        did_something = False
        for each_nurikabe in self._nurikabe:
            for each_island in self._islands:
                did_something |= each_island.remove_paths_blocking_nurikabe_liberties(each_nurikabe)
#         self.report_paths()
        return did_something
    
    def remove_island_paths_excluding_other_island_paths(self):
#         self.report_paths()
#         print("removing island paths that block all of another island's paths and island paths blocked by all of another island's paths")
        did_something = False
        # note that the action is not symmetric, so we're not doing each pair twice here
        for each_island in self._islands:
            cells_blocked = each_island.cells_blocked
            for each_other_island in self._islands:
                if each_other_island is each_island: continue
                did_something |= each_island.remove_paths_excluding_other_island_paths(each_other_island)
                if not each_other_island.all_paths_terminated(): continue
                did_something |= each_other_island.remove_paths_containing_blocked_cells(cells_blocked)
#         self.report_paths()
        return did_something
    def remove_nurikabe_paths_excluding_island_paths_and_vice_versa(self):
#         self.report_paths()
        did_something = False
        for each_nurikabe in self._nurikabe:
            for each_island in self._islands:
                did_something |= each_nurikabe.remove_paths_excluding_island_paths(each_island)
                did_something |= each_island.remove_paths_excluding_nurikabe_paths(each_nurikabe)
#         self.report_paths()
        return did_something
    
    def has_queued_cells(self):
        if self._island_cell_queue or self._nurikabe_cell_queue: return True
        return False

    def clear_cell_queue(self):
        print()
        print("clearing island cell queue",[each_cell.coords for each_cell in self._island_cell_queue])
        print("clearing nurikabe cell queue",[each_cell.coords for each_cell in self._nurikabe_cell_queue])
        while self.has_queued_cells():
            while self._nurikabe_cell_queue:
                print()
                print("popping nurikabe cell",self._nurikabe_cell_queue[0].coords,"from queue",[each_cell.coords for each_cell in self._nurikabe_cell_queue])
                changing_cell = self._nurikabe_cell_queue.popleft()
                changing_cell.become_nurikabe()
                if self.invalidate_paths(changing_cell):
                    self._current_island_path_length = 1
                    self._current_nurikabe_path_length = 1
                print(self)
                self.update()
            while self._island_cell_queue:
                print()
                print("popping island cell",self._island_cell_queue[0].coords,"from queue",[each_cell.coords for each_cell in self._island_cell_queue])
                changing_cell = self._island_cell_queue.popleft()
                changing_cell.become_island()
                if self.invalidate_paths(changing_cell):
                    self._current_island_path_length = 1
                    self._current_nurikabe_path_length = 1
                print(self)
                self.update()

    def invalidate_paths(self, changing_cell):
        did_something = False
        for each_group in itertools.chain(self._islands,self._nurikabe):
            did_something |= each_group.invalidate_paths(changing_cell)
        return did_something

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
    board_str1 = '''\
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
    board_str6 = '''\
2--2--3--3-1-2-3-1-3
--------------------
2--3-4-----1--------
--------3-7--2--3---
c-3------------5--2-
-----2--------------
-------2-1----------
----1-----2---3-----
-----1--1---1----3--
2------1---1----1---
--------3---1----1-2
-3----2----1-3------
---3----1-------4---
---------5-1-5-2---2
--3--1-1------------
1-----4-------------
-2--1----4------2--3
---1---------2-4----
----1-1-------------
3-------4-----------\
'''
# board_str7 has no solution?  changed 2--6 to 3--6
    board_str7 = '''\
1-3-3---2-3--4--2-1-
--------------------
1---3-3--1---------3
-----------3----4---
8-----2-2-3--2------
-----------------2--
2----1------2--1---3
------1-2-1---1-----
-1---------2---4----
---3--9--1---1------
3-2--1----2---1-3--3
----3-------3-------
----------1----3----
-7---------1--------
-----3------1-1-----
2------3--6----3-6--
-----1------2-------
-1--4--------------3
--1-----3-----1-----
1---------------2---\
'''
    board_str8 = '''\
----2--1-2-----1-4--
4------------3------
---1-1--------2-1-1-
1-2------3--4----3--
-----7-------1-2---3
3------2---1--------
---2------3-2-------
-----3--3-----3---3-
1-2-1-------1-------
-----------2-7-5----
1--2--2--2----------
-2-----------------2
---1-4----3-----1---
--2--------------4--
1---2--1-4--1--2----
---1--4-------------
4-1-3---3---3---1---
-----------------2--
--2-------2--3--1---
--------1---------1-\
'''
# board 9 will require some multiple-path checks.
    board_str9 = '''\
1-2-3---1-2--3--4-2-
--------------------
2--3---3---2-------2
--6---1---1--2------
-----4-2-1-4---2--2-
1------------3------
--------a-------3---
1-----3------1-----2
-3--3---------1-----
-----------3---2--1-
------6-------------
3-1--2------2--2----
--------------2--3--
---------3--1---3---
2-4--------2-------3
----3--------1------
-2-3----4-----3--1--
-----3----1-1---1---
-----------1-1-1-2--
2----2--------------\
'''
    board_str10 = '''\
2-2-2--2-2-4
------------
---3--4-----
4--------2--
------------
---3--2-1-1-
2-----------
--6----3---2
3---1-1-----
-------1-1--
-----2--1-1-
------------\
'''
    board_str11 = '''\
1-1-1-3---1-
------------
3-1-1------3
---3-5--4---
------------
6-----1--4--
----1--4----
---1-1------
---------3--
4--1--------
----3-------
---1---1-1-1\
'''
    board_str12 = '''\
4-2-4---3--3
------------
---3--------
--3-----1-3-
-----3------
3---4--5----
------------
--2-------1-
------------
4----3--3--3
------------
4----2--2---\
'''
    board_str13 = '''\
2--2--1-2--2
------------
2--2-2-3----
------------
4---2-----4-
------3--2-1
4-----------
-----2--1-1-
------1-----
3-3--3--2---
----------3-
--------1---\
'''
    board_str14 = '''\
a-1-2-3--2-1
------------
---3--------
------2--4--
-----2------
---2---5--1-
---------1--
1-2-3-----1-
------------
1--2--3--1-1
-1---1------
---------1-1\
'''
    board_str15 = '''\
1-4--1-1-2--
------------
4---2--3-3--
------------
---3-1---3--
4-----3-----
---------3--
--1-3-1----4
3------3----
---2--------
-----2---1--
2-----------\
'''
    board_str16 = '''\
6-1-2--3--3-
------------
-------2----
----4----2--
1-1--------1
-2---3--3---
---1-------1
--4--1------
1-----4----1
----3-------
4------2-2--
------------\
'''
    board_str17 = '''\
4-3--1-1-2--1--
-------------2-
----3-3---6----
--2------2-----
1-----3--------
----------2----
8---4-------1-2
-------3---2---
4----2---8---3-
---------------
------3----1---
--3--2---------
--------------3
1-----3--1-----
--3--------2---\
'''
    board_str18 = '''\
1----2---------
--2-----------4
-1--2---3-1----
------3-----1--
--3--2--2-----2
---------------
------2-------7
----3---3-1----
--4----2-------
-----3----2---4
--3----1-------
----------3---5
---------------
---5-----------
----1-6-2--4-3-\
'''
    board_str19 = '''\
--4--1---3----2
----1-----1-b--
---3-----4----2
---------------
2-1---1-3------
----1---------5
--3---1--------
----2----------
-------2----3-3
3--2-3---1-----
--------2---2--
---4------2----
-------2----1-1
-3---------4---
------3-------3\
'''
    board_str20 = '''\
1--------1----2
---2-----------
-1---4------3--
---------4-----
1-2----3----3-3
----2----------
------2--3-----
---5----2-----2
------------4--
--2--3-1--3----
----2---1---2-3
--2------------
-----4--2-3----
---------------
2--3--2-1-1-3-3\
'''
    board_str21 = '''\
-2------2--2---
--------------3
-1---4-1-------
---------2--4-1
-1--4-2-1------
----------2----
---------1----2
---4-3------3--
--------4------
---------------
-----5----4---4
4-----1-4------
--5-------2-4--
---------------
--4-3-2--3--2-3\
'''

    this_board = Board(board_str_lines=board_str21.split('\n'))
    print(this_board)
    this_board.solve()
#     print(this_board._islands)
#     print(this_board._nurikabe[0],this_board._nurikabe[1])
#     print(this_board._orphan_islands)

    
if __name__ == "__main__": main()