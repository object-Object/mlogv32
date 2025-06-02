.global _start
_start:
    li a0, 0x200000
    li a1, 0xdeadbeef
    sw a1, 0(a0)

    li a2, 0xbabecafe
    call cas

    li a0, 0x200000
    lw a2, 0(a0)

    li a2, 0xabcddcba

    sc.w t0, a2, (a0) # should fail

    lw a3, 0(a0)

    lr.w t0, (a0)
    addi a0, a0, 4
    sc.w t0, a2, (a0) # should fail

    lw a3, 0(a0)

    ebreak

    li a0, 0x200000
    li a1, 0b1010
    amoswap.w a2, a1, (a0)

    lw a2, 0(a0)

loop:
    j loop

    # a0 holds address of memory location
    # a1 holds expected value
    # a2 holds desired value
    # a0 holds return value, 0 if successful, !0 otherwise
cas:
    lr.w t0, (a0) # Load original value.
    bne t0, a1, fail # Doesn't match, so fail.
    sc.w t0, a2, (a0) # Try to update.
    bnez t0, cas # Retry if store-conditional failed.
    li a0, 0 # Set return to success.
    jr ra # Return.
fail:
    li a0, 1 # Set return to failure.
    jr ra # Return.
