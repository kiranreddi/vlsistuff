#! /usr/bin/python

WID,HEI = 1200,600

import os,sys,string,types,time

from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

import thread
import re

import oglGeoms
import dbase
import renders

import helpString 
from dumpFormats import connectivityClass
import drawVectorText

import cmd  
class cmdxClass(cmd.Cmd):
    def do_quit(self,aaa):
        print 'thanks and see you again'
        Glbs.finished=True
        sys.exit()
        return True 
    def emptyline(self):
        print 'emptyline'
        return False
    def default(self,Txt):
        wrds = string.split(Txt)
        if len(wrds)>0:
            use_command_wrds(wrds)
            CommandsHistory.append(Txt)
        return False



class GlobalsClass:
    def __init__(self):
        self.reset()

    def reset(self):
        self.history=[]
        self.Banner='iDraw: greenblat@mac.com +972-54-4927322'
        self.finished=False
        self.INIT = (WID,HEI)
        self.width=self.INIT[0]
        self.height=self.INIT[1]
        self.panelOffset=20
        self.graphicsChanged = True
        self.details={}
        self.pictures={}
        self.contexts={}
        self.adding_queue=[]
        self.params_queue=[]
        self.paramName='name'
        self.wireNumName=0
        self.set_context('backgroundColor','white')
        self.associated_dir={}
        self.useVectorText=True
        self.useShyParams=True
        self.fontShrink = 0.8
        self.pleaseExit=False
        self.listed={}
        self.lastKeys=[]
        self.loadStack=[]
        self.wratio = 1.0
        self.hratio = 1.0

    def wireName(self):
        self.wireNumName += 1
        return 'wire%d'%self.wireNumName

    def get_context(self,Param,Default=None):
        if Param in self.contexts:
            return self.contexts[Param]
        if (Default!=None):
            self.set_context(Param,Default)
            return Default
    
    def set_context(self,Param,Value):
        self.contexts[Param]=Value
        if (Param=='matrix'):
            Imatrix = matrix_inverse(Value)
            self.set_context('imatrix',Imatrix)
            recompute_proximity()
    def unset_context(Param):
        self.contexts.pop(Param)
    

    def try_load_picture(self,Pic):
        if Pic in self.pictures:
            return
        Dirs = self.get_context('pics_lib')
        if type(Dirs)==types.ListType:
            for Dir in Dirs:
                Fname = '%s/%s.zpic'%(Dir,Pic)
                if os.path.exists(Fname):
                    dbase.load_dbase_file(Fname)
                    return True
        elif type(Dirs)==types.StringType:
            Fname = '%s/%s.zpic'%(Dirs,Pic)
            if os.path.exists(Fname):
                dbase.load_dbase_file(Fname)
                return True
        return False

    def loadable_pictures(self):                
        Dirs = self.get_context('pics_lib')
        Res = []
        if type(Dirs)==types.ListType:
            for Dir in Dirs:
                LL = os.listdir(Dir)
                for Fname in LL:
                    if '.zpic' in Fname:
                        Cell = Fname[:-5]
                        if Cell not in self.pictures:
                            Res.append(Cell)
        elif type(Dirs)==types.StringType:
            LL = os.listdir(Dirs)
            for Fname in LL:
                if '.zpic' in Fname:
                    Cell = Fname[:-5]
                    if Cell not in self.pictures:
                        Res.append(Cell)
        return Res 


Glbs = GlobalsClass()
dbase.Glbs = Glbs
oglGeoms.Glbs = Glbs
renders.Glbs = Glbs
drawVectorText.Glbs=Glbs

def main():
#    global CmdFile
#    CmdFile = open_command_file()
    dbase.init()
    load_init_file()
    was_minus=False
    ind=1
    while ind < len(sys.argv):
        Fname = sys.argv[ind]
        if Fname[0]=='-':
            was_minus=True
        if not was_minus:
            if os.path.exists(Fname):
                dbase.load_dbase_file(Fname)
            else:
                dbase.log_error('file "%s" cant be read'%Fname)
            ind += 1
        else:
            if Fname=='-do':
                ind += 1
                What = sys.argv[ind]
                use_command_wrds([What])
                ind += 1
            else:
                dbase.log_error('"%s" not known'%sys.argv[ind])
                ind += 1
            
            
    Thr = thread.start_new_thread(execute_terminal_commands,())
    work()
    

def load_init_file():
    found=False
    homepath = '%s/.pyzdraw'%(os.path.expanduser('~'))
    herepath = '%s/.pyzdraw'%(os.path.abspath('.'))
    print 'home %s'%homepath
    print 'here %s'%herepath
    if os.path.exists(homepath):
        read_init_file(homepath)
        dbase.log_info('home dir .pyzdraw loaded')
        found=True
    if os.path.exists(herepath):
        read_init_file(herepath)
        dbase.log_info('pwd dir .pyzdraw loaded')
        found=True
    if not found:
        dbase.log_warning('no .pyzdraw loaded')


def doesntHaveExtension(Txt):
    ww = string.split(Txt,'/')
    Fname = ww[-1]
    return not (endsWith(Fname,'.zdraw')or endsWith(Fname,'.zpic'))
def figure_out_the_file(Fname):
    if os.path.exists(Fname):
        return Fname
    if doesntHaveExtension(Fname):
        if os.path.exists(Fname+'.zdraw'):
            return  Fname+'.zdraw'
        if os.path.exists(Fname+'.zpic'):
            return Fname+'.zpic'
    if Fname in Glbs.listed:
        Fname = Glbs.listed[Fname]+'/'+Fname
        return Fname
    if Fname+'.zdraw' in Glbs.listed:
        Fname = Glbs.listed[Fname+'.zdraw']+'/'+Fname+'.zdraw'
        return Fname
    if Fname+'.zpic' in Glbs.listed:
        Fname = Glbs.listed[Fname+'.zpic']+'/'+Fname+'.zpic'
        return Fname
    return False

def read_init_file(Fname):
    File = open(Fname)
    while 1:
        line = File.readline()
        if (len(line)==0):
            return
        wrds = string.split(line)
        if (len(wrds)>0)and(wrds[0]=='load'):
            Fname = figure_out_the_file(wrds[0])
            if not Fname:
                dbase.log_error('file "%s" cant be read'%Fname)
            else:
                dbase.load_dbase_file(Fname)
        elif (len(wrds)==2):
            Param = wrds[0]
            Value=wrds[1]
            dbase.log_info('read_init_file set context "%s" "%s"'%(Param,Value))
            if (',') in Value:
                W1 = string.split(Value,',')
                ll = []
                for X in W1:
                    ll.append(makenum(X))
                dbase.set_context(Param,ll)
            elif (Value[0] in '0123456789'):
                dbase.set_context(Param,makenum(Value))
            else:
                dbase.set_context(Param,Value)
        elif(len(wrds)>0):
            dbase.log_warning('read_init_file got "%s" . not valid.'%(string.join(wrds,' ')))
                
def makenum(Txt):
    try:
        if '.' in Txt:
            return float(Txt)
        return int(Txt)
    except:
        return Txt




def work():
    glutInit()
    glutInitWindowSize(Glbs.INIT[0],Glbs.INIT[1])
    glutCreateWindow("oglDraw")
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB)
    glutDisplayFunc(on_draw)
#    glutIdleFunc(on_draw)
    glutMouseFunc(on_mouse_press)
    glutMotionFunc(on_mouse_move)
    glutKeyboardFunc(on_key_press)
    glutSpecialFunc(on_special_press)
    glutTimerFunc(5,timerFun,333)
    glutReshapeFunc(on_resize)
    glutMainLoop()
#    if CmdFile:
#        CmdFile.close()


def on_mouse_move(X,Y):
    dbase.use_mousemove(X,Y)
    Glbs.graphicsChanged=True
#    on_draw()

def on_resize(width,height):
    Glbs.width=width
    Glbs.height=height
    Glbs.wratio = 1.0 * width / Glbs.INIT[0]
    Glbs.hratio = 1.0 * height / 480.0

    Glbs.set_context('width',width)
    Glbs.set_context('height',height)
    Glbs.graphicsChanged=True
#    on_draw()

def update_graphics():
    glViewport(0,0,Glbs.width,Glbs.height)
    if Glbs.finished:
        print 'graphics bye bye' 
        sys.exit()
    if not Glbs.graphicsChanged:
        return
    Glbs.graphicsChanged=False
    Glbs.longest=0



def initFun():
    glClear(GL_COLOR_BUFFER_BIT)
    Color = Glbs.get_context('backgroundColor')
    RGB = oglGeoms.oglcolor(Color)
    glClearColor(RGB[0],RGB[1],RGB[2],1.0)
    glColor3f(0.0,0.0, 0.0)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0.0,Glbs.width,0.0,Glbs.height)



def on_draw():
    if Glbs.finished:
        print 'graphics bye bye'
        sys.exit()
    if not Glbs.graphicsChanged:
        return
    update_graphics()
    initFun()
#    oglGeoms.draw_frect(4,4,Glbs.width-4,Glbs.height-4,'yellow')
    WW,HH = int(Glbs.width*Glbs.wratio),int(Glbs.height*Glbs.hratio)
#    oglGeoms.draw_label(Glbs.get_context('banner',Glbs.Banner),(WW+Glbs.panelOffset)/2,HH-15,'magenta','center',13)
#    oglGeoms.draw_horizontal(0,WW,HH-30,'magenta')
    oglGeoms.draw_label(Glbs.get_context('banner',Glbs.Banner),10,15,'magenta','center',13)
    oglGeoms.draw_horizontal(0,WW,20,'magenta')
    oglGeoms.oglcolor('black')
    glutSolidSphere(200.0,20,30)
    dbase.pdraw_current()
    glFlush()




CommandsHistory=[]


def was_execute_terminal_commands():
    print '>>0>>>>>'
    Glbs.IntrLoop = cmdxClass()
    print '>>1>>>>>'
    Glbs.IntrLoop.prompt='?:'
    print '>>2>>>>>'
    Glbs.IntrLoop.cmdloop('hello')
    print '>>3>>>>>'






def execute_terminal_commands():
    while 1:
        Txt = raw_input('?:')
        wrds = string.split(Txt)
        if len(wrds)>0:
            use_command_wrds(wrds)
            CommandsHistory.append(Txt)

def do_command_line():
    Txt = raw_input('?:')
    wrds = string.split(Txt)
    if len(wrds)==0:
        return
    use_command_wrds(wrds)
    do_command_line()

def use_command_wrds(wrds):
#    if (CmdFile and (len(wrds)!=0)):
#        CmdFile.write('%s\n'%string.join(wrds,' '))
    if len(wrds)==0:
        return
    if wrds[0]=='history':
        for LL in Glbs.history:
            print LL
        return
    else:
        Glbs.history.append(string.join(wrds,' '))
    Root=Glbs.get_context('root')
    if wrds[0] in ['quit','exit']:
        Glbs.details[Root].touched('Q')
        Glbs.pleaseExit=True
        Glbs.finished=True
        sys.exit()
    elif wrds[0]=='save':
        if Root in Glbs.associated_dir:
            Fname = '%s/%s.zdraw'%(Glbs.associated_dir[Root],Root)
        else:
            Fname = '%s.zdraw'%Root
        dbase.log_info('saving %s to %s file'%(Root,Fname))
        File = open(Fname,'w')
        Glbs.details[Root].save(File)
        File.close()
        Glbs.details[Root].touched(False)
    elif wrds[0]=='change':
        List = Glbs.details.keys()
        List.sort()
        if len(wrds)==1:
            dbase.log_info('available schematics: %s'%string.join(List,' '))
        elif(wrds[1] in List) :
            Glbs.set_context('root',wrds[1]) 
            Glbs.graphicsChanged=True
        else:
            print '"%s" is not loaded. use new to open new drawing'%wrds[1]
    elif wrds[0]=='delete':
        if (Root!='opening'):
             Glbs.details.pop(Root)
             Glbs.set_context('root','opening') 
             Glbs.graphicsChanged=True
    elif wrds[0] == 'V':
        Glbs.useVectorText = not Glbs.useVectorText;
        Glbs.graphicsChanged=True
    elif wrds[0] in ['plot','print']:
        dbase.postscript_current()
    elif 'new' in wrds[0]:
        Root = wrds[1]
        Glbs.set_context('root',Root)
        Glbs.details[Root] = dbase.DetailClass(Root)
        Glbs.graphicsChanged=True
    elif 'load' in wrds[0]:
        if len(wrds)==1:
            print 'loaded schematics:  %s'%str(Glbs.details.keys())
            print 'loaded pictures:  %s'%str(Glbs.pictures.keys())
        else:
            load_schematics(wrds[1])
                    
    elif 'add' in wrds[0]:
        Glbs.adding_queue.extend(wrds[1:])
    elif 'name' in wrds[0]:
        Glbs.paramName='name'
        Glbs.params_queue.extend(wrds[1:])
    elif 'param' in wrds[0]:
        Glbs.paramName=wrds[1]
        Glbs.params_queue.extend(wrds[2:])
    elif 'spice' in wrds[0]:
        Root = Glbs.get_context('root')
        Fname = '%s.cir'%(Root)
        File = open(Fname,'w')
        dbase.log_info('writing spice file "%s.cir"'%Root)
        GG = connectivityClass(Glbs,Root)
        GG.dumpSpice(File)
        File.close()
    elif ('dump' in wrds[0])or('verilog' in wrds[0]):
        if len(wrds)==1:
            Root = Glbs.get_context('root')
            Fname = '%s.v'%(Root)
            File = open(Fname,'w')
            dbase.log_info('writing verilog file "%s.v"'%Root)
            GG = connectivityClass(Glbs,Root)
            GG.dumpVerilog(File)
            File.close()
        elif len(wrds)==2:
            Fname = wrds[1]
            File = open(Fname,'w')
            Root = Glbs.get_context('root')
            GG = connectivityClass(Glbs,Root)
            GG.dumpVerilog(File)
            File.close()
        elif len(wrds)==3:
            Fname = wrds[2]
            File = open(Fname,'w')
            if wrds[1]=='*':
                for Name in Glbs.details:
                    GG = connectivityClass(Glbs,Root)
                    GG.dumpVerilog(File)
            else:
                GG = connectivityClass(Glbs,wrds[1])
                GG.dumpVerilog(File)
            File.close()

    elif ('sys' == wrds[0]):
        os.system('%s\n'%(string.join(wrds[1:],' ')))
    elif 'ls' in wrds[0]:
        if len(wrds)>1:
            Dir = wrds[1]
        else:
            Dir = '.'
        if not os.path.exists(Dir):
            print 'no such directory "%s"'%Dir
            return

        LL = os.listdir(Dir)
        L1 = []
        L2 = []
        for Fname in LL:
            if ('.zdraw' in Fname):
                L1.append(Fname)
            elif ('.zpic' in Fname):
                L2.append(Fname)
        for Cell in L1+L2:
            Glbs.listed[Cell] = Dir

        print 'schematics in "%s"  %s'%(Dir,L1)
        print 'pictures   in "%s"  %s'%(Dir,L2)
                
    elif (len(wrds)==3)and(wrds[1]=='='):
        Glbs.set_context(wrds[0],makenum(wrds[2]))
    elif(wrds[0]=='variables'):
        for Key in Glbs.contexts:
            print Key,Glbs.contexts[Key]
    elif 'help' in wrds[0]:
        if len(wrds)==1:
            print helpString.helpString
        else:
            List = string.split(helpString.helpString,'\n')
            for Str in List:
                if wrds[1] in Str:
                    print Str
    elif matchesCommand(wrds[0]):
        Comm = matchesCommand(wrds[0])
        wrds[0]=Comm
        use_command_wrds(wrds)
    else:
        print 'dont know to %s'%wrds

def load_schematics(newRoot):
    List = Glbs.details.keys()
    if newRoot in List:
        Glbs.set_context('root',newRoot) 
        Glbs.graphicsChanged=True
    else:
        Fname = figure_out_the_file(newRoot)
        if Fname:
            dbase.load_dbase_file(Fname)
        else:
            dbase.log_error('file "%s" cant be read'%newRoot)
            return
            


from renders import screen2schem
dbase.load_schematics = load_schematics

def on_mouse_press(button, modifiers,x,y):
    Glbs.Vertical=(x,y)
    Glbs.Msx=x
    Glbs.Msy=y
    Glbs.graphicsChanged=True
    dbase.use_mousedown(x,y)
#    on_draw()

def on_key_press(Chr,x,y):
#    if (Chr=='Q'):   # Q key
#        sys.exit()
    if (Chr=='h'):
        dbase.log_info(helpString.helpString)
    else:
        dbase.use_keystroke(Chr,x,y)
#    on_draw()

def on_special_press(Chr,x,y):
    dbase.use_keystroke(Chr,x,y)

def timerFun(Value):
    if (Glbs.finished or Glbs.pleaseExit):
        sys.exit()
    if Glbs.graphicsChanged:
        on_draw()
    glutTimerFunc(100,timerFun,333)
    



def open_command_file():
    Cnt = 1
    while True:
        Fname = 'cmd.%d'%Cnt
        if not os.path.exists(Fname):
            try:
                return open(Fname,'w')
            except:
                print 'failed to open command trace file  (%s)'%Fname
                return 0
        Cnt +=1


def printScreen():
    print 'print screen - not yet.'


ValidCommandsTxt = ''' add param dump load new delete print save change history help quit exit variables
    verilog spice plot
'''


ValidCommands = string.split(ValidCommandsTxt)
ValidCommands.sort()

def matchesCommand(Wrd0):
    res=[]
    for Comm in ValidCommands:
        if startsTheSame(Wrd0,Comm):
            res.append(Comm)
    if len(res)==1:
        return res[0]
    if len(res)>1:
        print 'ambigious command %s matches %s'%(Wrd0,res)
    elif len(res)==0:
        print 'valid cmds: %s'%ValidCommands

    return False


def startsTheSame(Wrd0,Comm):
    Len = len(Wrd0)
    if Len >len(Comm):
        return False
    Part = Comm[:Len]
    return Part==Wrd0


def endsWith(Fname,With):
    if With not in Fname:
        return False
    ind = Fname.index(With)
    return len(Fname)==(ind+len(With))



main()



