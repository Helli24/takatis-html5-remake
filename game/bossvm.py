"""Translate the end-boss routine of Takatis.exe (0x4036d0) into JavaScript.

The routine is unoptimised debug code built from a small set of x86 and x87 instructions. Every instruction
becomes one JavaScript statement; jumps become a loop around a switch over the jump targets. Memory is emulated
byte-exact by the runtime in template.html (sections .rdata/.data of the EXE are preloaded), calls into the rest of
the game go to handlers there (shots, sounds, particles, rendering, blits, pixel collision).
"""
import capstone
from capstone import x86

START, END = 0x4036d0, 0x4086e1   # up to and including the final ret

# callee-cleaned argument bytes (thiscall/stdcall); everything else is cdecl and cleaned by the caller
CALLEE_POP = {0x401195: 32, 0x40105a: 12, 0x40113b: 16, 0x42f26b: 4, 0x42ef25: 4, 0x4010c3: 8}
VCALL_POP = {0x1c: 24, 0x28: 28}   # IDirectDrawSurface7::BltFast, IDirect3DDevice7::Clear (this + args)

R32 = {'eax', 'ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp', 'esp'}
R8L = {'al': 'eax', 'bl': 'ebx', 'cl': 'ecx', 'dl': 'edx'}
R8H = {'ah': 'eax', 'bh': 'ebx', 'ch': 'ecx', 'dh': 'edx'}
R16 = {'ax': 'eax', 'bx': 'ebx', 'cx': 'ecx', 'dx': 'edx'}


class Gen:
    def __init__(self, md, code, base):
        self.md, self.code, self.base = md, code, base
        self.insns = list(md.disasm(code, base))

    def reg(self, r):
        return self.md.reg_name(r)

    def addr(self, op):
        m = op.mem
        parts = []
        if m.base:
            parts.append(self.reg(m.base))
        if m.index:
            parts.append(f'{self.reg(m.index)}*{m.scale}')
        if m.disp or not parts:
            parts.append(str(m.disp))
        return '(' + '+'.join(parts) + ')|0' if len(parts) > 1 else parts[0]

    def rd(self, op):
        if op.type == x86.X86_OP_IMM:
            v = op.imm & 0xffffffff
            return str(v - (1 << 32) if v & 0x80000000 else v)
        if op.type == x86.X86_OP_REG:
            n = self.reg(op.reg)
            if n in R32:
                return n
            if n in R8L:
                return f'({R8L[n]}&255)'
            if n in R8H:
                return f'(({R8H[n]}>>8)&255)'
            if n in R16:
                return f'({R16[n]}&65535)'
            raise ValueError(n)
        a = self.addr(op)
        return {1: f'V.r8({a})', 2: f'V.r16({a})', 4: f'V.r32({a})'}[op.size]

    def wr(self, op, val):
        if op.type == x86.X86_OP_REG:
            n = self.reg(op.reg)
            if n in R32:
                return f'{n}={val};'
            if n in R8L:
                r = R8L[n]
                return f'{r}=({r}&-256)|(({val})&255);'
            if n in R16:
                r = R16[n]
                return f'{r}=({r}&-65536)|(({val})&65535);'
            raise ValueError(n)
        a = self.addr(op)
        return {1: f'V.w8({a},{val});', 2: f'V.w16({a},{val});', 4: f'V.w32({a},{val});'}[op.size]

    def sext(self, expr, size):
        return {1: f'(({expr})<<24>>24)', 2: f'(({expr})<<16>>16)', 4: f'(({expr})|0)'}[size]

    def fmem(self, op):
        a = self.addr(op)
        return f'V.rf({a})' if op.size == 4 else f'V.rd({a})'

    def translate(self):
        targets = {START}
        for i in self.insns:
            if i.group(capstone.CS_GRP_JUMP) and i.operands[0].type == x86.X86_OP_IMM:
                targets.add(i.operands[0].imm)
        out = []
        for i in self.insns:
            if i.address in targets:
                out.append(f'case {i.address}:')
            out.append(self.one(i))
        return out

    def one(self, i):
        m, ops = i.mnemonic, i.operands
        S = lambda k: self.sext(k, ops[0].size)
        if m in ('mov',):
            return self.wr(ops[0], self.rd(ops[1]))
        if m == 'movsx':
            return self.wr(ops[0], self.sext(self.rd(ops[1]), ops[1].size))
        if m == 'lea':
            return self.wr(ops[0], self.addr(ops[1]))
        if m == 'push':
            return f'esp=(esp-4)|0;V.w32(esp,{self.rd(ops[0])});'
        if m == 'pop':
            return f'{self.wr(ops[0], "V.r32(esp)")}esp=(esp+4)|0;'
        if m in ('add', 'sub', 'cmp', 'and', 'or', 'xor', 'test'):
            a, b = S(self.rd(ops[0])), self.sext(self.rd(ops[1]), ops[0].size)
            f = {'add': 'ADD', 'sub': 'SUB', 'cmp': 'SUB', 'and': 'AND', 'or': 'OR', 'xor': 'XOR', 'test': 'AND'}[m]
            s = f'r=F.{f}({a},{b},{ops[0].size});'
            if m in ('cmp', 'test'):
                return s
            if m == 'xor' and ops[0].type == x86.X86_OP_REG and ops[1].type == x86.X86_OP_REG and ops[0].reg == ops[1].reg:
                return s + self.wr(ops[0], '0')
            return s + self.wr(ops[0], 'r')
        if m in ('inc', 'dec', 'neg'):
            return f'r=F.{m.upper()}({S(self.rd(ops[0]))},{ops[0].size});' + self.wr(ops[0], 'r')
        if m == 'imul':
            if len(ops) == 3:
                return self.wr(ops[0], f'Math.imul({self.rd(ops[1])},{self.rd(ops[2])})')
            if len(ops) == 2:
                return self.wr(ops[0], f'Math.imul({self.rd(ops[0])},{self.rd(ops[1])})')
        if m == 'cdq':
            return 'edx=eax<0?-1:0;'
        if m == 'idiv':
            return f'{{const d={self.rd(ops[0])},q=Math.trunc(eax/d);edx=(eax-q*d)|0;eax=q|0;}}'
        if m == 'rep stosd':
            return 'while(ecx){V.w32(edi,eax);edi=(edi+4)|0;ecx=(ecx-1)|0;}'
        if i.group(capstone.CS_GRP_JUMP):
            t = ops[0].imm
            cond = {'jmp': 'true', 'je': 'F.z', 'jne': '!F.z', 'jl': 'F.s!==F.o', 'jge': 'F.s===F.o',
                    'jg': '!F.z&&F.s===F.o', 'jle': 'F.z||F.s!==F.o', 'jns': '!F.s', 'js': 'F.s',
                    'jb': 'F.c', 'jae': '!F.c', 'ja': '!F.c&&!F.z', 'jbe': 'F.c||F.z'}[m]
            if cond == 'true':
                return f'pc={t};continue;'
            return f'if({cond}){{pc={t};continue;}}'
        if m == 'call':
            op = ops[0]
            if op.type == x86.X86_OP_IMM:
                a = op.imm
                pop = CALLEE_POP.get(a, 0)
                return f'r=V.call({a},esp,ecx);if(r!==undefined)eax=r;' + (f'esp=(esp+{pop})|0;' if pop else '')
            d = op.mem.disp
            return f'V.vcall({d},esp);esp=(esp+{VCALL_POP[d]})|0;'
        if m == 'ret':
            return 'return;'
        # x87
        if m == 'fld':
            if ops[0].type == x86.X86_OP_REG:
                return f'fp.push(fp[fp.length-1-{self.reg(ops[0].reg)[3]}]);'
            return f'fp.push({self.fmem(ops[0])});'
        if m == 'fild':
            return f'fp.push({self.rd(ops[0])});'
        if m in ('fst', 'fstp'):
            pop = 'fp.pop();' if m == 'fstp' else ''
            if ops[0].type == x86.X86_OP_REG:
                k = int(self.reg(ops[0].reg)[3])
                return f'fp[fp.length-1-{k}]=fp[fp.length-1];' + pop
            a = self.addr(ops[0])
            w = 'wf' if ops[0].size == 4 else 'wd'
            return f'V.{w}({a},fp[fp.length-1]);' + pop
        if m in ('fadd', 'fsub', 'fmul', 'fdiv', 'fdivr', 'fsubr'):
            if len(ops) == 1 and ops[0].type == x86.X86_OP_MEM:
                v = self.fmem(ops[0])
                e = {'fadd': f'T+{v}', 'fsub': f'T-{v}', 'fmul': f'T*{v}', 'fdiv': f'T/{v}',
                     'fdivr': f'{v}/T', 'fsubr': f'{v}-T'}[m]
                return f'{{const T=fp[fp.length-1];fp[fp.length-1]={e};}}'
            if len(ops) == 2 and ops[0].type == x86.X86_OP_REG and ops[1].type == x86.X86_OP_REG:
                d, s = int(self.reg(ops[0].reg)[3]), int(self.reg(ops[1].reg)[3])
                D, Sr = f'fp[fp.length-1-{d}]', f'fp[fp.length-1-{s}]'
                e = {'fadd': f'{D}+{Sr}', 'fsub': f'{D}-{Sr}', 'fmul': f'{D}*{Sr}', 'fdiv': f'{D}/{Sr}',
                     'fdivr': f'{Sr}/{D}', 'fsubr': f'{Sr}-{D}'}[m]
                return f'{D}={e};'
        if m in ('faddp', 'fmulp'):
            k = int(self.reg(ops[0].reg)[3]) if ops else 1
            o = '+' if m == 'faddp' else '*'
            return f'{{const T=fp.pop();fp[fp.length-{k}]=fp[fp.length-{k}]{o}T;}}'
        if m == 'fchs':
            return 'fp[fp.length-1]=-fp[fp.length-1];'
        if m == 'fcomp':
            return f'F.fcom(fp.pop(),{self.fmem(ops[0])});'
        if m == 'fnstsw':
            return 'eax=(eax&-65536)|F.sw;'
        raise NotImplementedError(f'{i.address:x} {m} {i.op_str}')


def translate(img, image_base):
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    g = Gen(md, img[START - image_base:END - image_base], START)
    body = g.translate()
    return ('// End-boss routine of Takatis.exe (0x4036d0), translated to JavaScript by game/bossvm.py at build time.\n'
            'function bossAsm(V,F,fp){let eax=0,ebx=0,ecx=0,edx=0,esi=0,edi=0,ebp=0,esp=V.esp0,r=0,pc=' + str(START) + ';\n'
            'for(;;)switch(pc){\n' + '\n'.join(body) + '\ndefault:throw new Error("boss pc "+pc.toString(16));}}\n')
