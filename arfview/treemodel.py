from PySide import QtCore, QtGui
import h5py
import time
import sys
import os
import arf
import subprocess

class TreeNode:
    def __init__(self,name, type, parent=None):
        if type not in ("File","Group","Dataset"):
            raise ValueError("Invalid type argument")
        
        self._name = name
        self._children = []
        self._parent = parent
        self._type = type
        
        if parent is not None:
            parent.addChild(self)
            
    def addChild(self, child):
        self._children.append(child)
        self._children.sort(key=lambda x: x.name())
        child._parent = self

    def removeChild(self, position):
        child = self._children.pop(position)
        child._parent = None
        for i in xrange(len(child._children)):
            grandkid.removeChild(i)
        
    def name(self):
        return self._name

    def setName(self, new_name):
        self._name = new_name
        
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

    def type(self):
        return self._type

class TreeModel(QtCore.QAbstractItemModel):
    def __init__(self, filenames, parent=None):
        super(TreeModel, self).__init__(parent)
        self.files = []
        self.roots = []
        #self.context_menu = QtGui.QMenu
        for f in filenames:
            success = self.insertFile(f)
            print success

    def getFile(self, node):
        '''Gets file object associated with node'''
        child = node
        parent = child.parent()
        while parent != None:
            child = parent            
            parent = child.parent()

        file_idx = self.roots.index(child)
        return self.files[file_idx]
        
    def getEntry(self, node):
        """Gets arf entry from node"""
        file = self.getFile(node)
        return file[node.name()]
            
    @staticmethod 
    def populate_tree(node, h5group):
        if isinstance(h5group,h5py.File): 
            path = '/'
        else:
            path = node.name()
        if h5group.parent.get(path) is not None:
            for key in h5group.iterkeys():
                h5obj = h5group.get(key)
                if isinstance(h5obj,h5py.Group):
                    new_node = TreeNode(h5obj.name, "Group")
                    node.addChild(new_node)
                    TreeModel.populate_tree(new_node, h5obj)
                else:
                    new_node = TreeNode(h5obj.name, "Dataset")
                    node.addChild(new_node)
                    
    def rowCount(self, parent):
        if not parent.isValid():
            return len(self.files)
        else:
            node = parent.internalPointer()
            return node.childCount()

    def columnCount(self,parent):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | \
            QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled
        
    def data(self,index,role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole):
            return node.name().split('/')[-1]
            
    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            if '/' in value:
                QtGui.QMessageBox.critical(self,"", "Entry name cannot contain '/' character.", QMessageBox.Ok)
                return False

            node = index.internalPointer()
            old_name = node.name()
            parent_name = '/'.join(old_name.split('/')[:-1])
            new_name = '/'.join([parent_name, value])
            file = self.getFile(node)
            try:
                file[new_name] = file[old_name]
                del file[old_name]
                node.setName(new_name)
                self.dataChanged.emit(index,index)
            except Exception as e:
                print(e.message)
                return False

            self.dataChanged.emit(index,index)
            return True

    # def mimeTypes(self):
    #     return ['arf-items']

    # def mimeData(self, indices):
    #     mimedata =
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
        try:
            parentNode = node.parent()
        except:
            print(node)
            return QtCore.QModelIndex()
            
        if node in self.roots or parentNode is None:
            return QtCore.QModelIndex()

        try:
            self.createIndex(parentNode.row(),0,parentNode.name())
        except Exception as e:
            print(e)
             
        return self.createIndex(parentNode.row(), 0, parentNode)

    # def insertRows(self, position, rows, parent=QtCore.QModelIndex()):
    #     if parent.isValid():
    #         parentNode = parent.internalPointer()
    #     self.beginInsertRows(parent, position, position + rows - 1)
    #     for row in range(rows):
    #         childNode = TreeNode("untitled")
    #         success = parentNode.addChild(childNode)

    #     self.endInsertRows()


    def deleteEntry(self, index):
        self.beginRemoveRows(index.parent(), index.row(), index.row())
        node = index.internalPointer()
        if node.type() == "File":
            return False
        file = self.getFile(node)
        try:
            del file[node.name()]
            node.parent().removeChild(node.row())
        except:
            return False
            
        self.endRemoveRows()
        return True

    def insertFile(self, filename, mode=None):
        self.beginInsertRows(QtCore.QModelIndex(),len(self.files)-1,len(self.files)-1)

        try:
            self.files.append(h5py.File(filename,mode))
        except:
            return False

        abspath = os.path.abspath(filename)
        try:
            self.roots.append(TreeNode(abspath, "File"))
            TreeModel.populate_tree(self.roots[-1],self.files[-1])
        except:
            self.files.pop(-1)
            if len(files)<len(roots):
                self.roots.pop(-1)
            return False
        self.endInsertRows()
        return True

    def insertGroup(self, parent):
        self.beginInsertRows(parent, 0, 0)
        parentNode = parent.internalPointer()
        if parentNode.type() == "Dataset":
            return False
            
        parentEntry = self.getEntry(parentNode)
        name = "%s/new"%parentEntry.name
        k = 1
        while name.split('/')[-1] in parentEntry.keys():
            name = "%s/new_%d"%(parentEntry.name,k)
            k+=1

        try:
            tstamp = subprocess.check_output(["date", "+%s"])
            arf.create_entry(parentEntry, name, tstamp)
        except Exception as e:
            print(e.message)
            return False

        try:
            new_node = TreeNode(name,'Group')
            parentNode.addChild(new_node)
        except Exception as e:
            print(e.message)
            del parentEntry[name]
            return False

        self.endInsertRows()
        index = self.index(new_node.row(), 0, parent)
        return index
        
    def closeFile(self, index):
        self.beginRemoveRows(QtCore.QModelIndex(), index.row(), index.row())
        try:
            node = index.internalPointer()
            i = self.roots.index(node)
            self.roots.pop(i)
            self.files[i].close()
            self.files.pop(i)
        except:
            return False

        self.endRemoveRows()
        return True

    def supportedDropActions(self):
        return QtCore.Qt.CopyAction
        
    def headerData(self,section,orientation,role):
        return "File Tree"
        

class ArfTreeView(QtGui.QTreeView):
    def __init__(self, *args, **kwargs):
        super(ArfTreeView, self).__init__(*args, **kwargs)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.onCustomConextMenuRequested)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        
    def delete_selected(self):
        reply = QtGui.QMessageBox.question(self,"","Are you sure you want to delete selected entries?",
                                         QtGui.QMessageBox.Yes | QtGui.QMessageBox.No,
                                         QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            selected = self.selectedIndexes()
            self.clearSelection()
            fail_message = False
            for index in selected:
                success = self.model().deleteEntry(index)
                if not success and not fail_message:
                    fail_message = True
            if fail_message:
                QtGui.QMessageBox.critical(self,"", "Could not delete all selected entries. Make sure you have write permission for the corresponding files.", QtGui.QMessageBox.Ok)
            

    def close_selected(self):
        selected = self.selectedIndexes()
        for index in selected:
            self.model().closeFile(index)
        
    def rename_selected(self):
        selected = self.selectedIndexes()
        self.clearSelection()
        if len(selected) == 1:
            self.edit(selected[0])

    def create_subgroup(self):
        selected = self.selectedIndexes()
        self.clearSelection()
        if len(selected) == 1:
            new_index = self.model().insertGroup(selected[0])
            if new_index:
                if not self.isExpanded(selected[0]):
                    self.setExpanded(selected[0], True)
                self.edit(new_index)
            else:
                QtGui.QMessageBox.critical(self,"", "Could create subgroup. Make sure you have write permission for the corresponding file.", QtGui.QMessageBox.Ok)
                

    def onCustomConextMenuRequested(self, pos):
        menu = QtGui.QMenu(self)
        menu.setParent(self)
        indices = self.selectedIndexes()
        nodes = [idx.internalPointer() for idx in indices]
        model = self.model()
        closeAction = QtGui.QAction("Close", menu)
        #closeAction.setShortcut(QtGui.QKeySequence("Ctrl+C"))
        closeAction.triggered.connect(self.close_selected)
        createAction = QtGui.QAction("Create subgroup", menu)
        #createAction.setShortcut(QtGui.QKeySequence("Ctrl+G"))
        createAction.triggered.connect(self.create_subgroup)
        deleteAction = QtGui.QAction("Delete", menu)
        #deleteAction.setShortcut(QtGui.QKeySequence("Ctrl+D"))
        deleteAction.triggered.connect(self.delete_selected)
        closeAction.triggered.connect(self.close_selected)
        renameAction = QtGui.QAction("Rename", menu)
        #renameAction.setShortcut("Ctrl+R")
        renameAction.triggered.connect(self.rename_selected)
        if all(node.type() == "File" for node in nodes):
            menu.addAction(closeAction)
        if all(node.type() in ("File","Group") for node in nodes) and len(nodes)==1:
            menu.addAction(createAction)
        if all(node.type() in ("Dataset","Group") for node in nodes):
            menu.addAction(deleteAction)
            if len(nodes) == 1:
                menu.addAction(renameAction)
            
        menu.exec_(pos)

    
        
filenames = ['/home/pmalonis/test2.arf','/home/pmalonis/test.arf']
# root = TreeNode('/')
# for key in file.keys():
#     root.addChild(TreeNode(key))
# app = QtGui.QApplication(sys.argv)
model = TreeModel(filenames)
treeView = ArfTreeView()
treeView.setModel(model)
treeView.show()
#sys.exit(app.exec_())