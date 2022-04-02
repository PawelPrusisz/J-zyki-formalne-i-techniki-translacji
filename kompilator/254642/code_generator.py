#Paweł Prusisz

from symbol_table import Variable


class CodeGenerator:
    def __init__(self, commands, symbols):
        self.commands = commands
        self.symbols = symbols
        self.code = []
        self.iterators = []

    def gen_code(self):
        self.gen_code_from_commands(self.commands)
        self.code.append("HALT")

    def gen_code_from_commands(self, commands):
        for command in commands:
            if command[0] == "write":
                value = command[1]
                register = 'a'
                register1 = 'b'
                if value[0] == "load":
                    if type(value[1]) == tuple:
                        if value[1][0] == "undeclared":
                            var = value[1][1]
                            self.load_variable_address(var, register, declared=False)
                            self.code.append(f"LOAD f")
                        elif value[1][0] == "array":
                            self.load_array_address_at(value[1][1], value[1][2], register, register1)
                            self.code.append(f"LOAD f")
                        elif value[1][0] == "unVARd":
                            self.load_iterator(value[1][1])
                    else:
                        if self.symbols[value[1]].initialized:
                            self.load_variable_address(value[1], register)
                            self.code.append(f"LOAD f")
                        else:
                            raise Exception(f"Use of uninitialized variable {value[1]}")

                elif value[0] == "const":
                    address = self.symbols.get_const(value[1])
                    if address is None:
                        address = self.symbols.add_const(value[1])
                        self.gen_const(address, register)
                        self.gen_const(value[1], register1)
                        self.code.append(f"SWAP {register1}")
                        self.code.append(f"STORE {register1}")
                    else:
                        self.gen_const(address, 'f')
                        self.code.append("LOAD f")
                        

                self.code.append(f"PUT")

            elif command[0] == "read":
                target = command[1]
                register = 'a'
                register1 = 'b'
                if type(target) == tuple:
                    if target[0] == "undeclared":
                        if target[1] in self.symbols.iterators:
                            raise Exception(f"Reading to iterator {target[1]}")
                        else:
                            raise Exception(f"Reading to undeclared variable {target[1]}")
                    elif target[0] == "array":
                        self.load_array_address_at(target[1], target[2], register, register1)
                else:
                    self.load_variable_address(target, register)
                    self.symbols[target].initialized = True
                self.code.append(f"GET")
                self.code.append(f"STORE f")
                
            elif command[0] == "assign":
                target = command[1]
                expression = command[2]
                target_reg = 'a'
                second_reg = 'f'
                third_reg = 'c'
                self.calculate_expression(expression)
                
                
                if(expression[0] == 'load'):
                    self.code.append("SWAP g")
                elif (expression[0] == 'mod' or expression[0] == 'div' or expression[0] == 'mul' or expression[0] == 'const'):
                    self.code.append("SWAP f")
                    self.code.append("SWAP g")
                    

            
                if type(target) == tuple:
                    if target[0] == "undeclared":
                        if target[1] in self.symbols.iterators:
                            raise Exception(f"Assigning to iterator {target[1]}")
                        else:
                            raise Exception(f"Assigning to undeclared variable {target[1]}")
                    elif target[0] == "array":
                        self.load_array_address_at(target[1], target[2], second_reg, third_reg)
                    elif target[0] == "unVARd":
                        self.load_iterator(target[1], second_reg, third_reg)

                        
                else:
                    if type(self.symbols[target]) == Variable:
                        self.load_variable_address(target, second_reg)
                        
                        self.symbols[target].initialized = True
                    else:
                        raise Exception(f"Assigning to array {target} with no index provided")
                if(expression[0] == 'load' or expression[0] == 'mod' or expression[0] == 'div'  or expression[0] == 'mul' or expression[0] == 'const'):
                    self.code.append("SWAP g")
                self.code.append(f"STORE f")
          
            elif command[0] == "if":
                condition = self.simplify_condition(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.gen_code_from_commands(command[2])
                else:
                    self.prepare_consts_before_block(command[-1])
                    condition_start = len(self.code)
                    self.check_condition(condition)
                    command_start = len(self.code)
                    self.gen_code_from_commands(command[2])
                    command_end = len(self.code)
                    for i in range(condition_start, command_start):
                        self.code[i] = self.code[i].replace('finish', str(command_end - i))

            elif command[0] == "ifelse":
                condition = self.simplify_condition(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.gen_code_from_commands(command[2])
                    else:
                        self.gen_code_from_commands(command[3])
                else:
                    self.prepare_consts_before_block(command[-1])
                    condition_start = len(self.code)
                    self.check_condition(command[1])
                    if_start = len(self.code)
                    self.gen_code_from_commands(command[2])
                    self.code.append(f"JUMP finish")
                    else_start = len(self.code)
                    self.gen_code_from_commands(command[3])
                    command_end = len(self.code)
                    self.code[else_start - 1] = self.code[else_start - 1].replace('finish', str(command_end - else_start + 1))
                    for i in range(condition_start, if_start):
                        self.code[i] = self.code[i].replace('finish', str(else_start - i))
            
            elif command[0] == "while":
                condition = self.simplify_condition(command[1])
                if isinstance(condition, bool):
                    if condition:
                        self.prepare_consts_before_block(command[-1])
                        loop_start = len(self.code)
                        self.gen_code_from_commands(command[2])
                        self.code.append(f"JUMP {loop_start - len(self.code)}")
                else:
                    
                    self.prepare_consts_before_block(command[-1])
                    condition_start = len(self.code)
                    self.check_condition(command[1])
                    loop_start = len(self.code)
                    self.gen_code_from_commands(command[2])
                    self.code.append(f"JUMP {condition_start - len(self.code)}")
                    loop_end = len(self.code)
                    for i in range(condition_start, loop_start):
                        self.code[i] = self.code[i].replace('finish', str(loop_end - i))
            
            elif command[0] == "until":
                loop_start = len(self.code)
                self.gen_code_from_commands(command[2])
                condition_start = len(self.code)
                self.check_condition(command[1])
                condition_end = len(self.code)
                for i in range(condition_start, condition_end):
                    self.code[i] = self.code[i].replace('finish', str(loop_start - i))
            
            elif command[0] == "forup":
                
                if command[2][0] == command[3][0] == "const":
                    if command[2][1] > command[3][1]:
                        continue
                    
                if self.iterators:
                    """address, bound_address = self.symbols.get_iterator(self.iterators[-1])
                    self.gen_const(address, 'e')
                    self.code.append("STORE e")"""
                else:
                    self.prepare_consts_before_block(command[-1])

                iterator = command[1]
                
                    
                address, bound_address = self.symbols.add_iterator(iterator)

                if self.symbols.is_iterator(iterator):
                    self.symbols.change_iterator(iterator, address, bound_address)

                self.gen_const(bound_address, 'a')
                self.code.append("SWAP d")
                if(command[3][0] == 'const'):
                    self.gen_const(command[3][1], 'a')
                else:
                    self.calculate_expression(command[3], 'a')
                
                

                self.code.append("STORE d")

                self.code.append("RESET d")
                
                self.gen_const(address, 'a')
                self.code.append("SWAP d")
                if(command[2][0] == 'const'):
                    self.gen_const(command[2][1], 'a')
                else:
                    self.calculate_expression(command[2], 'a')
                    
                self.code.append("STORE d")
                self.iterators.append(iterator)

                condition_start = len(self.code)
                self.gen_const(address, 'f')
                self.code.append("LOAD f")
                
                self.code.append("SWAP c")

                self.gen_const(bound_address, 'f')
                self.code.append("LOAD f")
                self.code.append("SUB c")
                
                
                self.code.append("JNEG finish")

                loop_start = len(self.code)
                self.gen_code_from_commands(command[4])
                self.gen_const(address, 'f')
                self.code.append("LOAD f")
                self.code.append("INC a")
                self.code.append("STORE f")
                self.code.append(f"JUMP {condition_start - len(self.code)}")
                loop_end = len(self.code)

                self.code[loop_start - 1] = f"JNEG  {loop_end - loop_start + 1}"
                
                self.iterators.pop()
                if self.iterators:
                    address, bound_address = self.symbols.get_iterator(self.iterators[-1])
                    self.gen_const(address, 'f')
                    self.code.append(f"LOAD f")
                    self.code.append("SWAP f")
            
            elif command[0] == "fordown":
                
                if command[2][0] == command[3][0] == "const":
                    if command[2][1] < command[3][1]:
                        continue
                if self.iterators:
                    """address, bound_address = self.symbols.get_iterator(self.iterators[-1])
                    self.gen_const(address, 'e')
                    self.code.append("SWAP f")
                    self.code.append("STORE e")"""
                else:
                    self.prepare_consts_before_block(command[-1])

                iterator = command[1]
                address, bound_address = self.symbols.add_iterator(iterator)
                self.gen_const(bound_address, 'a')
                self.code.append("SWAP d")
                if(command[3][0] == 'const'):
                    self.gen_const(command[3][1], 'a')
                else:
                    self.calculate_expression(command[3], 'a')
                
                

                self.code.append("STORE d")

                self.code.append("RESET d")
                
                self.gen_const(address, 'a')
                self.code.append("SWAP d")
                if(command[2][0] == 'const'):
                    self.gen_const(command[2][1], 'a')
                else:
                    self.calculate_expression(command[2], 'a')
                    
                self.code.append("STORE d")
                self.iterators.append(iterator)

                condition_start = len(self.code)
                self.gen_const(address, 'f')
                self.code.append("LOAD f")
                
                self.code.append("SWAP c")

                self.gen_const(bound_address, 'f')
                self.code.append("LOAD f")
                self.code.append("SUB c")
                
                
                self.code.append("JPOZ finish")

                loop_start = len(self.code)
                self.gen_code_from_commands(command[4])
                self.gen_const(address, 'f')
                self.code.append("LOAD f")
                self.code.append("DEC a")
                self.code.append("STORE f")
                self.code.append(f"JUMP {condition_start - len(self.code)}")
                loop_end = len(self.code)

                self.code[loop_start - 1] = f"JPOS {loop_end - loop_start + 1}"

                self.iterators.pop()
                if self.iterators:
                    address, bound_address = self.symbols.get_iterator(self.iterators[-1])
                    self.gen_const(address, 'f')
                    self.code.append(f"LOAD f")
                    self.code.append("SWAP f")
            

    def gen_const(self, const, targreg='a'):
        reg1 = 'a'
        reg2 = 'b'
        self.code.append(f"RESET {reg1}")
        self.code.append(f"RESET {reg2}")
        self.code.append(f"INC {reg2}")
        
        if(const >= 0):
            bits = bin(const)[2:]
            for bit in bits[:-1]:
                if bit == '1':
                    self.code.append(f"INC {reg1}")
                self.code.append(f"SHIFT {reg2}")
            if bits[-1] == '1':
                self.code.append(f"INC {reg1}")
        else:
            bits = bin(-const)[2:]
            for bit in bits[:-1]:
                if bit == '1':
                    self.code.append(f"DEC {reg1}")
                self.code.append(f"SHIFT {reg2}")
            if bits[-1] == '1':
                self.code.append(f"DEC {reg1}")
        if(targreg != 'a'):
            self.code.append(f"SWAP {targreg}")

    def calculate_expression(self, expression, target_reg='a', second_reg='b', third_reg='c', fourth_reg='d',
                             fifth_reg='e'):
        if expression[0] == "const":
            self.gen_const(expression[1], 'f')

        elif expression[0] == "load":
            if type(expression[1]) == tuple:
                if expression[1][0] == "undeclared":
                    self.load_variable(expression[1][1], target_reg, declared=False)
                elif expression[1][0] == "array":
                    self.load_array_at(expression[1][1], expression[1][2], target_reg, second_reg)
                elif expression[1][0] == "unVARd":
                    self.load_iterator(expression[1][1])
                    
                    
            else:
                if self.symbols[expression[1]].initialized:
                    self.load_variable(expression[1], target_reg)
                else:
                    raise Exception(f"Use of uninitialized variable {expression[1]}")

        else:
            if expression[1][0] == 'const':
                const, var = 1, 2
            elif expression[2][0] == 'const':
                const, var = 2, 1
            else:
                const = None

            if expression[0] == "add":
                if expression[1][0] == expression[2][0] == "const":
                    self.gen_const(expression[1][1] + expression[2][1], 'f')
                else:

                    self.calculate_expression(expression[1], target_reg, second_reg)
                    if expression[1][0] == "const":
                        self.code.append("SWAP f")
                    self.code.append(f"SWAP d")

                    self.calculate_expression(expression[2], target_reg, second_reg)
                    if expression[2][0] == "const":
                        self.code.append("SWAP f")
                    self.code.append(f"ADD d")

                    self.code.append(f"SWAP f")

            elif expression[0] == "sub":
                if expression[1][0] == expression[2][0] == "const":
                    self.gen_const(expression[1][1] - expression[2][1], 'f')
                    
                elif expression[1] == expression[2]:
                    self.code.append(f"RESET {target_reg}")

                else:
                    self.calculate_expression(expression[2], target_reg, second_reg)
                    if expression[2][0] == "const":
                        self.code.append("SWAP f")
                    self.code.append(f"SWAP d")
                    self.calculate_expression(expression[1], target_reg, second_reg)
                    if expression[1][0] == "const":
                        self.code.append("SWAP f")
                    self.code.append(f"SUB d")
                    self.code.append(f"SWAP f")

            elif expression[0] == "mul":
                if expression[1][0] == expression[2][0] == "const":
                    self.gen_const(expression[1][1] * expression[2][1], 'f')
                    return

                elif expression[1][0] == 'const':
                    self.gen_const(expression[1][1], 'd')
                    self.calculate_expression(expression[2], target_reg, second_reg)

                elif expression[2][0] == 'const':
                    self.gen_const(expression[2][1], 'd')
                    self.calculate_expression(expression[1], target_reg, second_reg)
                else:
                    self.calculate_expression(expression[2], target_reg, second_reg)
                    self.code.append("SWAP d")
                    self.calculate_expression(expression[1], target_reg, second_reg)
                    

                self.code.append("SWAP c")
                
               
                self.code.append("RESET a")
                self.code.append("RESET b")
                self.code.append("RESET e")
                self.code.append("RESET f")
                self.code.append("RESET g")
                self.code.append("RESET h")

               
                self.code.append("ADD c")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("INC e")
                self.code.append("RESET a")
                self.code.append("SUB c")
                self.code.append("SWAP c")

                
                self.code.append("RESET a")
                self.code.append("ADD d")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("INC e")
                self.code.append("RESET a")
                self.code.append("SUB d")
                self.code.append("SWAP d")

                

                self.code.append("RESET a")
                self.code.append("ADD e")
                self.code.append("DEC a")
                self.code.append("DEC a")
                self.code.append("JZERO 2")
                self.code.append("JUMP 3")
                self.code.append("DEC e")
                self.code.append("DEC e")
                
                
                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("SUB d")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("RESET a")
                self.code.append("SWAP c")
                self.code.append("SWAP d")
                self.code.append("SWAP c")


                

                self.code.append("RESET f")
                self.code.append("RESET a")
                self.code.append("INC a")
                self.code.append("SHIFT f")
                self.code.append("SUB d")
                self.code.append("JZERO 8") 
                self.code.append("JPOS 3")

                self.code.append("INC f")
                self.code.append("JUMP -7")

                self.code.append("RESET a")
                self.code.append("ADD f")
                self.code.append("JZERO 14")
                self.code.append("DEC f")
                self.code.append("RESET a")
                self.code.append("INC a")
                self.code.append("SHIFT f")
                self.code.append("SWAP d")
                self.code.append("SUB d")
                self.code.append("SWAP d")
                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("SHIFT f")
                self.code.append("ADD b")
                self.code.append("SWAP b")
                self.code.append("JUMP -24")
                

                
                self.code.append("SWAP e")
                self.code.append("JPOS 2")
                self.code.append("JUMP 5")
                self.code.append("RESET a")
                self.code.append("SUB b")
                self.code.append("SWAP f")
                self.code.append("JUMP 3")
                self.code.append("SWAP b")
                self.code.append("SWAP f")
                      
            elif expression[0] == "div":
                
                if expression[1][0] == expression[2][0] == "const":
                    if expression[2][1] != 0:
                        self.gen_const(expression[1][1] // expression[2][1], 'f')
                    else:
                        self.code.append(f"RESET f")
                    return

                elif expression[1][0] == 'const':
                    self.gen_const(expression[1][1], 'd')
                    self.calculate_expression(expression[2], target_reg, second_reg)

                elif expression[2][0] == 'const':
                    self.gen_const(expression[2][1], 'd')
                    self.calculate_expression(expression[1], target_reg, second_reg)
                else:
                    self.calculate_expression(expression[2], target_reg, second_reg)
                    self.code.append("SWAP d")
                    self.calculate_expression(expression[1], target_reg, second_reg)

                
                self.code.append("SWAP c")

               

                self.code.append("RESET a")
                self.code.append("RESET b")
                self.code.append("RESET e")
                self.code.append("RESET f")
                self.code.append("RESET g")
                self.code.append("RESET h")
                
                
                self.code.append("ADD d")
                self.code.append("JZERO 63") 
                self.code.append("RESET a")

                self.code.append("ADD d")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("INC e")
                self.code.append("RESET a")
                self.code.append("SUB d")
                self.code.append("SWAP d")


                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("INC e")
                self.code.append("RESET a")
                self.code.append("SUB c")
                self.code.append("SWAP c")

                
                self.code.append("RESET a")
                self.code.append("ADD e")
                self.code.append("DEC a")
                self.code.append("DEC a")
                self.code.append("JZERO 2")
                self.code.append("JUMP 2")
                self.code.append("RESET e")

                

                
                
                self.code.append("RESET f")
                self.code.append("RESET a")
                self.code.append("ADD d")
                self.code.append("SHIFT f")
                self.code.append("SUB c")
                self.code.append("JZERO 8")
                self.code.append("JPOS 3")
                self.code.append("INC f")
                self.code.append("JUMP -7")

                self.code.append("RESET a")
                self.code.append("ADD f")
                self.code.append("JZERO 16")

                self.code.append("DEC f")
                self.code.append("RESET a")
                self.code.append("INC a")
                self.code.append("SHIFT f")
                self.code.append("ADD b")
                self.code.append("SWAP b")

                self.code.append("RESET a")
                self.code.append("ADD d")
                self.code.append("SHIFT f")
                self.code.append("SWAP f")
                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("SUB f")
                self.code.append("SWAP c")

                self.code.append("JUMP -26")
                
                
                
                
                self.code.append("SWAP e")
                self.code.append("JPOS 2")
                self.code.append("JUMP 10")
                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("JPOS 2")
                self.code.append("JUMP 2")
                self.code.append("INC b")
                self.code.append("RESET a")
                self.code.append("SUB b")
                self.code.append("SWAP f")
                self.code.append("JUMP 3")
                self.code.append("SWAP b")
                self.code.append("SWAP f")
                

            elif expression[0] == "mod":
                if expression[1][0] == expression[2][0] == "const":
                    if expression[2][1] != 0:
                        self.gen_const(expression[1][1] % expression[2][1], 'f')
                    else:
                        self.code.append(f"RESET f")
                    return

                elif expression[1][0] == 'const':
                    self.gen_const(expression[1][1], 'd')
                    self.calculate_expression(expression[2], target_reg, second_reg)

                elif expression[2][0] == 'const':
                    self.gen_const(expression[2][1], 'd')
                    self.calculate_expression(expression[1], target_reg, second_reg)
                else:
                    self.calculate_expression(expression[2], target_reg, second_reg)
                    self.code.append("SWAP d")
                    self.calculate_expression(expression[1], target_reg, second_reg)

                self.code.append("SWAP c")
                

                self.code.append("RESET a")
                self.code.append("RESET b")
                self.code.append("RESET e")
                self.code.append("RESET f")
                self.code.append("RESET g")
                self.code.append("RESET h")
                
                self.code.append("ADD d")
                self.code.append("JZERO 76")
                self.code.append("RESET a")

                self.code.append("ADD d")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("INC g")
                self.code.append("RESET a")
                self.code.append("SUB d")
                self.code.append("SWAP d")

                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("JNEG 2")
                self.code.append("JUMP 5")
                self.code.append("INC e")
                self.code.append("RESET a")
                self.code.append("SUB c")
                self.code.append("SWAP c")

                
                

                self.code.append("RESET f")
                self.code.append("RESET a")
                self.code.append("ADD d")
                self.code.append("SHIFT f")
                self.code.append("SUB c")
                self.code.append("JZERO 8")
                self.code.append("JPOS 3")
                self.code.append("INC f")
                self.code.append("JUMP -7")
               

                self.code.append("RESET a")
                self.code.append("ADD f")
                self.code.append("JZERO 16")

               
                self.code.append("DEC f")
                self.code.append("RESET a")
                self.code.append("INC a")
                self.code.append("SHIFT f")
                self.code.append("ADD b")
                self.code.append("SWAP b")

                self.code.append("RESET a")
                self.code.append("ADD d")
                self.code.append("SHIFT f")
                self.code.append("SWAP f")
                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("SUB f")
                self.code.append("SWAP c")

                self.code.append("JUMP -26")

                
                
                
                self.code.append("RESET a")
                self.code.append("ADD e")
                self.code.append("JPOS 2")
                self.code.append("JUMP 9")
                self.code.append("RESET a")
                self.code.append("ADD g")
                self.code.append("JPOS 2")
                self.code.append("JUMP 9")
                self.code.append("RESET a")
                self.code.append("SUB c")
                self.code.append("SWAP f")
                self.code.append("JUMP 22") 

                self.code.append("RESET a")
                self.code.append("ADD e")
                self.code.append("JPOS 2")
                self.code.append("JUMP 6")
                self.code.append("RESET a")
                self.code.append("ADD d")
                self.code.append("SUB c")
                self.code.append("SWAP f")
                self.code.append("JUMP 13")

                self.code.append("RESET a")
                self.code.append("ADD g")
                self.code.append("JPOS 2")
                self.code.append("JUMP 6")
                self.code.append("RESET a")
                self.code.append("SUB d")
                self.code.append("ADD c")
                self.code.append("SWAP f")
                self.code.append("JUMP 4")

                self.code.append("RESET a")
                self.code.append("ADD c")
                self.code.append("SWAP f")

    def simplify_condition(self, condition):
        if condition[1][0] == "const" and condition[2][0] == "const":
            if condition[0] == "leq":
                return condition[1][1] <= condition[2][1]
            elif condition[0] == "geq":
                return condition[1][1] >= condition[2][1]
            elif condition[0] == "leq":
                return condition[1][1] < condition[2][1]
            elif condition[0] == "ge":
                return condition[1][1] > condition[2][1]
            elif condition[0] == "eq":
                return condition[1][1] == condition[2][1]
            elif condition[0] == "neq":
                return condition[1][1] != condition[2][1]


        elif condition[1][0] == "const" and condition[1][1] == 0:
            if condition[0] == "leq":
                return True
            elif condition[0] == "ge":
                return False
            else:
                return condition

        elif condition[2][0] == "const" and condition[2][1] == 0:
            if condition[0] == "geq":
                return True
            elif condition[0] == "leq":
                return False
            else:
                return condition

        elif condition[1] == condition[2]:
            if condition[0] in ["geq", "leq", "eq"]:
                return True
            else:
                return False

        else:
            return condition

    def check_condition(self, condition, first_reg='a', second_reg='b', third_reg='c'):
        if condition[1][0] == "const" and condition[1][1] == 0:
            if condition[0] == "geq" or condition[0] == "eq":
                self.calculate_expression(condition[2], first_reg, second_reg)
                self.code.append(f"JZERO 2")
                self.code.append("JUMP finish")

            elif condition[0] == "leq" or condition[0] == "neq":
                self.calculate_expression(condition[2], first_reg, second_reg)
                self.code.append(f"JZERO finish")

        elif condition[2][0] == "const" and condition[2][1] == 0:
            if condition[0] == "leq" or condition[0] == "eq":
                self.calculate_expression(condition[1], first_reg, second_reg)
                self.code.append(f"JZERO 2")
                self.code.append("JUMP finish")

            elif condition[0] == "ge" or condition[0] == "neq":
                self.calculate_expression(condition[1], first_reg, second_reg)
                self.code.append(f"JZERO finish")

        else:
            self.calculate_expression(condition[2], 'f', third_reg)
            if(condition[2][0] != 'load'):
                self.code.append("SWAP f")
            self.code.append("SWAP d")
            self.calculate_expression(condition[1], 'f', third_reg)
            if(condition[1][0] != 'load'):
                self.code.append("SWAP f")
            
            if condition[0] == "leq":
                self.code.append(f"SUB d")
                self.code.append(f"JNEG 3")
                self.code.append(f"JZERO 2")
                self.code.append(f"JUMP finish")

            elif condition[0] == "geq":
                self.code.append(f"SUB d")
                self.code.append(f"JPOS 3")
                self.code.append(f"JZERO 2")
                self.code.append(f"JUMP finish")

            elif condition[0] == "le":
                self.code.append(f"SUB d")
                self.code.append(f"JNEG 2")
                self.code.append(f"JUMP finish")

            elif condition[0] == "ge":
                self.code.append(f"SUB d")
                self.code.append(f"JPOS 2")
                self.code.append(f"JUMP finish")

            elif condition[0] == "eq":
                self.code.append(f"SUB d")
                self.code.append(f"JZERO 2")
                self.code.append(f"JUMP finish")

            elif condition[0] == "neq":
                self.code.append(f"SUB d")
                self.code.append(f"JZERO finish")

    def load_array_at(self, array, index, reg1, reg2):

        self.load_array_address_at(array, index, reg1, reg2)
        self.code.append(f"LOAD f")
          
    def load_array_address_at(self, array, index, reg1, reg2):
        regH = 'a'
        if type(index) == int:
            address = self.symbols.get_address((array, index))
            self.gen_const(address, 'f')
            

        elif type(index) == tuple:
            
            if type(index[1]) == tuple:
                self.load_iterator(index[1][1], regH)
            else:
                if not self.symbols[index[1]].initialized:
                    raise Exception(f"Trying to use {array}[{index[1]}] where variable {index[1]} is uninitialized")
                self.load_variable(index[1], regH)
            
            self.code.append(f"SWAP e")
            var = self.symbols.get_variable(array)

            self.gen_const(var.first_index, 'a')
            self.code.append(f"SWAP c")
            self.gen_const(var.memory_offset, 'a')
            self.code.append(f"SWAP h")
            
            self.code.append(f"RESET a")
            self.code.append(f"ADD h")
            self.code.append(f"ADD e")
            self.code.append(f"SUB c")
            
            self.code.append(f"SWAP f")
            
    def load_variable(self, name, reg, declared=True):
        if not declared and self.iterators and name == self.iterators[-1]:
            self.load_variable_address(name, 'a')
            self.code.append("SWAP d")
            self.code.append("LOAD d")
        else:
            self.load_variable_address(name, reg, declared)
            self.code.append(f"LOAD f")

    def load_iterator(self, name, reg = 'a', declared=True):
        if name in self.iterators:
            address = self.symbols.get_iterator(name)
            self.gen_const(address[0], 'a')
            self.code.append("LOAD a")

    def load_variable_address(self, name, reg, declared=True):
        reg = 'a'
        if declared or name in self.iterators:
            address = self.symbols.get_address(name)
            self.gen_const(address, 'f')
            
        else:
            raise Exception(f"Undeclared variable {name}")

    def prepare_consts_before_block(self, consts, reg1='a', reg2='b'):
        reg2 = 'a'
        for c in consts:
            address = self.symbols.get_const(c)
            if address is None:
                address = self.symbols.add_const(c)
                self.gen_const(address, 'f')
                self.gen_const(c, 'a')
                self.code.append(f"STORE f")
