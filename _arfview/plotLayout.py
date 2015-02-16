from PySide import QtGui,QtCore
import pyqtgraph as pg

class plotLayout(pg.GraphicsLayoutWidget):
    """Scroll area in mainwin where plots are placed"""
    def __init__(self,parent=None*args,**kwargs):
        super(plotLayout,self).__init__(*args,**kwargs)
        
        