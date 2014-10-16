from PySide.QtGui import *
from PySide.QtCore import *
import pyqtgraph as pg


class Hypnogram(pg.PlotItem):
    """Plot used for displaying sleep stages accross a night"""
    def __init__(self, lbl_dataset, *args, **kwargs):
        super(Hypnogram, self).__init__(*args, **kwargs)
        