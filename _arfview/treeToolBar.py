from PySide import QtCore,QtGui
import pyqtgraph as pg
from _arfview import datatree
import numpy as np

class treeToolBar(QtGui.QToolBar):
    """Toolbar at the bottom of the treeview"""
    def __init__(self, tree_model): 
        super(treeToolBar, self).__init__()
        self.tree_model = tree_model
        self.check_multiple_win = None
        self.initUI()

    def initUI(self):
        checkMultipleAction = QtGui.QAction('Check Multiple',self)
        checkMultipleAction.triggered.connect(self.check_multiple)
        uncheckAllAction = QtGui.QAction('Uncheck All', self)
        uncheckAllAction.triggered.connect(self.uncheck_all)
        self.addAction(checkMultipleAction)
        self.addAction(uncheckAllAction)

    def check_multiple(self):
        self.check_multiple_win = _checkMultipleWindow(self)
        self.check_multiple_win.show()

    def uncheck_all(self):
        indexes = self.tree_model.allDatasetIndexes()
        for idx in indexes:
             self.tree_model.setData(idx,QtCore.Qt.Unchecked,
                                     role=QtCore.Qt.CheckStateRole)
        
class _checkMultipleWindow(QtGui.QDialog):
    """Pop-up window that appears when the check multiple button is pressed. Allows for limitted queryingz"""
    def __init__(self, treeToolBar):
        super(_checkMultipleWindow, self).__init__()
        self.tree_model = treeToolBar.tree_model
        self.initUI()
        
    def initUI(self):
        self.attribute_label = QtGui.QLabel("Check entries with attribute")
        self.value_label = QtGui.QLabel("equal to")
        self.value_menu = QtGui.QComboBox()
        self.attribute_menu = attributeMenu(self.tree_model, self.value_menu)
        
        self.ok_button=QtGui.QPushButton("OK")
        self.ok_button.pressed.connect(self.button_pressed)
        
        ledge=0
        uedge=0
        
        layout=QtGui.QGridLayout()
        layout.addWidget(self.attribute_label, uedge+1, ledge)
        layout.addWidget(self.value_label, uedge+2, ledge)
        layout.addWidget(self.attribute_menu, uedge+1, ledge+1)
        layout.addWidget(self.value_menu, uedge+2,ledge+1)
        layout.setRowStretch(3, 2)
        layout.addWidget(self.ok_button, 3, 0)
        self.setLayout(layout)

    def button_pressed(self):
        key = self.attribute_menu.attribute
        value = self.attribute_menu.attribute_value
        indexes = self.tree_model.allDatasetIndexes()
        for idx in indexes:
            dataset = self.tree_model.getEntry(idx.internalPointer())
            attribute_objects = [dataset.attrs, dataset.parent.attrs]
            for attrs in attribute_objects:
                if key in attrs.keys() and attrs[key] == value:
                    self.tree_model.setData(idx, value=QtCore.Qt.CheckState.Checked,
                                            role=QtCore.Qt.CheckStateRole)

        self.close()
            
class attributeMenu(QtGui.QComboBox):
    """Combo box for selecting attributes to use as a criterion for checking datasets.
    When an attribute is selected, all of the values of this attribute that appear in the open
    files are shown in the value_menu combo box"""
    
    def __init__(self, tree_model, value_menu):
        super(attributeMenu, self).__init__()
        self.tree_model = tree_model
        self.value_menu = value_menu
        self.attribute = None
        self.attribute_value = None
        
        # adding all attribute keys in tree
        self.addItem('')
        indexes = self.tree_model.allDatasetIndexes()
        attributes = []
        for idx in indexes:
            dataset = self.tree_model.getEntry(idx.internalPointer())
            for a in dataset.attrs.keys() + dataset.parent.attrs.keys():
                 if a not in attributes:
                    attributes.append(a)
                    self.addItem(a)

        self.activated[str].connect(self.attribute_selected)
        self.value_menu.activated[str].connect(self.value_selected)
        
    def attribute_selected(self,text):
        self.attribute = text
        self.value_menu.clear()
        self.value_menu.addItem('')
        values = []
        indexes = self.tree_model.allDatasetIndexes()
        for idx in indexes:
            dataset = self.tree_model.getEntry(idx.internalPointer())
            attribute_objects= [dataset.attrs, dataset.parent.attrs]
            for attrs in attribute_objects:
                if self.attribute not in attrs.keys(): continue
                #avoiding problems with array comparison
                if isinstance(attrs[self.attribute], np.ndarray):
                    is_new_value = not np.any([np.array_equal(attrs[self.attribute],v)
                                               for v in values])
                else:
                    is_new_value = attrs[self.attribute] not in values
                if is_new_value:
                    values.append(attrs[self.attribute])
                    if self.attribute == 'datatype':
                        new_value = datatree.named_types[attrs[self.attribute]]
                    else:
                        new_value = str(attrs[self.attribute])
                    try:
                        self.value_menu.addItem(new_value)
                    except:
                        pass
                    
    def value_selected(self, text):
        if self.attribute == 'datatype':
            inverse_types = {value:key for key,value in
                             datatree.named_types.iteritems()}
            self.attribute_value = inverse_types[text]
        elif text.isdigit():
            self.attribute_value = float(text)
        else:
            self.attribute_value = text

        
            
