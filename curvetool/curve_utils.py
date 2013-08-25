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

# Third Part
import maya.cmds as cmds
import maya.mel as mel

#---------------------------------------------------------------- FUNCTIONS ---

def serializeCurves(nurbs_curves):
    ''' 
    Return an list of MEL setAttr commands that will create the shape defined
    by 'nurbs_curves' when executed. Each command has a '%s' string formatting
    token that must be formatted with the name of the shape object when run.
    
    ARGUMENTS:
        nurbs_curves - [list] of nurbsCurves Maya objects
    
    RETURNS: [list] of MEL commands
    '''
    
    if not isinstance(nurbs_curves, list):
        raise TypeError("nurbs_curves must be a list of nurbsCurve objects")
    
    for crv in nurbs_curves:
        if not cmds.objectType(crv, isType="nurbsCurve"):
            raise TypeError("nurbs_curves must be a list of nurbsCurve objects")
        
    result = []
    
    for crv in nurbs_curves:
        result.append(serializeCurve(crv))
        
    return result

def serializeCurve(crv):
    '''
    Return a MEL setAttr command that will create the shape defined by 'crv'
    when executed. This command has a '%s' string formatting token that must be
    formatted with the name of the shape object when run.
    
    ARGUMENTS:
        crv - [str] a nurbsCurve Maya object
        
    RETURNS: [str] a MEL command
    '''
    
    if not cmds.objectType(crv, isType="nurbsCurve"):
        raise TypeError("crv must be a nurbsCurve object")
        
    cmd = []
    
    crv_info = cmds.createNode('curveInfo', ss=True)
    cmds.connectAttr("%s.worldSpace" % crv, "%s.inputCurve" % crv_info)
    knots = cmds.getAttr("%s.knots" % crv_info)[0]
    num_knots = len(knots)
    cmds.delete(crv_info)
                
    degree = cmds.getAttr("%s.degree" % crv)
    spans =  cmds.getAttr("%s.spans" % crv)
    form =   cmds.getAttr("%s.form" % crv)
    
    num_cvs = degree + spans
    cvs = []
    
    for i in range(spans):
        cv = cmds.xform("%s.cv[%s]" % (crv, i), q=True, os=True, t=True)
        cvs.append(cv)
        
    for i in range(degree):
        cvs.append(cvs[i])
        
    cmd.append('setAttr "%s.cc" - type "nurbsCurve"')
    cmd.append('%s %s %s no 3' % (degree, spans, form))
    cmd.append('%s' % num_knots)
    
    for k in knots:
        cmd.append('%s' % int(k))
        
    cmd.append('%s' % num_cvs)
    
    for cv in cvs:
        for c in cv:
            cmd.append(str(c)) 
    
    return ' '.join(cmd)