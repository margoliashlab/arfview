from PySide import QtCore, QtGui
import h5py
import time
import sys
import os

class TreeNode:
    def __init__(self,name,parent=None):
        self._name = name
        self._children = []
        self._parent = parent
        
        if parent is not None:
            parent.addChild(self)
            
    def addChild(self, child):
        self._children.append(child)
        child._parent = self

    def name(self):
        return self._name
        
    def child(self, row):
        return self._children[row]

    def childCount(self):
        return len(self._children)

    def parent(self):
        return self._parent
        
    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)
        else:
            return 0
        
            


class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, filenames, parent=None):
        super(TreeModel, self).__init__(parent)
        self.files = []
        self.roots = []
        for f in filenames:
            self.files.append(h5py.File(f,'r+'))
            abspath = os.path.abspath(f)
            self.roots.append(TreeNode(abspath))
            TreeModel.populate_tree(self.roots[-1],self.files[-1])

    def get_entry(self, node):
        """Gets arf entry from node"""
        #finding file
        child = node
        parent = child.parent()
        while parent != None:
            child = parent            
            parent = child.parent()

        file_idx = self.roots.index(child)

        #retrieving entry
        return self.files[file_idx][node.name()]
            
        
    @staticmethod 
    def populate_tree(node, h5group):
        if isinstance(h5group,h5py.File): 
            path = '/'
        else:
            path = node.name()
        if h5group.parent.get(path) is not None:
            for key in h5group.keys():
                h5obj = h5group.get(key)
                new_node = TreeNode(h5obj.name)
                node.addChild(new_node)
                if isinstance(h5obj,h5py.Group):
                    TreeModel.populate_tree(new_node, h5obj)
        

    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.files)
        else:
            node = parent.internalPointer()
            return node.childCount()

    def columnCount(self,parent):
        return 1

    def data(self,index,role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole:
            return node.name().split('/')[-1]


    def index(self, row, column, parent):
        if not parent.isValid():
            return self.createIndex(row,column,self.roots[row])
        else:
            parentNode = parent.internalPointer() 

        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
            
    def parent(self, index):
        node = index.internalPointer()
        parentNode = node.parent()

        if node in self.roots:
            return QtCore.QModelIndex()

        try:
            self.createIndex(parentNode.row(),0,parentNode.name())
        except Exception as e:
            print(e)
             
        return self.createIndex(parentNode.row(), 0, parentNode)


    def headerData(self,section,orientation,role):
        return "File Tree"




        
filenames = ['/home/pmalonis/test2.arf','/home/pmalonis/song.arf']
# root = TreeNode('/')
# for key in file.keys():
#     root.addChild(TreeNode(key))

model = TreeModel(filenames)
treeView = QtGui.QTreeView()
treeView.show()
treeView.setModel(model)