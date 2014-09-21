

def bytes_to(byte_value, to, bsize=1024):
    """
    :type byte_value: int
    :type to: str
    :type bsize: int

    convert byte_value to megabytes, etc.

    sample code:
       print('mb= ' + str(bytes_to(314575262000000, 'm')))

    sample output:
       mb= 300002347.946
    """

    if byte_value is None:
        return float(0)

    a = {'k': 1, 'm': 2, 'g': 3, 't': 4, 'p': 5, 'e': 6}
    r = float(byte_value)
    for i in range(a[to]):
        r /= bsize

    return r
