Desc = cellDescClass("SDFFNSRX4")
Desc.properties["cell_leakage_power"] = "4071.617280"
Desc.properties["cell_footprint"] = "sdffnsr"
Desc.properties["area"] = "126.403200"
Desc.pinOrder = ['CKN', 'D', 'IQ', 'IQN', 'Q', 'QN', 'RN', 'SE', 'SI', 'SN', 'next']
Desc.add_arc("CKN","SI","setup_falling")
Desc.add_arc("CKN","SI","hold_falling")
Desc.add_arc("CKN","SE","setup_falling")
Desc.add_arc("CKN","SE","hold_falling")
Desc.add_arc("CKN","D","setup_falling")
Desc.add_arc("CKN","D","hold_falling")
Desc.add_arc("CKN","SN","setup_falling")
Desc.add_arc("CKN","SN","hold_falling")
Desc.add_arc("CKN","RN","setup_falling")
Desc.add_arc("CKN","RN","hold_falling")
Desc.add_arc("CKN","Q","falling_edge")
Desc.add_arc("SN","Q","preset")
Desc.add_arc("RN","Q","clear")
Desc.add_arc("CKN","QN","falling_edge")
Desc.add_arc("SN","QN","clear")
Desc.add_arc("RN","QN","preset")
Desc.add_param("area",126.403200);
Desc.add_pin("D","input")
Desc.add_pin("IQ","output")
Desc.add_pin_func("IQ","unknown")
Desc.set_pin_job("CKN","clock")
Desc.add_pin("CKN","input")
Desc.add_pin("next","output")
Desc.add_pin_func("next","unknown")
Desc.add_pin("Q","output")
Desc.add_pin_func("Q","unknown")
Desc.add_pin("SI","input")
Desc.add_pin("IQN","output")
Desc.add_pin_func("IQN","unknown")
Desc.add_pin("SN","input")
Desc.add_pin("RN","input")
Desc.add_pin("SE","input")
Desc.add_pin("QN","output")
Desc.add_pin_func("QN","unknown")
Desc.set_job("flipflop")
CellLib["SDFFNSRX4"]=Desc