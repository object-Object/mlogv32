.global _start
_start:
    la x1, word

    li x2, 0x01020304
    sw x2, 0(x1) # 0x04030201 (67305985)
    ebreak
    
    li x2, 0xab
    sb x2, 0(x1) # 0xab030201 (2869101057)
    ebreak
    sb x2, 1(x1) # 0xabab0201 (2880111105)
    ebreak
    sb x2, 2(x1) # 0xababab01 (2880154369)
    ebreak
    sb x2, 3(x1) # 0xabababab (2880154539)
    ebreak

    li x2, 0xcdef
    sh x2, 0(x1) # 0xefcdabab (4023233451)
    ebreak
    sh x2, 2(x1) # 0xefcdefcd (4023250893)
    ebreak

    li x2, 0x12345678
    sw x2, 0(x1) # 0x78563412 (2018915346)
    ebreak

    sw x2, 1(x1) # misaligned store exception

.section .data
.balign 4
word:
    .word 0x01020304

.balign 4
