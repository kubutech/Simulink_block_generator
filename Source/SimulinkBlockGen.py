from operator import contains
from platform import release
from urllib import response
import xml.etree.ElementTree as ET
import sys
import os
import requests
import shutil
import zipfile
import block_templates
import plugin_templates

class Variable:
    name = ''
    type = ''
    dataref = ''

    def __init__(self, name, type, dataref):
        self.name = name
        self.type = type
        self.dataref = dataref

class Block:
    variables = []
    name = ''
    type = ''
    updateRate = 0

    def __init__(self, name, type, updateRate):
        self.name = name
        self.type = type
        self.updateRate = int(updateRate)

    def putVariables(self, variables):
        self.variables = variables

pluginProject = "https://github.com/kubutech/Simulink_plugin/archive/refs/heads/master.zip"
try:
    blockList = []
    try:
        tree = ET.parse('SimulinkBlockGenConfig.xml')
        root = tree.getroot()
    except:
        print("Couldn't find configuration file. Make sure it's in the same directory as program!")
        input()
        sys.exit()

    for child in root:
        if child.tag == 'simulinkBlock':
            simulinkBlock = Block(child.get('name'), child.get('access'), child.get('updateRate'))
            variableList = []
            for var in child:
                try:
                    if (var.find('type').text == 'float' or var.find('type').text == 'double' or var.find('type').text == 'int'):
                        variableList.append(Variable(name=var.find('name').text, type = var.find('type').text, dataref = var.find('Dataref').text))
                    else:
                        print("Variable type wrong! (Remeber variable can only be float, double or int type)")
                        input
                        sys.exit()
                except Exception:
                    print("Wrong formating of 'variable' fields!")
                    input()
                    sys.exit()
            simulinkBlock.putVariables(variableList)
            for block in blockList:
                if block.name == simulinkBlock.name:
                    print("Cannot have two blocks with the same name!")
                    input()
                    sys.exit()
            blockList.append(simulinkBlock)


    for block in blockList:
        block_templates.matlabFile(block)
        block_templates.cFile(block)
        block_templates.headerFile(block)

    try:
        response = requests.get(pluginProject)

        zipFile = ".\Simulink_plugin.zip"

        open(zipFile, "wb").write(response.content)
        
        with zipfile.ZipFile(zipFile, 'r') as zip_ref:
            zip_ref.extractall(".\\")
        
        os.remove(zipFile)
        os.rename(".\Simulink_plugin-master", ".\Simulink_plugin_source")

    except Exception as a:
        print("Couldn't fetch plugin template project from Github")
        input()
        sys.exit()

    plugin_templates.plugin_template(blockList)

    if os.path.exists("C:\Program Files (x86)\Microsoft Visual Studio\\2022\BuildTools\MSBuild\Current\Bin"):
        os.environ["Path"] = "C:\Program Files (x86)\Microsoft Visual Studio\\2022\BuildTools\MSBuild\Current\Bin"
    else:
        print("MSBuild not installed! Aborting...")
        input()
        sys.exit()

    os.system("msbuild .\Simulink_plugin_source\Simulink_plugin.sln /p:Configuration=Release /p:Platform=x64")

    if os.path.exists(".\Simulink_plugin_source\\x64\Release\Simulink_plugin"):
        shutil.copytree(".\Simulink_plugin_source\\x64\Release\Simulink_plugin", ".\Resources\plugins\Simulink_plugin")
        print("Compilation successful!")
    else:
        print("Compilation error!")
        input()

    input()
except Exception as a:
    print(a)
    input()
