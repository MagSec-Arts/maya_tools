#------------------------------------------------------------------- HEADER ---
# Title: 
# Descr: 
#
# Author:  Ryan Porter
# Date:    2013.08.13   
# Version: 0.1
#
#------------------------------------------------------------------------------

#------------------------------------------------------------------ IMPORTS ---
# Built-in
import os.path
import traceback

# Third Party
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya

import maya.cmds as cmds
import maya.mel as mel

# Custom
import curve_utils

#------------------------------------------------------------------ GLOBALS ---
global CURVE_TOOL_UI
global CURVE_FILE_FORMAT
CURVE_FILE_EXT = ".crv"

#------------------------------------------------------------------ CLASSES ---
class CurveToolUI(object):
    win_name = "CurveToolUI"
    win_title = "Curve Tools UI v0.1"
    
    def __init__(self):
        self.preview_curve = None
        
        self.__preCreateUI()
        self.__createUI()
        self.__postCreateUI()
    
    def __preCreateUI(self):
        self.grp = cmds.createNode('transform', name="CURVE_TOOLS_NULL", ss=True)
        self.ns = 'curve_tools'
        
        try:
            self.ns = cmds.namespace(add=self.ns)
        except:
            pass
        
        cmds.lockNode(self.grp, l=True)
        
        tmp = cmds.ls(sl=True)
        
        self.viewport_cam = cmds.camera(
            name="Curve_Tools_CAM",
            p=[-15, 15, 21],
            wci=[0,0,0]
        )[0]
        
        cmds.parent(self.viewport_cam, self.grp)
                
        if tmp:
            cmds.select(tmp)
        else:
            cmds.select(clear=True)
            
    def __createUI(self):
        self.win = CurveToolUI.win_name
        
        if not cmds.uiTemplate('CurveToolsUITemplate', exists=True):
            cmds.uiTemplate('CurveToolsUITemplate')
            
        if cmds.window(self.win, exists=True):
            cmds.deleteUI(self.win)
            
        self.win = cmds.window(self.win, t=CurveToolUI.win_title, 
                               mb=True, w=656, h=385)
        
        self.main_menu = cmds.menu(label="Menu", parent=self.win)
        #cmds.menuItem(label="Refresh List", c=self.handleRefreshMenu)
        
        self.help_menu = cmds.menu(label="Help", parent=self.win)
        #cmds.menuItem(label="Help", c=self.handleHelpMenu)
        
        self.mainLayout = cmds.rowColumnLayout(nc=2, cw=[(1, 292), (2, 360)])
        self.leftLayout = cmds.rowColumnLayout(nr=3, parent=self.mainLayout,
                                               rh=[(1, 48), (2, 256), (3, 48)])
        self.topRow = cmds.rowColumnLayout(nc=3, parent=self.leftLayout)
        
        self.shapesList = cmds.textScrollList(parent=self.leftLayout, nr=24)
        
        self.btmRow = cmds.rowColumnLayout(nc=3, parent=self.leftLayout, w=128)
        
        self.createBtn =  cmds.button(l="Create",  w=96, h=48, parent=self.topRow)
        self.replaceBtn = cmds.button(l="Replace", w=96, h=48, parent=self.topRow)
        self.appendBtn =  cmds.button(l="Append",  w=96, h=48, parent=self.topRow)

        self.saveBtn = cmds.button(l="Save", w=96, h=48, parent=self.btmRow)
        self.overwriteBtn = cmds.button(l="Overwrite", w=96, h=48, parent=self.btmRow)
        self.deleteBtn = cmds.button(l="Delete", w=96, h=48, parent=self.btmRow)
        
        self.paneLayout = cmds.paneLayout(parent=self.mainLayout)            
        self.viewport = cmds.modelPanel(mbv=False, 
                                        parent=self.paneLayout)
        
        #------------------------------------------- install click handlers ---
        cmds.button(self.createBtn,  e=True, c=self.__handleCreateClick)
        cmds.button(self.replaceBtn, e=True, c=self.__handleReplaceClick)
        cmds.button(self.appendBtn,  e=True, c=self.__handleAppendClick)
        
        cmds.button(self.saveBtn,  e=True, c=self.__handleSaveClick)
        cmds.button(self.overwriteBtn, e=True, c=self.__handleOverwriteClick)
        cmds.button(self.deleteBtn,  e=True, c=self.__handleDeleteClick)   
        
        cmds.textScrollList(self.shapesList, e=True, 
                            sc=self.__handleShapeListSelection)
        
        #----------------------------------------- setup UiDeleted callback ---
        self.__uiCallback = OpenMayaUI.MUiMessage.addUiDeletedCallback(
            self.win, 
            self.__handleUIClosed
        )
        
        cmds.showWindow(self.win)
    
    def __postCreateUI(self):
        cmds.modelPanel(self.viewport, edit=True, cam=self.viewport_cam)
        cmds.modelEditor(self.viewport, edit=True, grid=False)

        self.__isolateSelectedInViewport()
        self.__refreshShapesList()
        
    def __handleUIClosed(self, *args):
        self.__isolateSelectedInViewport(0)
        
        if cmds.panel(self.viewport, exists=True):
            cmds.deleteUI(self.viewport, pnl=True)   
        
        cmds.lockNode(self.grp, l=False)
        cmds.delete(self.grp)
        
        try:
            cmds.namespace(rm=self.ns)
        except:
            mel.eval('''warning "Could not cleanup namespace '%s' when closing window"''' % self.ns)
        
        OpenMaya.MMessage.removeCallback(self.__uiCallback)
        
    #-------------------------------------------------------- GETTR METHODS ---
    def __get_selectedShape(self):
        result = None
        
        list_selection = cmds.textScrollList(self.shapesList, q=True, si=True)
        
        if list_selection:
            result = list_selection[0]
            
        return result
    
    #---------------------------------------------------- UTILITY FUNCTIONS ---
    def __isolateSelectedInViewport(self, enabled=1):
        tmp = cmds.ls(sl=True)
        
        if enabled:            
            if self.preview_curve is not None and cmds.objExists(self.preview_curve):
                cmds.select(self.preview_curve)
            else:
                cmds.select(clear=True)
            
        mel.eval('enableIsolateSelect %s %s' % (self.viewport, enabled))
        
        if enabled:
            if tmp:
                cmds.select(tmp)
            else:
                cmds.select(clear=True)
                
    def __refreshShapesList(self):
        cmds.textScrollList(self.shapesList, edit=True, ra=True)
        
        for shape in get_shapes():
            cmds.textScrollList(self.shapesList, edit=True, a=shape)
    
    #------------------------------------------------------- CLICK HANDLERS ---
    def __handleCreateClick(self, *args):
        selected_shape = self.__get_selectedShape()
        
        if selected_shape:
            createCurve(selected_shape)
        else:
            mel.eval('''warning "Select a shape from the list and try again."''')
    
    def __handleAppendClick(self, *args):
        selected_shape = self.__get_selectedShape()
        
        if selected_shape:
            appendCurve(selected_shape)
        else:
            mel.eval('''warning "Select a shape from the list and try again."''')
            
    def __handleReplaceClick(self, *args):
        selected_shape = self.__get_selectedShape()
        
        if selected_shape:
            replaceCurve(selected_shape)
        else:
            mel.eval('''warning "Select a shape from the list and try again."''')
            
    def __handleSaveClick(self, *args):
        result = saveCurve()
        
        if result is not None:
            self.__refreshShapesList()
    
    def __handleOverwriteClick(self, *args):
        selected_shape = self.__get_selectedShape()
        
        if selected_shape:
            result = overwriteCurve(selected_shape)
            
            if result is not None:
                cmds.textScrollList(self.shapesList, 
                                    edit=True, 
                                    si=selected_shape)
                                    
                self.__createPreviewShape()
        else:
            mel.eval('''warning "Select a shape from the list and try again."''')
                
    def __handleDeleteClick(self, *args):
        selected_shape = self.__get_selectedShape()
        
        if selected_shape:
            result = deleteCurve(selected_shape)
            
            if result:
                self.__refreshShapesList()
                self.__createPreviewShape()
        else:
            mel.eval('''warning "Select a shape from the list and try again."''')

    def __handleShapeListSelection(self, *args):
        self.__createPreviewShape()      
        
    def __createPreviewShape(self):
        selected_shape = self.__get_selectedShape()
        
        if selected_shape:
            if self.preview_curve is None or not cmds.objExists(self.preview_curve):
                self.preview_curve = createCurve(selected_shape, '%s:PREVIEW_CRV' % self.ns)
                
                cmds.parent(self.preview_curve, self.grp)
            else:
                replaceCurve(selected_shape, [self.preview_curve])
        else:
            if cmds.objExists(self.preview_curve):
                cmds.delete(self.preview_curve)
                self.preview_curve = None
                
        self.__isolateSelectedInViewport()
        cam_shape = cmds.listRelatives(self.viewport_cam, shapes=True)[0]
        cmds.viewFit(cam_shape, namespace=':')
#---------------------------------------------------------------- FUNCTIONS ---    
#------------------------------------------------------------ GETTR METHODS ---
def __get_shapesDir():
    '''
    Return the path to the /curves folder in the user prefs directory. Create 
    the folder if it does not already exist.
    '''
    
    user_prefs_dir = cmds.internalVar(upd=True)
    
    shapes_dir = ''.join([user_prefs_dir, '/curves/'])
    
    if not os.path.isdir(shapes_dir):
        os.makedirs(shapes_dir)
    
    return shapes_dir

def __get_shapeName(file_):
    if not file.endswith(CURVE_FILE_EXT):
        raise Exception('%s is not a curve file.' % file_)

    result = ""
    
    filename = os.path.basename(file_)
    filename = filename.replace(CURVE_FILE_EXT, "")
    
    return result

def get_shapes():
    result = []
    
    shapes_dir = __get_shapesDir()
    
    for file_ in os.listdir(shapes_dir):
        filepath = ''.join([shapes_dir, file_])
        if os.path.isfile(filepath) and file_.endswith(CURVE_FILE_EXT):
            result.append(file_.replace(CURVE_FILE_EXT, ""))
            
    return result

def __get_shapeFile(shape, new_file=False):
    result = None
    
    shape_file = ''.join([__get_shapesDir(), shape, CURVE_FILE_EXT])

    if not new_file:
        try:
            __validate_shapeFile(shape_file)
            result = shape_file 
        except IOError:
            msg = "File '%s' does not exist for shape '%s'." % (shape_file, shape)
            mel.eval('''warning "%s"''' % msg)
    else:
        result = shape_file
        
    return result

def __get_selectedNurbsCurves():
    result = None
    
    scene_selection = cmds.ls(sl=True)
    
    for sel in scene_selection:
        shapes = cmds.listRelatives(sel, shapes=True)
        
        if shapes:
            for shape in shapes:
                if cmds.objectType(shape, isType="nurbsCurve"):
                    if result is None:
                        result = []
                        
                    result.append(shape)
        
        if result is not None:
            break
    
    return result

#----------------------------------------------------------- HELPER METHODS ---
def __validate_nurbsCurves(nurbs_curves):
    result = True
        
    if not isinstance(nurbs_curves, list):
        result = False
        mel.eval('warning "nurbs_curves must be a list of nurbsCurves."')
    else:
        for crv in nurbs_curves:
            if not cmds.objectType(crv, isType="nurbsCurve"):
                result = False
                mel.eval('warning "nurbs_curves must be a list of nurbsCurves."')
                break
        
    return result
   
def __validate_shapeFile(shape_file):
    if not os.path.isfile(shape_file):
        raise IOError("File does not exist %s" % shape_file)
    
def __confirmAction(title, msg):
    result = False
    
    confirm = cmds.confirmDialog(
        title=title, 
        message=msg, 
        button=['Yes','No'], 
        defaultButton='Yes', 
        cancelButton='No', 
        dismissString='No'
    )
    
    if confirm == 'Yes':
        result = True
        
    return result
     
def __promptUserInput(title, msg, defaultText=""):
    result = None
    
    prompt = cmds.promptDialog(
        title=title,
        message=msg,
        tx=defaultText,
        button=['OK', 'Cancel'],
        defaultButton='OK',
        cancelButton='Cancel',
        dismissString='Cancel'
    )
    
    if prompt == "OK":
        result = cmds.promptDialog(query=True, text=True)
        
        if result == "":
            result = __promptUserInput(title, msg, defaultText)
                
    return result

def __getMELCmds(shape_file):
    result = []
    
    try:
        with open(shape_file, 'r') as f:
            result = f.readlines()
    except IOError:
        msg = "An error occurred reading file '%s'." % shape_file +\
             "See script editor for details." 
        mel.eval('''warning "%s"''' % msg)
    
    return result

def __createCurves(parentObj, mel_cmds, shape):
    for i, mel_cmd in enumerate(mel_cmds, 1):
        try:
            crv = cmds.createNode('nurbsCurve',
                                  parent=parentObj, 
                                  name ="%sShape%s" % (parentObj, i),
                                  ss=True)
        except:
            traceback.print_exc()
            mel.eval('''warning "Encountered an error creating a nurbsCurve. Aborting."''')
            return
        
        try:
            mel.eval(mel_cmd % crv)
        except:
            print "# Bad command: %s" % mel_cmd
            msg = "An error occurred creating curve " +\
                  "%s of shape %s. " (i, shape) +\
                  "See script editor for details." % (i, shape)
            mel.eval('''warning "%s"''' % msg)
            cmds.delete(crv)

#--------------------------------------------------------------- PUBLIC API ---
def createCurve(shape, name=None):
    '''
    Create a new object with the nurbsCurves from 'shape' named 'name'. If name
    is None, prompt the user for a name
    '''
    result = None
        
    shape_file = __get_shapeFile(shape)
    
    if shape_file is not None:    
        if name is None:
            name = __promptUserInput('Curve Name',
                                     'Enter a name for the new curve',
                                     defaultText="newControl")
        
        if name is not None:  
            mel_cmds = __getMELCmds(shape_file)
            result = cmds.createNode('transform', name=name)
            __createCurves(result, mel_cmds, shape)
        
    if result is not None:
        cmds.select(result)
        
    return result

def appendCurve(shape, objects=None):
    '''
    Add the nurbsCurves from 'shape' to each object in objects (or the current 
    selection is objects i None)
    '''
    shape_file = __get_shapeFile(shape)
    
    if shape_file is not None:
        mel_cmds = __getMELCmds(shape_file)
        
        if objects is None:
            objects = cmds.ls(sl=True)
            
        if objects:
            for obj in objects:
                __createCurves(obj, mel_cmds, shape)
        else:
            mel.eval('''warning "Select at least one object and try again."''')

def replaceCurve(shape, objects=None):
    '''
    Replace the nurbsCurve shapes for each object in objects (or the current
    selection if objects is None) with the nurbsCurves from 'shape'. Only affect
    objects that already have nurbsCurve shapes.
    '''
    shape_file = __get_shapeFile(shape)
    
    if shape_file is not None:
        mel_cmds = __getMELCmds(shape_file)

        if objects is None:
            objects = cmds.ls(sl=True)
            
        objects_with_curves = []
        
        for obj in objects:
            shapes = cmds.listRelatives(obj, shapes=True)
            
            if shapes is not None:
                for s in shapes:
                    if cmds.objectType(s, isType="nurbsCurve"):
                        objects_with_curves.append(obj)
                        break

        if objects_with_curves:
            for obj in objects_with_curves:
                shapes = cmds.listRelatives(obj, shapes=True)
                nurbs_curves = []
                
                for s in shapes:
                    if cmds.objectType(s, isType="nurbsCurve"):
                        nurbs_curves.append(s)
                        
                cmds.delete(nurbs_curves)
                __createCurves(obj, mel_cmds, shape)
        else:
            mel.eval('''warning "Select at least one object with nurbsCurve shape nodes and try again."''')
            
def saveCurve(nurbs_curves=None, name=None):
    '''
    Serializes 'nurbs_curves' to MEL cmds and saves them to a file named 'name'
    and return the file path. If the user cancels the save or an error occurs,
    return None.
    
    If name is not given, the user will be prompted for the name. 
    '''
    result = None
    
    if nurbs_curves is None:
        nurbs_curves = __get_selectedNurbsCurves()
        
    if nurbs_curves is not None:
        if __validate_nurbsCurves(nurbs_curves):
            if name is None:
                name = __promptUserInput("Save Curve",
                                          "Enter a name for the shape file")
                
                if name is not None:
                    shape_file = __get_shapeFile(name, new_file=True)
                    mel_cmds = curve_utils.serializeCurves(nurbs_curves)
                    
                    try:
                        with open(shape_file, 'w') as f:
                            for cmd in mel_cmds:
                                f.write(cmd + "\n")
                            
                        result = shape_file
                    except IOError:
                        msg = "Encountered an error trying to save " +\
                              "shape '%s' to file '%s'" % (name, shape_file) +\
                              "See script editor for details."
                        mel.eval('''warning "%s."''' % msg)
    else:
        mel.eval('warning "Select a nurbsCurve and try again."')
                
    return result

def overwriteCurve(shape, nurbs_curves=None):
    '''
    Serializes 'nurbs_curves' to MEL cmds, save them over the selected shape and
    return the file path. If the user cancels the save or an error occurs,
    return None. 
    '''
    result = None
    
    if nurbs_curves is None:
        nurbs_curves = __get_selectedNurbsCurves()
        
    if nurbs_curves is not None:
        shape_file = __get_shapeFile(shape)
        
        if shape_file is not None:
            if __validate_nurbsCurves(nurbs_curves):
                mel_cmds = curve_utils.serializeCurves(nurbs_curves)
                
                try:
                    with open(shape_file, 'w') as f:
                        for cmd in mel_cmds:
                            f.write(cmd + "\n")
                    
                    result = shape_file
                except IOError:
                    msg = "Encountered an error trying to overwrite " +\
                          "file '%s'. See script editor for details." % shape_file
                    mel.eval('''warning "%s"''' % msg)
    else:
        mel.eval('warning "Select a nurbsCurve and try again."')
  
    return result

def deleteCurve(shape):
    '''Delete the file for 'shape' and return True if successful.'''
    result = False
    shape_file = __get_shapeFile(shape)
    
    if shape_file is not None:
        if __confirmAction("Delete Shape",
                           "Are you sure you want to delete '%s'?" % shape):
            
            
            try:
                os.remove(shape_file)
                result = True
            except Exception:
                traceback.print_exc()
                error_msg = "An error occurred trying to remove '%s'." % shape +\
                            "See script editor for details."
                mel.eval('''warning "%s"''' % error_msg)
            
    return result

def main():
    reload(curve_utils)
    CURVE_TOOL_UI = CurveToolUI()