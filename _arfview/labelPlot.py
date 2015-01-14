from PySide.QtGui import *
from PySide.QtCore import *
import sys
import pyqtgraph as pg
import numpy as np
from utils import replace_dataset
import _arfview.utils as utils
import h5py
import arf
import pyqtgraph.functions as fn

class labelRegion(pg.LinearRegionItem):
    '''Labeled region on label plot'''
    def __init__(self, name, start, stop, parent, *args, **kwargs):
        super(labelRegion, self).__init__([start, stop], *args, **kwargs)
        parent.addItem(self)  
        self.text = pg.TextItem(name)
        self.text.setScale(2)
        parent.addItem(self.text)
        self.position_text_y()
        self.position_text_x()
        self.setMovable(False)
        self.getViewBox().sigYRangeChanged.connect(self.position_text_y)

    def position_text_y(self):
        yrange=self.getViewBox().viewRange()[1]
        self.text.setY(np.mean(yrange)*1.5)

    def position_text_x(self):
        xmin, xmax = self.getViewBox().viewRange()[0]
        if xmin <= self.getRegion()[0] <= xmax:
            self.text.setX(self.getRegion()[0])
        elif self.getRegion()[0] < xmin < self.getRegion()[1]:
            self.text.setX(xmin)
        else:
            self.text.hide()

            
class labelPlot(pg.PlotItem):
    '''Interactive plot for making and displaying labels
    '''
    sigLabelSelected = Signal()
    sigNoLabelSelected = Signal()
    
    def __init__(self, file, path, *args, **kwargs):
        super(labelPlot, self).__init__(*args, **kwargs)
        lbl = file[path]
        if not utils.is_complex_event(lbl):           
            raise TypeError("Argument must be complex event dataset")
        else:
             self.lbl = lbl
        #saving the file and the path allows access to non-anonymous reference to
        #the dataset, which is necessary for deleting labels
        self.file = file
        self.path = path          
        self.double_clicked = np.zeros(len(self.lbl),dtype=bool)
        self.installEventFilter(self)
        self.getViewBox().enableAutoRange(enable=False)
        #self.getAxis('left').hide()
        self.key = None
        self.dclickedRegion = None
        self.activeLabel = None
        if 'ms' in self.lbl.attrs['units']:
            self.scaling_factor = 1000.
        elif 'samples' in self.lbl.attrs['units']:
            self.scaling_factor = float(self.lbl.attrs['sampling_rate'])
        else:
            self.scaling_factor = 1.
        self.setMouseEnabled(y=False)
        self.max_plotted = 100
        self.getViewBox().sigXRangeChanged.connect(self.plot_all_events)
        self.plot_all_events()
        
    def plot_all_events(self):
        self.clear()
        if len(self.lbl) == 0: return 
        t_min,t_max = self.getAxis('bottom').range
        names = self.lbl['name']
        starts = self.lbl['start']/self.scaling_factor
        stops = self.lbl['stop']/self.scaling_factor
        first_idx = next((i for i in xrange(len(self.lbl)) if
                          stops[i]>t_min),0)
        last_idx = next((i for i in xrange(len(self.lbl)-1,0,-1)
                    if starts[i]<t_max),first_idx)
        n = last_idx - first_idx
        #labels that will be plotted
        if n > self.max_plotted:
            plotted_idx = (first_idx + int(np.ceil(i*n/self.max_plotted))
                           for i in xrange(self.max_plotted) )
        else:
            plotted_idx = xrange(first_idx,last_idx+1)

        #Keeps track of previous label so that if the stop of a red label equals
        #the start of the next, the red line from
        #the previous label won't be drawn over
        prev_was_clicked = False
        prev_stop = None
        for i in plotted_idx:
            if self.double_clicked[i]:
                line_color = ['r','r']
                brush_color = 'b'
                prev_was_clicked = True
            elif prev_was_clicked and prev_stop == self.lbl[i]['start']:
                line_color = ['y','r']
                brush_color = None
                prev_was_clicked = False
            else:
                line_color = None
                brush_color = None
                prev_was_clicked = False
                
            self.plot_complex_event(self.lbl[i],line_color=line_color,
                                    brush_color=brush_color)
            prev_stop = self.lbl[i]['stop']

        self.setActive(True)
            
    def plot_complex_event(self, complex_event, line_color=None,
                           brush_color=None,with_text=True):
        '''Plots a single event'''
        name = complex_event['name']
        start = complex_event['start'] / self.scaling_factor
        stop = complex_event['stop'] / self.scaling_factor
        region = labelRegion(name, start, stop, parent=self)

        if line_color is not None:
            for line,color in zip(region.lines,line_color):
                line.setPen(fn.mkPen(color))
        if brush_color is not None:
            region.setBrush(fn.mkBrush(brush_color))
        
        return region
        
    def sort_lbl(self):
        '''Sorts lbl dataset by start time'''
        data = self.lbl[:]
        sort_idx = data.argsort(order='start')
        data.sort(order='start')
        try:
            self.lbl[:] = data
        except Exception as e:
            raise e
            
        self.double_clicked = self.double_clicked[sort_idx]

        return sort_idx
        
    def delete_selected_labels(self):
        win = self.parentWidget().getViewWidget()
        if self.file.mode == 'r':
            QMessageBox.critical(win,"", "Cannot delete label. Make sure you have write permission for this file.", QMessageBox.Ok)
        else:
            reply = QMessageBox.question(win,"","Delete selected labels?",
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)
            if reply == QMessageBox.Yes:
                new_data = self.lbl[np.negative(self.double_clicked)]
                lbl = self.file[self.path] #non-anonymous lbl entry
                replace_dataset(lbl, lbl.parent, data=new_data, maxshape=(None,))
                self.lbl = self.file[self.path]
                self.double_clicked = np.zeros(len(self.lbl),dtype=bool)
                self.plot_all_events()
                self.sigNoLabelSelected.emit()
            

    def add_label(self, name, start, stop):
        """adds label to plot if possible.  Returns the index of the new label in the sorted dataset"""        
        if self.lbl.maxshape != (None,): #if dataset is extensible
            win = self.parentWidget().getViewWidget()        
            reply = QMessageBox.question(win,"", "Label cannot be added because dataset is not extensible. Replace with extensible dataset?", QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
            self.key = None  #because keyReleaseEvent may be ignored during message box display                
            if reply == QMessageBox.Yes:
                lbl = self.file[self.path] 
                self.lbl = replace_dataset(lbl, lbl.parent, data=lbl[:], maxshape=(None,))
            else:
                return 

        elif self.file.mode == 'r':
            win = self.parentWidget().getViewWidget()
            QMessageBox.critical(win,"", "Cannot add label. Make sure you have write permission for this file.", QMessageBox.Ok)
            self.key = None
            return 

        arf.append_data(self.lbl,(name,start,stop))
        self.double_clicked = np.append(self.double_clicked,False)
        sort_idx = self.sort_lbl()
        new_idx = np.argmax(sort_idx==(len(self.lbl)-1))
        self.plot_all_events()

        return new_idx
                           
    def keyPressEvent(self, event):
        """Records alphabetical key as a potential label in self.key.
        Labels the interval representing the entire current view if space bar is pressed
        at the same time as a key"""
        if event.text().isalpha():
            event.accept()
            self.key = event.text().lower()
        elif event.key() == Qt.Key_Space:
            if self.key is not None:
                name = self.key
                start, stop = self.getViewBox().viewRange()[0]
                self.add_label(name,start,stop)
        elif event.key() == Qt.Key_Backspace:
            self.delete_selected_labels()
        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        """Clears self.key if the key released is the key stored in self.key"""
        if event.text().lower() == self.key:
            event.accept()
            self.key = None
        else:
            event.ignore()
            
    def mouseClickEvent(self, event):
        """Creates a new label if alphabetical key is pressed"""
        if event.button() == Qt.LeftButton:
            pos=self.getViewBox().mapSceneToView(event.scenePos())
            t = pos.x() * self.scaling_factor
            if self.key and self.activeLabel is None:
                self.activeLabel = self.add_label(self.key,t,t)
                if (self.activeLabel is not None and
                    event.modifiers() != Qt.ShiftModifier):
                        self.sort_lbl()
                        self.activeLabel = None
            elif self.activeLabel is not None:
                i = self.activeLabel
                if t >= self.lbl[i]['start']:
                    self.lbl[i] = (self.lbl[i]['name'], self.lbl[i]['start'], t)
                else:
                    self.lbl[i] =  (self.lbl[i]['name'], t, self.lbl[i]['stop'])

                self.sort_lbl()
                self.plot_all_events()
                self.activeLabel = None

    def mouseDoubleClickEvent(self, event):
        """Used to select a label for potential deletion.  Changes the color of selected label"""
        if self.activeLabel: return
        previously_clicked = list(self.double_clicked)
        pos = event.scenePos()
        vb = self.getViewBox()
        pixel_margin = 5
        distances=np.zeros(len(self.lbl))
        in_range = [] #list of label indices the mouse is in range of
        for i,(start,stop) in enumerate(zip(self.lbl['start'],self.lbl['stop'])):
            scene_start =  vb.mapViewToScene(QPointF(start/self.scaling_factor,0)).x()
            scene_stop = vb.mapViewToScene(QPointF(stop/self.scaling_factor,0)).x()
            #distances[i] = np.abs(pos.x() - scene_start)
            if scene_start - pixel_margin < pos.x() < scene_stop + pixel_margin:
                in_range.append(i)
                self.double_clicked[i] = not self.double_clicked[i]

        # if any(in_range):
        #     idx = in_range[np.argmin(distances[i] for i in in_range)]
        #     self.double_clicked[idx] = not self.double_clicked[idx]
                
        self.plot_all_events()
        if any(self.double_clicked) and not any(previously_clicked):
            event.accept()
            if not any(previously_clicked):
                self.sigLabelSelected.emit()
        elif not any(self.double_clicked):
            event.ignore()
            if any(previously_clicked):
                self.sigNoLabelSelected.emit()

