from cx_Freeze import setup, Executable
import glob
import shutil
import subprocess
import os
import sys
import time
build_dir = 'build/arfview.app/Contents/MacOS' 

def listfiles(directory):
    files=[os.path.join(dir, f) for dir,_,fname in os.walk(directory) for f in fname]    
    return files

def copy_dependencies(directory, dest=None):
    if not dest: dest = directory
    files = listfiles(directory)
    for f in files:
        otool_out = subprocess.check_output('otool -L %s'%(f), shell=True).split()
        dependencies = [d for d in otool_out if os.path.isfile(d)]
        subprocess.call('chmod a+rwx %s' %f, shell=True)
        for d in dependencies:
            rel_path = d.split('/')[-1]
            if not os.path.isfile(os.path.join(dest, rel_path)):
                shutil.copy(d, dest)
            try:
                depth=f.count('/')-directory.count('/')
                if directory[-1] != '/': depth-=1
                from_loader='../'*depth
                subprocess.check_output('install_name_tool -change "%s" "@loader_path/%s%s" %s'%(d,from_loader,rel_path,f), shell=True)                   

            except:
                import pdb;pdb.set_trace()



def link_dependencies(directory):
    subprocess.check_output('otool -L %s'%(f), shell=True).split()
    

def test():
    copy_dependencies(build_dir)

def main():

    buildOptions = dict(packages = ['PySide','PySide.QtCore','PySide.QtGui','atexit',
                                    'numpy','libtfr','arf', 'scipy',
                                    'scipy.signal', 'scipy.interpolate', 'sys', 'os',
                                    'pyqtgraph','tempfile', 'signal', 'arfx', 'ewave'],
                        excludes = ["Tkinter", "Tkconstants", "tcl"],
                        copy_dependent_files=True)
    base = 'Win32GUI' if sys.platform=='win32' else None


    executables = [
        Executable('../arfview/mainwin.py', base=base, targetName='arfview')
    ]

    mac_options = dict(bundle_name = 'arfview')
    try:
        setup(name='arfview',
              version = '1.0',
              description = 't',
              options = dict(build_exe = buildOptions,
                             bdist_mac = mac_options),
              executables = executables)
    finally:
        subprocess.call('cp -r /Library/Python/2.7/site-packages/h5py %s' %build_dir, 
                        shell=True)    
        copy_dependencies(build_dir)


if __name__=='__main__':
    main()
