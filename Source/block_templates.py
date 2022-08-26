from operator import ge
from statistics import variance
import sys
import os

def matlabFile(block):
    newpath = ".\\{name}".format(name = block.name)
    if not os.path.exists(newpath):
        os.makedirs(newpath)

    cFilename = '{name}.c'.format(name = block.name)
    headerFilename = '{name}.h'.format(name = block.name)
    matFilename = '.\{name}\{name}.m'.format(name = block.name)

    stepImpl = ''
    variables = ''
    varType = {'float':'single(0)', 'double':'double(0)', 'int':'uint32(0)'}
    for var in block.variables:
        variables += ',' + var.name

    if block.type == 'write':
        stepImpl = "function stepImpl(obj{variables})\n\
                coder.cinclude('{name}.h');\n\
                coder.ceval('send_{name}'{variables});\n\
            end".format(variables = variables, name = block.name)

    elif block.type == 'read':
        stepImpl = "function [{variables}] = stepImpl(obj)\n".format(variables = variables[1::], name = block.name)
        for var in block.variables:
            stepImpl += "\
                {varName} = {varType};\n".format(varName = var.name, varType = varType[var.type])

        stepImpl += "\
                coder.cinclude('{name}.h');\n\
                coder.ceval('update_{name}');\n".format(variables = variables[1::], name = block.name)

        for var in block.variables:
            stepImpl += "\
                {varName} = coder.ceval('get_{varName}');\n".format(varName = var.name)
        stepImpl += "\
            end\n"

    else:
        print("Wrong 'access' field. Enter correct value (write/read)")
        input()
        sys.exit()


    with open(matFilename, 'w') as matlab:
        matlab.write("classdef {name} < matlab.System & coder.ExternalDependency\n\
        % {name}- this block sends its inputs to active X-Plane simulation using shared memory. Note: in order for this block to work, special X-Plane plugin needs to be installed\n\
    \n\
        properties(Access = public)\n\
        \n\
        end\n\
            \n\
        properties(DiscreteState)\n\
    \n\
        end\n\
    \n\
        properties(Access = private)\n\
    \n\
        end\n\
    \n\
        methods(Access = protected)\n\
            function setupImpl(obj)\n\
                    coder.cinclude('{headerName}');\n\
                    coder.ceval('setup_{name}');\n\
            end\n\
    \n\
            {stepImpl}\
    \n\
            function resetImpl(obj)\n\
                \n\
            end\n\
            \n\
            function releaseImpl(obj)\n\
                coder.cinclude('{headerName}');\n\
                coder.ceval('close_{name}');\n\
            end\n\
        end\n\
            \n\
        methods (Static)\n\
            function name = getDescriptiveName()\n\
                name = '{name}';\n\
            end\n\
            function b = isSupportedContext(context)\n\
                b = context.isCodeGenTarget('rtw');\n\
            end\n\
            function updateBuildInfo(buildInfo, context)\n\
            % Update the build-time buildInfo\n\
                blockRoot = fileparts(mfilename('fullpath'));\n\
                buildInfo.addIncludePaths({{blockRoot}});\n\
                buildInfo.addIncludeFiles({{'{headerName}'}});\n\
                buildInfo.addSourcePaths({{blockRoot}});\n\
                buildInfo.addSourceFiles({{'{sourceName}'}});\n\
            end\n\
        end\n\
    end".format(name = block.name, headerName = headerFilename, sourceName = cFilename, stepImpl = stepImpl))


def cFile(block):
    cFilename = '.\{name}\{name}.c'.format(name = block.name)
    interface = ''
    active = ''
    variables = ''
    for var in block.variables:
        variables += ', ' + var.type + ' ' + var.name

    if block.type == 'write':
        interface = "void send_{name}({variables})\n\
{{\n\
    if ({name}_isMapped) {{\n".format(variables = variables[2::], name = block.name)

        active = "{name}_struct.active = 0;\n\
        memcpy({name}_Buf, &{name}_struct, sizeof({name}_struct));".format(name = block.name)

        for var in block.variables:
            interface += "\
        {name}_struct.{varName} = {varName};\n".format(name = block.name, varName = var.name)

        interface += "\
        {name}_struct.active = 1;\n\
        memcpy({name}_Buf, &{name}_struct, sizeof({name}_struct));\n\
    }}\n\
}}\n".format(name = block.name)

    elif block.type == 'read':
        for var in block.variables:
            interface += "\n{type} get_{varName}()\n\
{{\n\
    if ({name}_isMapped) {{\n\
        return {name}_struct.{varName};\n\
    }} else {{\n\
        return 0;\n\
    }}\n\
}}\n".format(name = block.name, varName = var.name, type = var.type)

        interface += "\n\
void update_{name}() {{\n\
    if ({name}_isMapped) {{\n\
        memcpy(&{name}_struct, {name}_Buf, sizeof({name}_struct));\n\
    }}\n\
}}\n".format(name = block.name)

    else:
        print("Wrong 'access' field. Enter correct value (write/read)")
        input()
        sys.exit()

    with open(cFilename,"w") as cSource:
        cSource.write("#include \"{name}.h\"\n\
\n\
\n\
void setup_{name}()\n\
{{\n\
    {name}_Mapping = OpenFileMapping(\n\
        FILE_MAP_ALL_ACCESS,   // read/write access\n\
        FALSE,                 // do not inherit the name\n\
        {name}_Name);               // name of mapping object\n\
    \n\
    if ({name}_Mapping == NULL) {{\n\
        {name}_isMapped = false;\n\
        return;\n\
    }}\n\
\n\
    {name}_Buf = (LPTSTR)MapViewOfFile({name}_Mapping, // handle to map object\n\
        FILE_MAP_ALL_ACCESS,  // read/write permission\n\
        0,\n\
        0,\n\
        BUF_SIZE);\n\
    \n\
    if ({name}_Buf == NULL) {{\n\
        {name}_isMapped = false;\n\
        return;\n\
    }}\n\
    {name}_isMapped = true;\n\
}}\n\n\
{interface}\
\n\
void close_{name}()\n\
{{\n\
    if ({name}_isMapped) {{\n\
        {active}\n\
        UnmapViewOfFile({name}_Buf);\n\
        CloseHandle({name}_Mapping);\n\
    }}\n\
}}".format(name = block.name, interface = interface, active = active))


def headerFile(block):
    headerFilename = '.\{name}\{name}.h'.format(name = block.name)
    interface = ''
    variables = ''
    
    for var in block.variables:
        variables += ', ' + var.type + ' ' + var.name

    if block.type == 'write':
        interface += "void send_{name}({variables});\n".format(name = block.name, variables = variables[2::])

    if block.type == 'read':
        interface += "void update_{name}();\n\n".format(name = block.name)
        for var in block.variables:
            interface += "\
{type} get_{varName}();\n".format(type = var.type, varName = var.name)

    struct = "struct {\n"

    for var in block.variables:
        struct += "\
    {type} {varName};\n".format(type = var.type, varName = var.name)

    struct += "\
    int active;\n\
}}{name}_struct;\n".format(name = block.name)
    with open(headerFilename,"w") as header:
        header.write("#pragma once\n\
#include <windows.h>\n\
#include <tchar.h>\n\
#include <stdio.h>\n\
#include <stdbool.h>\n\
\n\
#define BUF_SIZE 64\n\
HANDLE {name}_Mapping;\n\
LPCTSTR {name}_Buf;\n\
TCHAR {name}_Name[] = TEXT(\"{name}\");\n\
boolean {name}_isMapped;\n\
\n\
{struct}\
\n\
void setup_{name}();\n\
\n\
{interface}\
\n\
void close_{name}();".format(struct = struct, name = block.name, interface = interface))