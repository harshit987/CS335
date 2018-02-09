#!/usr/bin/env python
from get_reg import *
from utilities import *

class CodeGenerator:
    def gen_data_section(self):
        print("extern printf\n")
        print("section\t.data\n")
        print("print_int:\tdb\t\"%d\",10,0")
        for symbol in symbol_table.keys():
            if symbol_table[symbol].array_size != None:
                print(str(symbol) + "\ttimes\t" + str(symbol_table[symbol].array_size) + "\tdd\t0")
            else:
                print(str(symbol) + "\tdd\t0")

    def gen_start_template(self):
        print()
        print("section .text")
        print("\tglobal main")
        print("main:")

    def op_print_int(self, instr):
        print("\tpush ebp")
        print("\tmov ebp,esp")
        loc = get_best_location(instr.inp1)
        print("\tpush dword " + str(loc))
        print("\tpush dword print_int")
        print("\tcall printf")
        print("\tadd esp, 8")
        print("\tmov esp, ebp")
        print("\tpop ebp")

    def op_add(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", [" + instr.inp1 + "]")
        R2 = get_best_location(instr.inp2)
        print("\tadd " + R1 + ", " + R2)


    def op_sub(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", [" + instr.inp1 + "]")
        R2 = get_best_location(instr.inp2)
        print("\tsub " + R1 + ", " + R2)


    def op_mult(self, instr):
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", [" + instr.inp1 + "]")
        R2 = get_best_location(instr.inp2)
        print("\timul " + R1 + ", " + R2)    ###### Can do bit-shift if multiplier is 2


    def op_div(self, instr):
        save_reg_contents("edx")
        save_reg_contents("eax")
        print("\txor edx, edx")
        print("\tmov eax, " + get_best_location(instr.inp1))
        if instr.inp2.isdigit():
            R1, flag = get_reg(instr,exclude=["eax","edx"])
            print("\tmov " + R1 + ", " + get_best_location(instr.inp2))
            print("\tidiv " + R1)
        else:
            print("\tidiv " + get_best_location(instr.inp2))

        reg_descriptor["eax"].add(instr.out)
        symbol_table[instr.out].address_descriptor_reg.add("eax")

    def op_modulo(self, instr):
        save_reg_contents("edx")
        save_reg_contents("eax")
        print("\txor edx, edx")
        print("\tmov eax, " + get_best_location(instr.inp1))
        if instr.inp2.isdigit():
            R1, flag = get_reg(instr,exclude=["eax","edx"])
            print("\tmov " + R1 + ", " + get_best_location(instr.inp2))
            print("\tidiv " + R1)
        else:
            print("\tidiv " + get_best_location(instr.inp2))

        reg_descriptor["edx"].add(instr.out)
        symbol_table[instr.out].address_descriptor_reg.add("edx")

    def op_assign(self, instr):
        if instr.inp1 not in symbol_table.keys():   #### For excluding x=y assignments, check if inp1 not in symbol_table
            R1, flag = get_reg(instr, compulsory=False)
            R2 = get_best_location(instr.inp1)
            print("\tmov " + R1 + ", " + R2)

    def op_logical(self, instr):
        # Doing same operation for normal and, or, not and bitwise and, or, not.
        # No special instr for normal logical ops.
        R1, flag = get_reg(instr)
        if flag:
            print("\tmov "+ R1 + ", [" + instr.inp1 + "]")
        R2 = get_best_location(instr.inp2)
        def log_op(x):
            return {
                    "&" : "and ",
                    "|" : "or ",
                    "^" : "xor ",
                    "&&": "and ",
                    "||": "or ",
            }[x]
        if (instr.operation != "~" and instr.operation != "!"):
            print("\t" + log_op(instr.operation) + R1 + ", " + R2)
        else:
            print("\tnot " + R1)

    def op_ifgoto(self, instr):
        pass

    def op_label(self, instr):
        print(instr.label_name + ":")

    def op_call_function(self, instr):
        save_context()
        print("\tcall " + instr.jmp_to_label)

    def op_return(self, instr):
        if instr.is_main_return:
            print("\tmov eax, 0")
        elif instr.out != None:
            save_reg_contents("edi")
            print("\tmov edi, " + get_best_location(instr.out))
        print("\tret")

    def gen_code(self, instr):
        instr_type = instr.instr_type
        if instr.label_to_be_added == True:
            print("label_" + str(instr.line_no) + ":")

        if instr_type == "arithmetic":
            if instr.operation == "+":
                self.op_add(instr)
            elif instr.operation == "-":
                self.op_sub(instr)
            elif instr.operation == "*":
                self.op_mult(instr)
            elif instr.operation == "/":
                self.op_div(instr)
            elif instr.operation == "%":
                self.op_modulo(instr)

        elif instr_type == "logical":
            self.op_logical(instr)

        elif instr_type == "assignment":
            self.op_assign(instr)

        elif instr_type == "ifgoto":
            self.op_ifgoto(instr)

        elif instr_type == "return":
            self.op_return(instr)

        elif instr_type == "label":
            self.op_label(instr)

        elif instr_type == "func_call":
            self.op_call_function(instr)

        elif instr_type == "print_int":
            self.op_print_int(instr)


###################################global generator############################
generator = CodeGenerator()
###################################global generator############################

def next_use(leader, IR_code):
    '''
    This function determines liveness and next
    use information for each statement in basic block

    Input: first line number of basic block
    '''
    generator = CodeGenerator()
    for b_start in range(len(leader) -  1):
        basic_block = IR_code[leader[b_start] - 1:leader[b_start + 1] - 1]
        # for x in basic_block:
            # print(x.line_no)
        # print()
        for instr in reversed(basic_block):
            if is_valid_sym(instr.out):
                instr.per_inst_next_use[instr.out].live = symbol_table[instr.out].live
                instr.per_inst_next_use[instr.out].next_use = symbol_table[instr.out].next_use
                symbol_table[instr.out].live = False
                symbol_table[instr.out].next_use = None

            if is_valid_sym(instr.inp1):
                instr.per_inst_next_use[instr.inp1].live = symbol_table[instr.inp1].live
                instr.per_inst_next_use[instr.inp1].next_use = symbol_table[instr.inp1].next_use
                symbol_table[instr.inp1].live = True
                symbol_table[instr.inp1].next_use = instr.line_no

            if is_valid_sym(instr.inp2):
                instr.per_inst_next_use[instr.inp2].live = symbol_table[instr.inp2].live
                instr.per_inst_next_use[instr.inp2].next_use = symbol_table[instr.inp2].next_use
                symbol_table[instr.inp2].live = True
                symbol_table[instr.inp2].next_use = instr.line_no

        for instr in basic_block:
            generator.gen_code(instr)
        save_context()

if __name__ == "__main__":
    leader, IR_code = read_three_address_code("../test/2_test.csv")
    generator.gen_data_section()
    generator.gen_start_template()
    next_use(leader, IR_code)
