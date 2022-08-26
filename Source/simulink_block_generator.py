import xml.etree.ElementTree as ET
import sys
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


blockList = []

tree = ET.parse('X-Plane_block_generator_config.xml')
root = tree.getroot()

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

plugin_templates.plugin_template(blockList)