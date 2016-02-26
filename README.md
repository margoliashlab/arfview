Arfview
========

Arfview is a data visualization program for use with data in the [arf](https://github.com/dmeliza/arf/) format.

![](http://i60.tinypic.com/2rc9vnm.png)


Installation (Linux and OS X)
-----------------------------

A compiled stand-alone application for 64-bit Linux and OS X 10.9 can be downloaded from the releases page in this repository.


Building from source (Linux and OS X)
--------------------
  * Install [Anaconda](https://store.continuum.io/cshop/anaconda/).
  * In a new terminal window, install arfview:

        git clone https://github.com/margoliashlab/arfview.git
        cd arfview
        python setup.py install

To have audio playback, install [sox](http://sox.sourceforge.net/)

You may also need build dependencies for PySide and HDF5. In Ubuntu/Debian:

    sudo apt-get build-dep python-pyside python-h5py


Plotting
--------
To plot a dataset, select the dataset in the tree on the left-hand side of the window by clicking it with the left
mouse button.  You can also plot all of the datasets in a group by selecting the group. You can select multiple entries by holding down Ctrl while selecting the entries.  If you press Shift while clicking on an entry, all
of the entries between the current selected entry and the entry clicked will be selected.

You can also switch the selected dataset using keyboard shortcuts. If a single dataset or group is selected, Ctrl+F moves the selection to the next entry. If a single dataset is selected within a group, Ctrl+Shift+F selects the next dataset in the file with the same name. 

Plot Checked Mode
-----------------
To plot multiple datasets across groups or files, click the "Plot Checked Mode" button in the toolbar. Then check the datasets you want to plot, and click "Refresh Data View."  To select data based on attributes, select "Check Multiple" in the Tree toolbar.  Later versions will include the capability for more complex queries. 

Changing the View Range and Zoom
--------------------------------
There are three ways to change the view range in arfview:

1) *Mouse*. Hold down the left mouse button and drag the mouse to change the view range.  Hold down the right
mouse button to change the zoom.

2) *Arrow Keys*.  To use the arrow keys to adjust the zoom, first place the cursor over the plot you want to adjust. Press the down arrow key to double the zoom, and the up arrow key to halve it.  The right and left arrow keys move the view range in the time axis to the right or left (respectively) by the length of the current view window.  To move the range by half a window, hold down the Ctrl key and press the left or right arrow key.

3) *Context Menu*.  When you right click on a plot, a context menu appears that allows you to enter in specific values for the view range.  The menu also allows you to link the y-axes of different plots so that their ranges are always the same (the x-axes of all the plots are always linked).

Editing files
-------------
Arfview can be used to rename and delete entries, create new groups, and copy entries between groups both within and 
between files.  

To rename or delete an entry, right-click the entry and select the desired option from the menu that appears. 

To create a new group within a file or group, right-click the location where the new group is to reside and select 
"Create Subgroup."

To copy an entry, simply select it and drag it to the desired location.

Labeling
--------
To add a label to an existing label dataset, hold down a letter key and click on the plot.  A simple label with the name of the key pressed will be added to the plot at the location of the cursor on the time axis.  To label an interval, hold down shift and the letter key, click on the plot at the start time of the label, and then click again at the stop time.  You can also create an interval label corresponding the current view range by holding down a letter key and then pressing the space bar. 

To add a label dataset, select the entry where you want the label to be added, and press the "Add Label" button on the main toolbar. 

To delete a label, double click on the labels you want to delete and then press the "Delete Selected Label" button on the toolbar.


Exporting data
--------------
*Whole Datasets*
The "Export Checked Data" tool allows you to export the checked datasets as .wav or .csv files. 

*Selection from dataset*
To export a portion of a dataset, plot plot it as a oscillogram or spectrogram, and then double click on the plot. A line will appear on the plot. Click and drag the line to create a shaded region on the plot, and adjust the edges of the region to the selection you want to export. Then click "Export Selection" on the main toolbar.

Changing the position of the panels
------------------------------------
You can change the relative position of the four panels (Tree, Attributes, Settings, Data), by clicking on and dragging the purple bars containing the panel titles.
