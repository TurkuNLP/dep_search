#Thanks, https://www.geeksforgeeks.org/lzw-lempel-ziv-welch-compression-technique/
'''
  *     PSEUDOCODE
  1     Initialize table with single character strings
  2     P = first input character
  3     WHILE not end of input stream
  4          C = next input character
  5          IF P + C is in the string table
  6            P = P + C
  7          ELSE
  8            output the code for P
  9            add P + C to the string table
  10           P = C
  11         END WHILE
  12    output code for P 
  
  
  *    PSEUDOCODE
1    Initialize table with single character strings
2    OLD = first input code
3    output translation of OLD
4    WHILE not end of input stream
5        NEW = next input code
6        IF NEW is not in the string table
7               S = translation of OLD
8               S = S + C
9       ELSE
10              S = translation of NEW
11       output S
12       C = first character of S
13       OLD + C to the string table
14       OLD = NEW
15   END WHILE
  
  '''
  
import struct
from io import BytesIO

def bin_encode(data):
    encoded = struct.pack(">{}H".format(len(data)), *data)
    tmp = struct.pack(">H", len(data))
    encoded = tmp + encoded #appending at the start    
    return encoded
        
def bin_decode(encoded):
    begin = 2
    #try:
    size = struct.unpack(">H", encoded[0:begin])[0]
    return struct.unpack(">{}H".format(size), encoded[begin:])
    #except Exception as e:
    #    return None

def decompress(inp,comp_dict):

    r_comp_dict = {v: k for k, v in comp_dict.items()}

    output = BytesIO()
    for c in bin_decode(inp):
        output.write(r_comp_dict[c])

    return output.getvalue()

def compress(inp,comp_dict):
    #
    if len(comp_dict) < 1:
        for c in range(256):
            comp_dict[bytes([c])] = c

    output = []
    p = bytes([inp[0]])
    for c in inp[1:]:
        c = bytes([c])
        if p+c in comp_dict.keys():
            p = p+c
        else:
            output.append(comp_dict[p])
            if len(comp_dict) < 65535:
                comp_dict[p+c] = len(comp_dict)
            p = c

    if len(p)>0:
        output.append(comp_dict[p])
            
    return bin_encode(output), comp_dict
    
