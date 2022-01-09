from array import array

poly = 0xEDB88320
table = array('L')
for byte in range(256):
    crc = 0
    for bit in range(8):
        if (byte ^ crc) & 1:
            crc = (crc >> 1) ^ poly
        else:
            crc >>= 1
        byte >>= 1
    table.append(crc)

def crc32(b) -> int:
    value = 0xffffffff
    for by in b:
            value = table[(by ^ value) & 0xff] ^ (value >> 8)
    return (-1 - value) & 0xffffffff
