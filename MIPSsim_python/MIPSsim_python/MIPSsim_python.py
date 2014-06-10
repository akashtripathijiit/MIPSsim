class instructions:
    
    def __init__(self,string):
        self.read_file(string)

    def read_file(self,filename):
        fin = open(filename,'r')
        self.inst_dict_binary = dict()
        temp_address = 128
        for line in fin:
            self.inst_dict_binary[temp_address] = line.strip()
            temp_address += 4
        self.last_address = temp_address - 4
        self.convert_to_assembly()   

    def convert_to_assembly(self):
        #instruction decode
        temp_address = 128
        self.inst_dict = dict()
        f_write = open('disassembly-created.txt','w')
        while temp_address <= self.last_address:
            string = self.inst_dict_binary[temp_address]
            cat_no = self.categorize(string[:3])
            operation = self.opcode(cat_no,string)
            assembly = self.create_assembly(cat_no, operation,string)
            self.inst_dict[temp_address] = assembly
            addr = str(temp_address)
            str_to_write = self.inst_dict_binary[temp_address] + '\t' + addr + '\t' + self.inst_dict[temp_address]
            print(str_to_write, file = f_write)
            temp_address += 4
            if(operation == 'BREAK'):
                break
        
        #Memory allocation
        self.memory_dict = dict()
        while temp_address <= self.last_address:
            self.memory_dict[temp_address] = two_complement(self.inst_dict_binary[temp_address])
            addr = str(temp_address)
            str_to_write = self.inst_dict_binary[temp_address] + '\t' + addr + '\t' + str(self.memory_dict[temp_address])
            print(str_to_write, file = f_write)
            temp_address += 4
        print(self.memory_dict)

        #register allocation
        self.register = dict()
        for i in range(32):
            self.register[i] = 0
        print(self.register)

    def create_assembly(self,cat,op,string):
        if cat == 2:
            rs = str(bin_to_dec(string[3:8]))
            rt = str(bin_to_dec(string[8:13]))
            rd = str(bin_to_dec(string[16:21]))
            return op + ' R' + rd + ', R' + rs + ', R' + rt
        elif cat == 3:
            rs = str(bin_to_dec(string[3:8]))
            rt = str(bin_to_dec(string[8:13]))
            imm = str(two_complement(string[16:32]))
            return op + ' R' + rt + ', R' + rs + ', #' + imm
        else:
            if op == 'BREAK':
                return op
            elif op == 'J':
                add = str(4 * bin_to_dec(string[6:32]))
                return 'J #' + add
            elif op == 'BEQ':
                rs = str(bin_to_dec(string[6:11]))
                rt = str(bin_to_dec(string[11:16]))
                offset = str(4 * two_complement(string[16:32]))
                return op + ' R' + rs + ', R' + rt + ', #' + offset
            elif op == 'BGTZ':
                rs = str(bin_to_dec(string[6:11]))
                offset = str(4 * two_complement(string[16:32]))
                return op + ' R' + rs + ', #' + offset
            elif op == 'SW':
                base = str(bin_to_dec(string[6:11]))
                rt = str(bin_to_dec(string[11:16]))
                offset = str(two_complement(string[16:32]))
                return op + ' R' + rt + ', ' + offset + '(R' + base + ')'
            elif op == 'LW':
                base = str(bin_to_dec(string[6:11]))
                rt = str(bin_to_dec(string[11:16]))
                offset = str(two_complement(string[16:32]))
                return op + ' R' + rt + ', ' + offset + '(R' + base + ')'

    def opcode(self,cat,string):
        if cat == 1:
            op = string[3:6]
            if op == '000':
                return 'J'
            elif op == '010':
                return 'BEQ'
            elif op == '100':
                return 'BGTZ'
            elif op == '101':
                return 'BREAK'
            elif op == '110':
                return 'SW'
            elif op == '111':
                return 'LW'

        elif cat == 2:
            op = string[13:16]
            if op == '000':
                return 'ADD'
            elif op == '001':
                return 'SUB'
            elif op == '010':
                return 'MUL'
            elif op == '011':
                return 'AND'
            elif op == '100':
                return 'OR'
            elif op == '101':
                return 'XOR'
            elif op == '110':
                return 'NOR'

        elif cat == 3:
            op = string[13:16]
            if op == '000':
                return 'ADDI'
            elif op == '001':
                return 'ANDI'
            elif op == '010':
                return 'ORI'
            elif op == '011':
                return 'XORI'
            
    def categorize(self,inp):
        if inp == '000':
            return 1
        elif inp == '110':
            return 2
        elif inp == '111':
            return 3
        else:
            raise Exception('Invalid input')

def bin_to_dec(string):
    length = len(string)
    loop = length
    number = 0
    while loop > 0:
        if string[length - loop] == '1' :
            number += 2**(loop - 1)
        loop -= 1
    return number

def two_complement(string):
    new_string = string[1:]
    length = len(new_string)
        
    if(string [0] == '1'):    
        final_string = new_string.replace('0','2')
        final_string = final_string.replace('1','0')
        final_string = final_string.replace('2','1')
    else:
        final_string = new_string
    loop = length
    number = 0
    while loop > 0:
        if final_string[length - loop] == '1' :
            number += 2**(loop - 1)
        loop -= 1
    if(string[0] == '1'):
        number = (number + 1)*(-1)
    return number    

class inst_fetch:
    def __init__(self, pre_issue):
        self.pre_issue = pre_issue
    
    def process(self, pc, inst):
        self.counter = pc
        count = 0
        while(count < 2 and self.pre_issue.size() < self.pre_issue.maxsize):
            if(inst.inst_dict[self.counter] == 'BREAK'):
                return 0
            else:
                self.pre_issue.enqueue(block(inst.inst_dict[self.counter]))
                count += 1
                self.counter += 4
        return count

class block:
    def __init__(self,inst):
        self.inst = inst
        self.flag = 0

class hardware:
    def __init__(self):
        self.instantiate_buffers()
        self.instantiate_units()

    def instantiate_buffers(self):
        self.pre_issue = Queue(4)
        self.pre_alu = Queue(2)
        self.post_mem = Queue(1)
        self.pre_mem = Queue(1)
        self.post_alu = Queue(1)
    
    def instantiate_units(self):
        self.fetch = inst_fetch(self.pre_issue)

class Queue:
    def __init__(self, maxsize):
        self.items = []
        self.maxsize = maxsize
 
    def isEmpty(self):
        return self.items == []

    def enqueue(self, item):
        if self.size() < self.maxsize:
            self.items.insert(0,item)
        else:
           #raise Exception('queue full')
           pass

    def dequeue(self):
        s = self.size()
        if self.items[s-1].flag == 1:
            return self.items.pop()
        else :
            pass
 
    def size(self):
        return len(self.items)

    def show(self):
        print('[ ',end='')
        for i in self.items:
            print(i.inst,end=', ')
        print(']')

    def refresh(self):
        for i in self.items:
            i.flag = 1
 
def main():
    inst = instructions("sample.txt")
    hw = hardware()
    pc = 128
    while (1):
        res = hw.fetch.process(pc, inst)
        if res == 0:
            break
        elif res == 1:
            pc += 4
        elif res == 2:
            pc += 8
        hw.pre_issue.show()
        hw.pre_issue.dequeue()
        hw.pre_issue.refresh()
    
if __name__ == "__main__":main()