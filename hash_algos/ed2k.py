import hashlib


class ED2KHash(object):
    MAGICLEN = 9728000

    def __init__(self):
        self.hashes = []
        self.pos = 0
        self.md4 = hashlib.new('md4')

    def update(self, data):
        data_len = len(data)
        for d in (data[i:i + ED2KHash.MAGICLEN] for i in range(0, data_len, ED2KHash.MAGICLEN)):
            self._update(d)

    def _update(self, data):
        data_len = len(data)
        assert data_len <= ED2KHash.MAGICLEN

        newpos = self.pos + data_len

        if newpos < ED2KHash.MAGICLEN:
            self.md4.update(data)
            self.pos = newpos
            return
        else:
            prev = data[:ED2KHash.MAGICLEN - self.pos]
            next_val = data[ED2KHash.MAGICLEN - self.pos:]
            self.md4.update(prev)
            self.hashes.append(self.md4.digest())
            self.md4 = hashlib.new('md4')
            self.md4.update(next_val)
            self.pos = len(next_val)
            return

    def digest(self):
        if len(self.hashes) == 0:
            return self.md4.digest()
        else:
            m = hashlib.new('md4')
            newhashes = self.hashes + [self.md4.digest()]
            m.update(b''.join(newhashes))
            return m.digest()