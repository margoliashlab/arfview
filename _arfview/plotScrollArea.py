from PySide import QtGui,QtCore
import pyqtgraph as pg

class plotScrollArea(QtGui.QScrollArea):
    """Scroll area in mainwin where plots are placed"""
    def __init__(self, parent=None, *args, **kwargs):
        super(plotScrollArea,self).__init__(*args,**kwargs)
        self.parent = parent
        
    def keyPressEvent(self,event):
        if event.key() not in [QtCore.Qt.Key_Up,QtCore.Qt.Key_Down,
                           QtCore.Qt.Key_Left,QtCore.Qt.Key_Right]:
            event.ignore()
        else:
            event.accept()
            for pl in self.parent.subplots:
                if pl.isUnderMouse():
                    min,max = pl.getViewBox().viewRange()[0]
                    range = max - min
                    if event.key() == QtCore.Qt.Key_Down:
                        pl.setXRange(min - range/2., max + range/2., padding=0)
                    elif event.key() == QtCore.Qt.Key_Up:
                        pl.setXRange(min + range/4., max - range/4., padding=0)
                    elif event.key() == QtCore.Qt.Key_Left:
                        if event.modifiers() ==QtCore.Qt.ControlModifier:
                            pl.setXRange(min - range/2., max - range/2., padding=0)
                        else:
                            pl.setXRange(min - range, max - range, padding=0)
                    elif event.key() == QtCore.Qt.Key_Right:
                        if event.modifiers() == QtCore.Qt.ControlModifier:
                            pl.setXRange(min + range/2., max + range/2., padding=0)
                        else:
                            pl.setXRange(min + range, max + range, padding=0)


                    break
                    
        