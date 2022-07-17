import os
import sys

def plugin_template(blocksList):
    newpath = ".\\Plugin"
    content = "#pragma once\n\n"
    varDefs = ''

    if not os.path.exists(newpath):
        os.makedirs(newpath)
    
    for block in blocksList:
        varDefs += "TCHAR {name}_Mapping[] = TEXT(\"{name}\");\n\
HANDLE {name}_Handle;\n\
LPCTSTR {name}_Buf;\n\
Str_{name}_Datarefs {name}_Datarefs;\n\
Str_{name} {name};\n\n".format(name = block.name)

        structs = "typedef struct {\n"
        structsDataref = "typedef struct {\n"
        
        for var in block.variables:
            structsDataref += "\tXPLMDataRef {varName};\n".format(varName = var.name)
            structs += "\t{type} {varName};\n".format(varName = var.name, type = var.type)
        structsDataref += "}}Str_{name}_Datarefs;\n".format(name = block.name)
        structs += "\tint active;\n}}Str_{name};\n".format(name = block.name)

        content += structsDataref + '\n'
        content += structs + '\n'

    with open(".\\Plugin\\structTypeDefs.h","w") as structDefs:
            structDefs.write(content)
        


    content = "#pragma once\n\
#include <string.h>\n\
#include <stdio.h>\n\
#include <time.h>\n\
#include \"XPLMDisplay.h\"\n\
#include \"XPLMGraphics.h\"\n\
#include \"XPLMPlugin.h\"\n\
#include \"XPLMDataAccess.h\"\n\
#include \"XPLMProcessing.h\"\n\
#include \"structTypeDefs.h\"\n\
\n\
#define BUF_SIZE 64\n\
\n\
{varDefs}\
\n\
XPLMFlightLoopID loopDataref;\n\
XPLMFlightLoopID loopFlightData;\n\
\n\
#include \"Simulink_plugin_functions.h\"".format(varDefs = varDefs)

    with open(".\Plugin\Simulink_plugin.h", "w") as header:
        header.write(content)

    content = "#pragma once\n\nfloat UpdateFlightData(float inElapsedSinceLastCall,\n\
	float inElapsedTimeSinceLastFlightLoop,\n\
	int inCounter,\n\
	void* time)\n{\n"

    for block in blocksList:
        if block.type == "write":
            content += "\tmemcpy(&{name}, {name}_Buf, sizeof({name}));\n\n\
    if ({name}.active > 0) {{\n".format(name = block.name)
            for var in block.variables:
                content += "\t\tXPLMSetData{type}({name}_Datarefs.{varName}, {name}.{varName});\n".format(name = block.name, varName = var.name, type = var.type[0])
            content += "\t}\n\n"

        if block.type == 'read':
            for var in block.variables:
                content += "\t{name}.{varName} = XPLMGetData{type}({name}_Datarefs.{varName});\n".format(name = block.name, varName = var.name, type = var.type[0])
            content += "\n\
    memcpy(PVOID({name}_Buf), &{name}, sizeof({name}));\n\n".format(name = block.name)

    content += "\treturn 0.008;\n}\n\n"

    content += "void FindDataRefs()\n{\n"

    for block in blocksList:
        for var in block.variables:
            content += "\t{name}_Datarefs.{varName} = XPLMFindDataRef(\"{dataref}\");\n".format(name = block.name, varName = var.name, dataref = var.dataref)
        content += "\n"
    content += "}\n\n"

    content += "void setupSharedMem()\n{\n"

    for block in blocksList:
        content += "\t{name}_Handle = CreateFileMapping(\n\
		INVALID_HANDLE_VALUE,\n\
		NULL,\n\
		PAGE_READWRITE,\n\
		0,\n\
		BUF_SIZE,\n\
		{name}_Mapping);\n\n\
    {name}_Buf = (LPTSTR)MapViewOfFile({name}_Handle,\n\
		FILE_MAP_ALL_ACCESS,\n\
		0,\n\
		0,\n\
		BUF_SIZE);\n\n".format(name = block.name)

    content += "}\n\n"

    content += "void closeSharedMem()\n{\n"
    for block in blocksList:
        content += "\tUnmapViewOfFile({name}_Buf);\n\
	CloseHandle({name}_Handle);\n\n".format(name = block.name)
    
    content += "}"
    
    with open(".\Plugin\Simulink_plugin_functions.h","w") as functions:
        functions.write(content)