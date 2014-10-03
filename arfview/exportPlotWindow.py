from PySide import QtGui, QtCore
from pyqtgraph.exporters.ImageExporter import ImageExporter
import os

class exportPlotWindow(QtGui.QDialog):
    def __init__(self, data_layout):
        super(exportPlotWindow, self).__init__()
        self.data_layout = data_layout
        self.initUI()

    def initUI(self):
        self.dialog_layout = QtGui.QGridLayout()
        self.setLayout(self.dialog_layout)
        self.dialog_layout.addWidget(QtGui.QLabel('Filename:'),0,0)
        self.dialog_layout.addWidget(QtGui.QLabel('Format:'),1,0)
        self.dialog_layout.addWidget(QtGui.QLabel('Width:'),2,0)
        self.dialog_layout.addWidget(QtGui.QLabel('Height:'),3,0)
        self.filename = QtGui.QLineEdit('')
        self.format = QtGui.QComboBox()
        self.format.addItems(['PNG','JPEG'])
        self.widthEdit = QtGui.QLineEdit('%d'%(self.data_layout.width()))
        self.widthEdit.textEdited.connect(self.proportionHeight)
        self.heightEdit = QtGui.QLineEdit('%d'%(self.data_layout.height()))
        self.heightEdit.textEdited.connect(self.proportionWidth)
        self.export = QtGui.QPushButton('Export')
        self.export.pressed.connect(self.exportPlot)
        self.cancel = QtGui.QPushButton('Cancel')
        self.cancel.pressed.connect(self.close)
        self.dialog_layout.addWidget(self.filename,0,1)
        self.dialog_layout.addWidget(self.format,1,1)
        self.dialog_layout.addWidget(self.widthEdit,2,1)
        self.dialog_layout.addWidget(self.heightEdit,3,1)
        self.dialog_layout.addWidget(self.export,4,1)
        self.dialog_layout.addWidget(self.cancel,4,0)
        self.validator = QtGui.QIntValidator()
        self.validator.setBottom(0)
        self.heightEdit.setValidator(self.validator)
        
    def proportionHeight(self):
        try:
            float(self.widthEdit.text())
        except:
            return
        ratio = self.data_layout.height()/self.data_layout.width()
        new_height = int(float(self.widthEdit.text()) * ratio)
        print(new_height)
        self.heightEdit.setText(unicode(new_height))
        
    def proportionWidth(self):
        try:
            float(self.heightEdit.text())
        except:
            return
        ratio = self.data_layout.width()/self.data_layout.height()
        new_width = int(float(self.heightEdit.text()) * ratio)
        print(new_width)
        self.widthEdit.setText(unicode(new_width))
        
    def exportPlot(self):
        try:
            if int(self.heightEdit.text()) < 0:
                return
            if int(self.widthEdit.text()) < 0:
                return
        except:
            return

        exporter = ImageExporter(self.data_layout)
        name = os.path.splitext(self.filename.text())[0]
        name += '.png' if self.format.currentText() == 'PNG' else '.jpg'
        exporter.parameters()['width'] = int(self.widthEdit.text())
        exporter.parameters()['height'] = int(self.heightEdit.text())
        exporter.export(name)
        self.close()

    