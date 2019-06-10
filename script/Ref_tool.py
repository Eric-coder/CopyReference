# -*- coding:utf-8 -*-
import maya.cmds as cmds
import pymel.core as pm
import os
import shutil
import traceback
try:
    from PySide2 import QtWidgets
    from PySide2 import QtCore
    from PySide2 import QtGui
except ImportError:
    from PySide import QtGui as QtWidgets
    from PySide import QtCore
    from PySide import QtGui
    
To_Copy_Path = "D:/RF_Copy"

def handleError(func):
    def handle(*args,**kwargs):
        try:
            return func(*args,**kwargs)
        except:
            title = 'error'
            content = traceback.format_exc()
            QtWidgets.QMessageBox(QtWidgets.QMessageBox.Critical,title,content).exec_()
    return handle
    
class Window(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(Window,self).__init__(parent)
        self.resize(300,100)
        self.label = QtWidgets.QLabel(u'复制到的路径：(默认 D:/RF_Copy)')
        self.to_path = QtWidgets.QLineEdit("")
        self.file_but = QtWidgets.QPushButton("...")
        self.copy_but = QtWidgets.QPushButton(u"复制RF") 
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.label,0,0)
        layout.addWidget(self.to_path,1,0)
        layout.addWidget(self.file_but,1,1)
        v = QtWidgets.QHBoxLayout()
        v.addStretch()
        v.addWidget(self.copy_but)
        v.addStretch()
        layout.addLayout(v,3,0,3,1)
     
        self.setLayout(layout)
        self.copy_but.clicked.connect(self.copy_rf)
        self.file_but.clicked.connect(self.out)

    def out(self):     
        s = QtWidgets.QFileDialog.getExistingDirectory(self, "Open file dialog", "D:/")
        self.to_path.setText(s)
        
        
    def combinePath(self,filelist):
        result = []
        for j in filelist:
            fullName = os.path.splitext(j)[0]
            ext = os.path.splitext(j)[-1]
            if '{' in ext:
                ext = ext.split('{')[0]
                j = fullName+ext
            result.append(j)
        # result = list(set(result))
        return result
        
    @handleError    
    def copy_rf(self):
        rf_list = cmds.ls(rf=1)
        resouce = []  # 存储所有RF原来的路径
        nameSP = [] # 存储所有RF的命名空间
        newRF_path = [] #存储所有RF的新路径
        newMA_path = [] #存储所有材质的新路径
        for i in rf_list:
            resouce.append(cmds.referenceQuery(i, filename=True))#获取源场景的文件路径
            nameSP.append(cmds.referenceQuery(i, namespace=True))#获取参考文件的命名空间
        resouce = self.combinePath(resouce)
        for j in resouce:
            par_file = os.path.dirname(j)#获取ref的文件夹目录           
            print par_file
            
            if self.to_path.text() == "": 
                newfile = To_Copy_Path+os.path.splitdrive(par_file)[1]
            else:
                newfile = self.to_path.text()+os.path.splitdrive(par_file)[1]
            if not os.path.exists(newfile):
                os.makedirs(newfile)
            else:
                pass  
                
            to_RF = newfile + "/" + os.path.split(j)[1]
            newRF_path.append(to_RF)
            
            if os.path.exists(to_RF):#用来判断现有的新路径的ref是否存在以及改变
                continue 
                #new = os.path.getsize(j)
                #old = os.path.getsize(to_RF)
                
                # 比较大小，如果大小不一样，说明改动过，需要重命名来复制
                #if new != old:  
                #    to_RF = self.rename(to_RF)
                #    newRF_path.append(to_RF)
            shutil.copy2(j, to_RF)  #复制ref 
            
        old_rf_tex = self.copy_ma()# [u'D:/liuzhiwei/shinei_text/sourceimages/hdr_non_blured.hdr']  贴图位置
        
        rf_tex = []    
        for i in old_rf_tex:
            if i != '':
                rf_tex.append(i)
        for j in rf_tex:
            par_file = os.path.dirname(j)
            if self.to_path.text() == "": 
                newfile = To_Copy_Path+os.path.splitdrive(par_file)[1]
            else:
                newfile = self.to_path.text()+os.path.splitdrive(par_file)[1]
            if not os.path.exists(newfile):
                os.makedirs(newfile)
            else:
                pass  
            to_MA = newfile + "/" + os.path.split(j)[1]
            newMA_path.append(to_MA)
            try:#如果贴图路径错误则忽略此次复制
                shutil.copy2(j, to_MA)
            except:
                print ('%s %s'%('No',to_MA))

        # 替换原来的RF
        
        for i in range(len(nameSP)):
            for j in range(len(newRF_path)):
                if i == j:
                    # print nameSP[i][1:], newRF_path[j]
                    self.Replace_Rf(newRF_path[j], nameSP[i][1:])
        # 替换原来的MA
        self.Replace_MA()#贴图位置
        
        self.mergeFile()
        
    def mergeFile(self):
        '''
        将替换好的文件场景进行再次输出到移动的文件中
        '''
        if self.to_path.text() == "": 
            SavePath = "D:/RF_Copy"
            currentPath = cmds.file(loc=1,q=1)
            currentPath=currentPath.split(':')[1]
            Path = SavePath+os.path.splitdrive(currentPath)[1]
            makePath=os.path.dirname(Path)
            if not os.path.exists(makePath):
                os.makedirs(makePath)    
            cmds.file(rename=Path)
            cmds.file(save=1,type='mayaBinary')
        else:
            SavePath=self.to_path.text()
            currentPath = cmds.file(loc=1,q=1)
            currentPath=currentPath.split(':')[1]
            Path = SavePath+os.path.splitdrive(currentPath)[1]
            makePath=os.path.dirname(Path)
            if not os.path.exists(makePath):
                os.makedirs(makePath)  
            cmds.file(rename=Path)
            cmds.file(save=1,type='mayaBinary')    
        qtm=QtWidgets.QMessageBox
        msg_box = qtm(qtm.Information,u'提示!',u'复制成功!',qtm.Yes)
        msg_box.exec_()
        
    def copy_ma(self):
        '''
        找有相同命名空间的材质
        '''
        all_tex = cmds.ls(tex=1)
        temp = []
        for j in all_tex:
            if cmds.objExists(j+".fileTextureName"):
                temp.append(cmds.getAttr(j+".fileTextureName"))
                    # else:   
        return temp
        
    def rename(self,path):
        '''
        return: 返回添加尾缀的Rference 
        例如：源文件下有"a.mb"文件，则返回"a(1).mb"文件
        '''      
        if os.path.exists(path):
            old = os.path.basename(path).split(".")[0]
            temp = []
            for dirpath, dirnames, filenames in os.walk(os.path.dirname(path)):
                for file in filenames:
                    # print old, file[:len(old)]
                    if old == file[:len(old)]:
                        temp.append(file)
            temp.sort()
            new = os.path.dirname(path)+"/"+old+"(%s)"%(len(temp))+"."+os.path.basename(path).split(".")[-1]             
        else:
            old = os.path.basename(path).split(".")[0]
            new = os.path.dirname(path)+"/"+old+"(%s)"%(str(1))+"."+os.path.basename(path).split(".")[-1]        
        return new
        
    def Replace_Rf(self, newpath, name_space=''):
        '''
        name_space: RF的命名空间
        newpath: 复制后的新路径
        '''
        FR = pm.FileReference(namespace = name_space)
        current_path = FR.path
        FR.replaceWith(newpath)
        
    def Replace_MA(self):
        temp = pm.ls(tex=1)
        all_tex = []
        for j in temp:
            if cmds.objExists(j+".fileTextureName"):
                all_tex.append(j)                   
        for j in all_tex:
            old = cmds.getAttr(j+".fileTextureName")
            if self.to_path.text() == "": 
                 new = To_Copy_Path+old[2:]
            else:
                 new = self.to_path.text()+old[2:]
            cmds.setAttr(j+".fileTextureName",new,type='string')
if __name__ == "__main__":
    app=QtWidgets.QApplication.instance() # checks if QApplication already exists 
    if not app: # create QApplication if it doesnt exist 
        app = QtWidgets.QApplication(sys.argv)
    win= Window()
    win.show()
    app.exec_()  

    
