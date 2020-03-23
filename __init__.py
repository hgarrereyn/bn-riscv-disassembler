import binaryninja

from .riscv import RISCV
RISCV.register()

RISCV_ELF = 243
binaryninja.BinaryViewType['ELF'].register_arch(
    RISCV_ELF, 
    binaryninja.enums.Endianness.LittleEndian, 
    binaryninja.Architecture['riscv:hacksec']
)
