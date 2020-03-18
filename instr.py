
from binaryninja.function import RegisterInfo, InstructionInfo, InstructionTextToken
from binaryninja.enums import InstructionTextTokenType, BranchType


# binary ninja text helpers
def tI(x): return InstructionTextToken(InstructionTextTokenType.InstructionToken, x)
def tR(x): return InstructionTextToken(InstructionTextTokenType.RegisterToken, x)
def tS(x): return InstructionTextToken(InstructionTextTokenType.OperandSeparatorToken, x)
def tM(x): return InstructionTextToken(InstructionTextTokenType.BeginMemoryOperandToken, x)
def tE(x): return InstructionTextToken(InstructionTextTokenType.EndMemoryOperandToken, x)
def tA(x,d): return InstructionTextToken(InstructionTextTokenType.PossibleAddressToken, x, d)
def tT(x): return InstructionTextToken(InstructionTextTokenType.TextToken, x)
def tN(x,d): return InstructionTextToken(InstructionTextTokenType.IntegerToken, x, d)

REGS = [
    'zero', 'ra', 'sp', 'gp', 'tp',
    't0', 't1', 't2',
    's0', 's1',
    'a0', 'a1', 'a2', 'a3', 'a4', 'a5', 'a6', 'a7',
    's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9', 's10', 's11',
    't3', 't4', 't5', 't6',
    'pc'
]

# compressed registers addressed by 3-bit id's
RVC = [
    's0', 's1', 'a0', 'a1', 
    'a2', 'a3', 'a4', 'a5'
]

def u32(dat):
    x = 0
    x += dat[0]
    x += (dat[1] << 8)
    x += (dat[2] << 16)
    x += (dat[3] << 24)
    return x

def u16(dat):
    x = 0
    x += dat[0]
    x += (dat[1] << 8)
    return x

def bits(x,hi,lo):
    '''bits hi to lo inclusive'''
    return (x >> lo) & ((2 ** (hi - lo + 1)) - 1)

def ext(x,n):
    '''sign extend x as an "n" bit number'''
    if (x >> (n-1)) & 1:
        # invert
        return -((~x)+1)
    else:
        return x

class Instr(object):
    def __init__(self, x):
        self.x = x
        
        self.base = bits(x,1,0)
        self.op = bits(x,6,2)
        self.opcode = bits(x,6,0)

        self.rd = bits(x,11,7)
        self.rs1 = bits(x,19,15)
        self.rs2 = bits(x,24,20)

        self.funct3 = bits(x,14,12)
        self.funct7 = bits(x,31,25)

        # immediate values
        self.imm_i = bits(x,31,20)
        self.imm_s = (bits(x,31,25) << 5) + (bits(x,11,7))
        self.imm_b = (bits(x,12,12) << 12) + (bits(x,7,7) << 11) + (bits(x,30,25) << 5) + (bits(x,11,8))
        self.imm_u = (bits(x,31,12) << 12)
        self.imm_j = (bits(x,31,31) << 20) + (bits(x,19,12) << 12) + (bits(x,20,20) << 11) + (bits(x,30,21) << 1)

        # sign extended immediates
        self.imm_i_ext = ext(self.imm_i, 12)
        self.imm_s_ext = ext(self.imm_s, 12)
        self.imm_b_ext = ext(self.imm_b, 12)
        self.imm_j_ext = ext(self.imm_j, 20)

class CInstr(object):
    def __init__(self, x):
        self.x = x

        self.op = bits(x,1,0)
        
        # 5-bit register id
        self.rd = bits(x,11,7)
        self.rs1 = bits(x,11,7)
        self.rs2 = bits(x,6,2)

        # 3-bit register id
        self.rd_c = bits(x,4,2)
        self.rs1_c = bits(x,9,7)
        self.rs2_c = bits(x,4,2)

        self.funct2 = bits(x,6,5)
        self.funct3 = bits(x,15,13)
        self.funct4 = bits(x,15,12)
        self.funct6 = bits(x,15,10)
        
        # immediate values
        self.imm_ci = (bits(x,12,12) << 5) + (bits(x,6,2))
        self.imm_css = bits(x,12,7)
        self.imm_ciw = bits(x,12,5)
        self.imm_cl = (bits(x,12,10) << 2) + (bits(x,6,5))
        self.imm_cs = (bits(x,12,10) << 2) + (bits(x,6,5))

        self.offset = (bits(x,12,10) << 5) + (bits(x,6,2))
        self.jump_target = bits(x,12,2)


def load_instr(op, v): 
    info = InstructionInfo()
    info.length = 4

    tok = [tI(op), tT(' '), tR(REGS[v.rd]), tS(', '), tM('['), tR(REGS[v.rs1]), tT('+'), tA(hex(v.imm_i_ext), v.imm_i_ext), tE(']')]

    return (tok, info)

def store_instr(op, v): 
    info = InstructionInfo()
    info.length = 4

    tok = [tI(op), tT(' '), tR(REGS[v.rs2]), tS(', '), tM('['), tR(REGS[v.rs1]), tT('+'), tA(hex(v.imm_s_ext), v.imm_s_ext), tE(']')]

    return (tok, info)

def itype_instr(op, v):
    info = InstructionInfo()
    info.length = 4

    tok = [tI(op), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs1]), tS(', '), tN(hex(v.imm_i_ext), v.imm_i_ext)]

    return (tok, info)

def itype_shift_instr(op, v):
    info = InstructionInfo()
    info.length = 4

    tok = [tI(op), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs1]), tS(', '), tN(hex(v.rs2), v.rs2)]

    return (tok, info)

def rtype_instr(op, v):
    info = InstructionInfo()
    info.length = 4
    
    tok = [tI(op), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs1]), tS(', '), tR(REGS[v.rs2])]

    return (tok, info)

def jal(v, addr):
    info = InstructionInfo()
    info.length = 4

    tok = []
    if v.rd == 0:
        tok = [tI('j'), tT(' '), tA(hex(v.imm_j_ext + addr), (v.imm_j_ext + addr))]
        info.add_branch(BranchType.UnconditionalBranch, v.imm_j_ext + addr) 
    elif v.rd == 1:
        tok = [tI('call'), tT(' '), tA(hex(v.imm_j_ext + addr), (v.imm_j_ext + addr))]
        info.add_branch(BranchType.CallDestination, v.imm_j_ext + addr)
    else:
        tok = [tI('jal'), tT(' '), tR(REGS[v.rd]), tS(', '), tA(hex(v.imm_j_ext + addr), (v.imm_j_ext + addr))]
        info.add_branch(BranchType.CallDestination, v.imm_j_ext + addr) 
    
    return (tok, info)

def jalr(v, addr):
    info = InstructionInfo()
    info.length = 4 

    tok = []
    if v.rd == 0:
        tok = [tI('jr'), tT(' '), tR(REGS[v.rs1]), tT('+'), tA(hex(v.imm_i_ext + addr), (v.imm_i_ext + addr))]
        info.add_branch(BranchType.FunctionReturn, v.imm_i_ext + addr) 
    elif v.rd == 1:
        tok = [tI('call'), tT(' '), tR(REGS[v.rs1]), tT('+'), tA(hex(v.imm_i_ext + addr), (v.imm_i_ext + addr))]
        info.add_branch(BranchType.CallDestination, v.imm_i_ext + addr)
    else:
        tok = [tI('jalr'), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs1]), tT('+'), tA(hex(v.imm_i_ext + addr), (v.imm_i_ext + addr))]
        info.add_branch(BranchType.CallDestination, v.imm_i_ext + addr)
    
    return (tok, info)

def lui(v):
    info = InstructionInfo()
    info.length = 4

    tok = [tI('lui'), tT(' '), tR(REGS[v.rd]), tS(', '), tA(hex(v.imm_u), v.imm_u)]
    
    return (tok, info)

def auipc(v, addr):
    info = InstructionInfo()
    info.length = 4

    tok = [tI('auipc'), tT(' '), tR(REGS[v.rd]), tS(', '), tA(hex(v.imm_u + addr), (v.imm_u + addr))]
    
    return (tok, info)

def branch_instr(op, v, addr):
    info = InstructionInfo()
    info.length = 4
    info.add_branch(BranchType.TrueBranch, v.imm_b_ext + addr) 
    info.add_branch(BranchType.FalseBranch, addr + 4)

    tok = [tI(op), tT(' '), tR(REGS[v.rs1]), tS(', '), tR(REGS[v.rs1]), tS(', '), tA(hex(v.imm_b_ext + addr), (v.imm_b_ext + addr))]
    
    return (tok, info)

def simple(op):
    info = InstructionInfo()
    info.length = 4
    
    tok = [tI(op)]
    
    return (tok, info)

def csr(op, v):
    info = InstructionInfo()
    info.length = 4
    
    tok = [tI(op), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs1]), tS(', '), tT('csr_%d' % v.imm_i)]
    
    return (tok, info)

def csr_i(op, v):
    info = InstructionInfo()
    info.length = 4
    
    tok = [tI(op), tT(' '), tR(REGS[v.rd]), tS(', '), tN(str(ext(v.rs1, 5)), ext(v.rs1, 5)), tS(', '), tT('csr_%d' % v.imm_i)]
    
    return (tok, info)

def decode_base(v, addr):
    '''base ISA'''

    if v.op == 0b00000:
        # load
        if   v.funct3 == 0b000: return load_instr('lb', v)
        elif v.funct3 == 0b001: return load_instr('lh', v)
        elif v.funct3 == 0b010: return load_instr('lw', v)
        elif v.funct3 == 0b011: return load_instr('ld', v)
        elif v.funct3 == 0b100: return load_instr('lbu', v)
        elif v.funct3 == 0b101: return load_instr('lhu', v)
        elif v.funct3 == 0b110: return load_instr('lwu', v)
        return load_instr('load?%d' % v.funct3, v)

    elif v.op == 0b00011:
        if   v.funct3 == 0b000: return simple('fence')
        elif v.funct3 == 0b001: return simple('fence.I')
        
    elif v.op == 0b00100:
        # I-type math
        if   v.funct3 == 0b000: return itype_instr('addi', v)
        elif v.funct3 == 0b001: return itype_shift_instr('slli', v)
        elif v.funct3 == 0b010: return itype_instr('slti', v)
        elif v.funct3 == 0b011: return itype_instr('sltiu', v)
        elif v.funct3 == 0b100: return itype_instr('xori', v)
        elif v.funct3 == 0b101:
            if   v.funct7 == 0b0000000: return itype_shift_instr('srli', v)
            elif v.funct7 == 0b0100000: return itype_shift_instr('srai', v)
        elif v.funct3 == 0b110: return itype_instr('ori', v)
        elif v.funct3 == 0b111: return itype_instr('andi', v)
        return itype_instr('itype?%d' % v.funct3, v)

    elif v.op == 0b00101:
        return auipc(v, addr)

    elif v.op == 0b00110:
        if   v.funct3 == 0b000: return itype_instr('addiw', v)
        elif v.funct3 == 0b001: return itype_shift_instr('slliw', v)
        elif v.funct3 == 0b101:
            if   v.funct7 == 0b0000000: return itype_shift_instr('srliw', v)
            elif v.funct7 == 0b0100000: return itype_shift_instr('sraiw', v)

    elif v.op == 0b01000:
        # store
        if   v.funct3 == 0b000: return store_instr('sb', v)
        elif v.funct3 == 0b001: return store_instr('sh', v)
        elif v.funct3 == 0b010: return store_instr('sw', v)
        elif v.funct3 == 0b011: return store_instr('sd', v)
        return store_instr('store?%d' % v.funct3, v)

    elif v.op == 0b01100:
        if v.funct7 & 1:
            # M extension
            if   v.funct3 == 0b000: return rtype_instr('mul', v)
            elif v.funct3 == 0b001: return rtype_instr('mulh', v)
            elif v.funct3 == 0b010: return rtype_instr('mulhsu', v)
            elif v.funct3 == 0b011: return rtype_instr('mulhu', v)
            elif v.funct3 == 0b100: return rtype_instr('div', v)
            elif v.funct3 == 0b101: return rtype_instr('divu', v)
            elif v.funct3 == 0b110: return rtype_instr('rem', v)
            elif v.funct3 == 0b111: return rtype_instr('remu', v)
        else:
            # R-type math
            if   v.funct3 == 0b000:
                if   v.funct7 == 0b0000000: return rtype_instr('add', v)
                elif v.funct7 == 0b0100000: return rtype_instr('sub', v)
            elif v.funct3 == 0b001: return rtype_instr('sll', v)
            elif v.funct3 == 0b010: return rtype_instr('slt', v)
            elif v.funct3 == 0b011: return rtype_instr('sltu', v)
            elif v.funct3 == 0b100: return rtype_instr('xor', v)
            elif v.funct3 == 0b101:
                if   v.funct7 == 0b0000000: return rtype_instr('srl', v)
                elif v.funct7 == 0b0100000: return rtype_instr('sra', v)
            elif v.funct3 == 0b110: return rtype_instr('or', v)
            elif v.funct3 == 0b111: return rtype_instr('xor', v)

    elif v.op == 0b01101:
        return lui(v)

    elif v.op == 0b01110:
        # rv64 extension
        if v.funct7 & 1:
            # M extension
            if   v.funct3 == 0b000: return rtype_instr('mulw', v)
            elif v.funct3 == 0b100: return rtype_instr('divw', v)
            elif v.funct3 == 0b101: return rtype_instr('divuw', v)
            elif v.funct3 == 0b110: return rtype_instr('remw', v)
            elif v.funct3 == 0b111: return rtype_instr('remuw', v)
        else:
            if   v.funct3 == 0b000:
                if   v.funct7 == 0b0000000: return rtype_instr('addw', v)
                elif v.funct7 == 0b0100000: return rtype_instr('subw', v)
            elif v.funct3 == 0b001: return rtype_instr('sllw', v)
            elif v.funct3 == 0b101:
                if   v.funct7 == 0b0000000: return rtype_instr('srlw', v)
                elif v.funct7 == 0b0100000: return rtype_instr('sraw', v)

    elif v.op == 0b11000:
        # branches
        if   v.funct3 == 0b000: return branch_instr('beq', v, addr)
        elif v.funct3 == 0b001: return branch_instr('bne', v, addr)
        elif v.funct3 == 0b100: return branch_instr('blt', v, addr)
        elif v.funct3 == 0b101: return branch_instr('bge', v, addr)
        elif v.funct3 == 0b110: return branch_instr('bltu', v, addr)
        elif v.funct3 == 0b111: return branch_instr('bgeu', v, addr)

    elif v.op == 0b11001:
        return jalr(v, addr)

    elif v.op == 0b11011:
        return jal(v, addr)

    elif v.op == 0b11100:
        if   v.funct3 == 0b000:
            if   v.imm_i == 0b000000000000: return simple('ecall')
            elif v.imm_i == 0b000000000001: return simple('ebreak')

            # privileged:
            if v.funct7 == 0b0000000:
                if v.rs2 == 0b00010: return simple('uret')
            elif v.funct7 == 0b0001000:
                if   v.rs2 == 0b00010: return simple('sret')
                elif v.rs2 == 0b00101: return simple('wfi')
            elif v.funct7 == 0b0011000:
                if v.rs2 == 0b00010: return simple('mret')
            elif v.funct7 == 0b0001001:
                return simple('sfence.vma')
                
        elif v.funct3 == 0b001: return csr('csrrw', v)
        elif v.funct3 == 0b010: return csr('csrrs', v)
        elif v.funct3 == 0b011: return csr('csrrc', v)
        elif v.funct3 == 0b101: return csr_i('csrrwi', v)
        elif v.funct3 == 0b110: return csr_i('csrrsi', v)
        elif v.funct3 == 0b111: return csr_i('csrrci', v)

            


# ------- Compressed extension -------

def c_simple(op):
    info = InstructionInfo()
    info.length = 2

    tok = [tI(op)]
    
    return (tok, info)

def c_addi4spn(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,10,7) << 6) + (bits(x,12,11) << 4) + (bits(x,5,5) << 3) + (bits(x,6,6) << 2)
    
    tok = [tI('c.addi4spn'), tT(' '), tR(RVC[v.rd_c]), tS(', '), tR('sp'), tS(', '), tN(str(imm), imm)]
    
    return (tok, info)

def c_lw(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,5,5) << 6) + (bits(x,12,10) << 3) + (bits(x,6,6) << 2)
    
    tok = [tI('c.lw'), tT(' '), tR(RVC[v.rd_c]), tS(', '), tM('['), tR(RVC[v.rs1_c]), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_ld(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,6,5) << 6) + (bits(x,12,10) << 3)
    
    tok = [tI('c.ld'), tT(' '), tR(RVC[v.rd_c]), tS(', '), tM('['), tR(RVC[v.rs1_c]), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_sw(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,5,5) << 6) + (bits(x,12,10) << 3) + (bits(x,6,6) << 2)
    
    tok = [tI('c.sw'), tT(' '), tR(RVC[v.rs2_c]), tS(', '), tM('['), tR(RVC[v.rs1_c]), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_sd(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,6,5) << 6) + (bits(x,12,10) << 3)
    
    tok = [tI('c.sd'), tT(' '), tR(RVC[v.rs2_c]), tS(', '), tM('['), tR(RVC[v.rs1_c]), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_addi(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 5) + (bits(x,6,2))
    
    tok = [tI('c.addi'), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rd]), tS(', '), tN(hex(imm), imm)]
    
    return (tok, info)

def c_addiw(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 5) + (bits(x,6,2))
    
    tok = [tI('c.addiw'), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rd]), tS(', '), tN(hex(imm), imm)]
    
    return (tok, info)

def c_li(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 5) + (bits(x,6,2))
    
    tok = [tI('c.li'), tT(' '), tR(REGS[v.rd]), tS(', '), tN(hex(imm), imm)]
    
    return (tok, info)

def c_addi16sp(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 9) + (bits(x,4,3) << 7) + (bits(x,5,5) << 6) + (bits(x,2,2) << 5) + (bits(x,6,6) << 4)
    
    tok = [tI('c.addi16sp'), tT(' '), tR('sp'), tS(', '), tN(hex(imm), imm)]
    
    return (tok, info)

def c_lui(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 17) + (bits(x,6,2) << 12)
    
    tok = [tI('c.lui'), tT(' '), tR(REGS[v.rd]), tS(', '), tN(hex(imm), imm)]
    
    return (tok, info)

def c_j(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 11) + (bits(x,8,8) << 10) + (bits(x,10,9) << 8) + (bits(x,6,6) << 7) \
        + (bits(x,7,7) << 6) + (bits(x,2,2) << 5) + (bits(x,11,11) << 4) + (bits(x,5,3) << 1)

    info.add_branch(BranchType.UnconditionalBranch, imm)
    
    tok = [tI('c.j'), tT(' '), tA(hex(imm), imm)]
    
    return (tok, info)

def c_jr(op, v):
    info = InstructionInfo()
    info.length = 2
    
    tok = []
    if v.rs1 == 1 and op == 'c.jr':
        tok = [tI('c.ret')]
        info.add_branch(BranchType.FunctionReturn)
    else:
        tok = [tI(op), tT(' '), tR(REGS[v.rs1])]
        info.add_branch(BranchType.UnresolvedBranch)
    
    return (tok, info)

def c_branch(op, v, addr):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 8) + (bits(x,6,5) << 6) + (bits(x,2,2) << 5) + (bits(x,11,10) << 3) + (bits(x,4,3) << 1)

    target = addr + ext(imm, 8)

    info.add_branch(BranchType.TrueBranch, target)
    info.add_branch(BranchType.FalseBranch, addr + 2)
    
    tok = [tI(op), tT(' '), tR(RVC[v.rs1_c]), tS(', '), tA(hex(target), target)]
    
    return (tok, info)

def c_slli(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,12,12) << 5) + (bits(x,6,2))

    tok = [tI('c.slli'), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rd]), tS(', '), tN(hex(imm), imm)]
    
    return (tok, info)

def c_lwsp(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,3,2) << 6) + (bits(x,12,12) << 5) + (bits(x,6,4) << 2)
    
    tok = [tI('c.lwsp'), tT(' '), tR(REGS[v.rd]), tS(', '), tM('['), tR('sp'), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_ldsp(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,4,2) << 6) + (bits(x,12,12) << 5) + (bits(x,6,5) << 3)
    
    tok = [tI('c.ldsp'), tT(' '), tR(REGS[v.rd]), tS(', '), tM('['), tR('sp'), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_mv(v):
    info = InstructionInfo()
    info.length = 2

    tok = [tI('c.mv'), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs2])]
    
    return (tok, info)

def c_add(v):
    info = InstructionInfo()
    info.length = 2

    tok = [tI('c.add'), tT(' '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rd]), tS(', '), tR(REGS[v.rs2])]
    
    return (tok, info)

def c_swsp(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,8,7) << 6) + (bits(x,12,9) << 2)
    
    tok = [tI('c.swsp'), tT(' '), tR(REGS[v.rs2]), tS(', '), tM('['), tR('sp'), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def c_sdsp(v):
    info = InstructionInfo()
    info.length = 2

    x = v.x
    imm = (bits(x,9,7) << 6) + (bits(x,12,8) << 3)
    
    tok = [tI('c.sdsp'), tT(' '), tR(REGS[v.rs2]), tS(', '), tM('['), tR('sp'), tT('+'), tA(hex(imm), imm), tE(']')]
    
    return (tok, info)

def decode_compressed(v, addr):
    '''C extension'''
    if v.x == 0:
        return c_simple('illegal')

    if   v.op == 0b00:
        if   v.funct3 == 0b000: return c_addi4spn(v)
        elif v.funct3 == 0b001: return c_simple('c.fld') # floating point (FLD)
        elif v.funct3 == 0b010: return c_lw(v)
        elif v.funct3 == 0b011: return c_ld(v)
        elif v.funct3 == 0b100: return None # reserved
        elif v.funct3 == 0b101: return c_simple('c.fsd') # floating point (FSD)
        elif v.funct3 == 0b110: return c_sw(v)
        elif v.funct3 == 0b111: return c_sd(v)
    elif v.op == 0b01:
        if v.funct3 == 0b000: 
            if v.rd == 0b00000: return c_simple('nop')
            else: return c_addi(v)
        elif v.funct3 == 0b001:
            if v.rd != 0b00000: return c_addiw(v)
        elif v.funct3 == 0b010:
            if v.rd != 0b00000: return c_li(v)
        elif v.funct3 == 0b011:
            if v.rd == 0b00010: return c_addi16sp(v)
            elif v.rd != 0b0000: return c_lui(v)
        elif v.funct3 == 0b100:
            return c_simple('<c.math>')
        elif v.funct3 == 0b101: return c_j(v)
        elif v.funct3 == 0b110: return c_branch('c.beqz', v, addr)
        elif v.funct3 == 0b111: return c_branch('c.bnez', v, addr)
    elif v.op == 0b10:
        if v.funct3 == 0b000:
            if v.rd != 0b00000: return c_slli(v)
        elif v.funct3 == 0b001: return c_simple('c.fldsp')
        elif v.funct3 == 0b010:
            if v.rd != 0b00000: return c_lwsp(v)
        elif v.funct3 == 0b011:
            if v.rd != 0b00000: return c_ldsp(v)
        elif v.funct3 == 0b100:
            if bits(v.x,12,12):
                if v.rd == 0b00000: return c_simple('c.ebreak')
                else:
                    if v.rs2 == 0b00000: return c_jr('c.jalr', v)
                    else: return c_add(v)
            else:
                if v.rd != 0b00000:
                    if v.rs2 == 0b00000: return c_jr('c.jr', v)
                    else: return c_mv(v)
        elif v.funct3 == 0b101: return c_simple('c.fsdsp')
        elif v.funct3 == 0b110: return c_swsp(v)
        elif v.funct3 == 0b111: return c_sdsp(v)

    return None


def decode(dat, addr):
    
    if bits(dat[0],1,0) == 0b11:
        if len(dat) < 4: return None

        # base 32 bit instruction
        v = Instr(u32(dat))
        return decode_base(v, addr)
    else:
        if len(dat) < 2: return None

        # compressed 16 bit instruction
        v = CInstr(u16(dat))
        return decode_compressed(v, addr)

    return None
