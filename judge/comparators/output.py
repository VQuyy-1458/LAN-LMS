def compare(actual:bytes,expected:bytes,mode='exact'):
    if mode=='exact':return actual==expected
    if mode!='normalized':raise ValueError('Unknown comparator')
    def normalize(data):
        return b'\n'.join(line.rstrip(b' \t') for line in data.replace(b'\r\n',b'\n').split(b'\n')).rstrip(b'\n')
    return normalize(actual)==normalize(expected)
