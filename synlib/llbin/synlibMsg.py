#! /usr/bin/python


import os,sys,string,pickle
import traceback,logs

import msgsim2c

Cells = {}
Types = {}
class cellClass:
    def __init__(self,Name):
        self.Name=Name
        self.pins={}
        self.busses={}
        self.pairs={}
        self.ff=0
        self.latch=0
        self.statetable=0
        self.memory = 0
        self.PinJobs={}
        self.arcs=[]


def main():
    if (len(sys.argv)>1):
        Fname = sys.argv[1]
        if os.path.exists(Fname):
            os.system('/bin/rm lex.out db0.pickle')
            os.system('llbin/synlib_lexer %s'%Fname)
            os.system('llbin/synlibyacc.py lex.out')
            os.system('llbin/simplify_pickle.py db0.pickle db1.pickle')
        else:
            print 'file cannot be read "%s"'%Fname
            return
    pythonConnection = '-python' in sys.argv
    load_db0('db1.pickle')
    dump_dump()
    Top = ('Library',1)
    LL = DataBase[Top]
    Lib0 = match("library ( ?Lib )  { ?Items }",LL)
    if Lib0:
        Items = Lib0['Items']
        scan_lib_items(Items)
    else:
        print 'failed library'
    Fcc=open('msgsim_cells.ccc','w')
    for Cell in Cells:
        Cells[Cell].Types=Types
        msgsim2c.cell_dump_msgsim_c(Cells[Cell],Fcc,pythonConnection)
    Fcc.close()

    Fcc=open('cell.descriptions','w')
    for Cell in Cells:
        Cells[Cell].Types=Types
        msgsim2c.cell_dump_description(Cells[Cell],Fcc,pythonConnection)
    Fcc.close()


def scan_lib_items(Items):
    if len(Items[0])==4:
        one_lib_item(Items)
    else:
        for Key in Items:
            LL = DataBase[Key]
            one_lib_item(LL)

def one_lib_item(LL):
    Head = LL[0][0]
    if Head in knownUselessKeys:
        pass
    elif (Head=='cell'):
        deal_cell(LL)
    elif (Head=='type'):
        deal_type(LL)
    else:
        print 'unknown item',Head,LL

def deal_cell(LL):
    Lb0 = match('cell ( ?Name ) { ?Items }',LL)
    if not Lb0:
        print 'bad cell %s'%str(LL)
        return
    Name = Lb0['Name']
    Cells[Name]=cellClass(Name)
    Items = Lb0['Items']
    if len(Items[0])==4:
        Lb2 = match('?Param : ?Val ;',Items)
        if Lb2:
            Cells[Name].pairs[Lb2['Param']]=Lb2['Val']
        else:
            print 'wrong for deal_cell '
        return
    for Key in Lb0['Items']:
        LL2 =  DataBase[Key]
        Lb2 = match('?Param : ?Val ;',LL2)
        taken=False
        if Lb2:
            taken=True
            print Lb0['Name'],'cell item ',Lb2['Param'],Lb2['Val']
            Cells[Name].pairs[Lb2['Param']]=Lb2['Val']
        Lb2 = match('pin ( ?Pin ) { ?Items }',LL2)
        if not Lb2:
            Lb2 = match('pin ( ?Pin [ ?Ind ] ) { ?Items }',LL2)
            if Lb2:
                Pin = Lb2['Pin']
                Ind = Lb2['Ind']
                Lb2['Pin'] = '%s[%s]'%(Pin,Ind)

        if Lb2:
            taken=True
            Pin = Lb2['Pin']
            Cells[Name].pins[Pin]={}
            Items = Lb2['Items']
            if len(Items[0])==4:
                Lb3 = match('?Param : ?Val ;',Items)
                if Lb3:
                    Param,Val = (string.replace(Lb3['Param'],'"',''),string.replace(Lb3['Val'],'"',''))
                    Cells[Name].pins[Pin][Param]=Val
            else:
                 for Thing in Lb2['Items']:
                     Lparam = getPair(Thing)
                     if len(Thing)==2:
                         LLx = DataBase[Thing]
                     else:
                         LLx=Thing
                     if Lparam:
                         Cells[Name].pins[Pin][Lparam[0]]=Lparam[1]
                     elif (LLx[0][0] in ['timing']):
                         LLy = DataBase[LLx[4]]
                         workOnTiming(Name,Pin,LLy)
                     elif (LLx[0][0] in knownUselessPinItems):
                         pass
                     else:
                         print Lb0['Name'],'cell pin unknown',Lb2['Pin'],LLx
            
        Lb2 = match('bus ( ?Pin ) { ?Items }',LL2)
        if Lb2:
            taken=True
            Bus = Lb2['Pin']
            Cells[Name].busses[Bus]={}
            for Thing in Lb2['Items']:
                Lparam = getPair(Thing)
                LLx = DataBase[Thing]
                if Lparam:
                    Cells[Name].busses[Bus][Lparam[0]]=Lparam[1]
                elif (LLx[0][0] in knownUselessPinItems):
                    pass
                else:
                    print Lb0['Name'],'cell bus unknown',Lb2['Pin'],LLx
            

        Lb2 = match('memory ( ) { ?Items }',LL2)
        if Lb2:
            taken=True
            gather={}
            for Thing in Lb2['Items']:
                Lparam = getPair(Thing)
                print Lb0['Name'],'cell memory',Lparam 
                gather[Lparam[0]]=Lparam[1]
            Cells[Name].memory = gather

        if LL2[0][0] in ['leakage_power','test_cell']:
            taken=True

        Lb2 = match('ff ( ?Toks ) { ?Pairs }',LL2)
        if Lb2:
            taken=True
            Pairs = getPairs2(Lb2['Pairs'])
            Toks = getToks(Lb2['Toks'])
            
            Cells[Name].ff=(Toks,Pairs)

        Lb2 = match('latch ( ?Toks ) { ?Pairs }',LL2)
        if Lb2:
            taken=True
            Pairs = getPairs2(Lb2['Pairs'])
            Toks = getToks(Lb2['Toks'])
            Cells[Name].latch=(Toks,Pairs)

        Lb2 = match('statetable ( ?Exprs ) { ?Pair }',LL2)
        if Lb2:
            taken=True
            Pair = Lb2['Pair']
            Lines = Pair[2][0]
            Toks = getToks(Lb2['Exprs'])
            print  'pair',Lines,'toks',Toks
            Cells[Name].statetable=(Toks,Lines)



        if (not taken):
            print 'cell item unknown ',LL2

def workOnTiming(Name,Pin,LLy):
    Pairs = getPairs(LLy)
    if 'related_pin' in Pairs:
        Who = Pairs['related_pin']
        if 'timing_type' in Pairs:
            Type = Pairs['timing_type']
        else:
            Type = 'combi'
        Tuple = (Pin,Who,Type)
        if Tuple not in Cells[Name].arcs:
            Cells[Name].arcs.append(Tuple)

def getToks(List):
    res=[]
    for XX in List:
        Tok = string.replace(XX[0],'"','')
        if Tok !=',':
            res.append(Tok)
    return res

knownUselessPinItems = string.split('internal_power timing fall_transition rise_transition cell_rise cell_fall rise_constraint fall_constraint')

def getPair(Key):
    if Key in DataBase:
        LL2 = DataBase[Key]
        Lb2 = match('?Param : ?Val ;',LL2)
        if Lb2:
            return (string.replace(Lb2['Param'],'"',''),string.replace(Lb2['Val'],'"',''))
    return False


def getPairs(List):
    res = {}
    for Thing in List:
        Lparam = getPair(Thing)
        LLx = DataBase[Thing]
        if Lparam:
            res[Lparam[0]] = string.replace(Lparam[1],'"','')
        elif (LLx[0][0] in knownUselessPinItems):
            pass
        else:
            print 'error! get pair got %s lparam=%s llx=%s'%(str(Thing),Lparam,LLx)
    return res

def getPairs2(List):
    res = []
    for Thing in List:
        Lparam = getPair(Thing)
        LLx = DataBase[Thing]
        if Lparam:
            Tok = string.replace(Lparam[1],'"','')
            res.append((Lparam[0],Tok))
        elif (LLx[0][0] in knownUselessPinItems):
            pass
        else:
            print 'error! get pair got %s'%str(Thing)
    return res


def deal_type(LL):
    Lb0 = match('type ( ?Name ) { ?Pairs }',LL)
    Type = Lb0['Name']
    Types[Type]={}
    for Key in Lb0['Pairs']:
        LL2 =  DataBase[Key]
        Lb2 = match('?Param : ?Val ;',LL2)
        if Lb2:
#            print Lb0['Name'],'type lb2',Lb2['Param'],Lb2['Val']
            Types[Type][Lb2['Param']]=Lb2['Val']
        else:
            print 'bad type thing',LL2


def load_db0(Fname):
    global DataBase
    File = open(Fname)
    DataBase = pickle.load(File) 


def match(Pattern,List):
    if (len(List)==2)and(List in DataBase):
        return match(Pattern,DataBase[List])

    Words = string.split(Pattern)
    if len(Words)!=len(List): return False

    res={}
    for ind,Key in enumerate(Words):
        Act = List[ind]
        if (Key==Act[0]):
            pass
        elif(Key[0]=='?'):
            if len(Act)==2:
                res[Key[1:]]=DataBase[Act]
            elif len(Act)==4:
                res[Key[1:]]=Act[0]
            else:
                print 'error!'
                return 0
        else:
            return 0
    return res

def dump_dump():
    Fout = open('ttt.ttt','w')
    for Key in DataBase:
        Fout.write('key %s = %s\n'%(Key,DataBase[Key]))
    Fout.close()


knownUselessKeys = string.split(''' 
default_intrinsic_fall default_inout_pin_fall_res default_intrinsic_rise default_slope_rise
default_output_pin_fall_res default_slope_fall default_inout_pin_rise_res default_output_pin_rise_res
delay_model revision date comment time_unit
voltage_unit current_unit leakage_power_unit nom_process
nom_temperature nom_voltage capacitive_load_unit pulling_resistance_unit
 default_cell_leakage_power default_fanout_load default_inout_pin_cap default_input_pin_cap
 default_output_pin_cap default_max_transition default_leakage_power_density slew_derate_from_library
 slew_lower_threshold_pct_fall slew_upper_threshold_pct_fall slew_lower_threshold_pct_rise slew_upper_threshold_pct_rise
 input_threshold_pct_fall input_threshold_pct_rise output_threshold_pct_fall output_threshold_pct_rise
 k_process_cell_fall k_process_cell_leakage_power k_process_cell_rise k_process_fall_transition
 k_process_hold_fall k_process_hold_rise k_process_internal_power k_process_min_pulse_width_high
 k_process_min_pulse_width_low k_process_pin_cap k_process_recovery_fall k_process_recovery_rise
 k_process_rise_transition k_process_setup_fall k_process_setup_rise k_process_wire_cap
 k_process_wire_res k_temp_cell_fall k_temp_cell_rise k_temp_hold_fall
 k_temp_hold_rise k_temp_min_pulse_width_high k_temp_min_pulse_width_low k_temp_min_period
 k_temp_rise_propagation k_temp_fall_propagation k_temp_rise_transition k_temp_fall_transition
 k_temp_recovery_fall k_temp_recovery_rise k_temp_setup_fall k_temp_setup_rise
 k_volt_cell_fall k_volt_cell_rise k_volt_hold_fall k_volt_hold_rise
 k_volt_min_pulse_width_high k_volt_min_pulse_width_low k_volt_min_period k_volt_rise_propagation
 k_volt_fall_propagation k_volt_rise_transition k_volt_fall_transition k_volt_recovery_fall
 k_volt_recovery_rise k_volt_setup_fall k_volt_setup_rise operating_conditions
 default_operating_conditions wire_load output_voltage input_voltage
 input_voltage lu_table_template lu_table_template lu_table_template
 power_lut_template library_features technology simulation define_cell_area
 define_cell_area wire_load_selection wire_load_selection default_wire_load_selection default_wire_load
 default_wire_load_mode in_place_swap_mode default_max_fanout k_volt_cell_leakage_power
 k_temp_cell_leakage_power k_volt_internal_power k_temp_internal_power
 k_temp_wire_cap k_volt_wire_cap k_temp_wire_res k_volt_wire_res k_temp_pin_cap k_volt_pin_cap
 voltage_map
 ''')





main()



