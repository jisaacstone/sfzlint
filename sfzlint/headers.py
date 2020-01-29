# -*- coding: utf-8 -*-


from collections import defaultdict, abc


class Header(dict):
    '''A dictionary with a name

    used to store opcode pairs under their header tag
    e.g. <global>hivel=25 -> Header<global>{'hivel': 25}
    '''
    def __init__(self, token, *args, **kwargs):
        self.token = token
        self.version = header_meta[self.token]['ver']
        super(Header, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'Header<{self.token}>{super(Header, self).__repr__()}'


class HeaderList(abc.MutableSequence):
    def __init__(self, *headers):
        self.counts = defaultdict(int)
        self._headers = []
        self.extend(headers)

    def __getitem__(self, *args, **kwargs):
        return self._headers.__getitem__(*args, **kwargs)

    def __setitem__(self, key, header):
        old = self._headers[key]
        self._headers[key] = header
        if old.token != header.token:
            self._inc_cnt(header.token)
            self.counts[old.token] -= 1

    def __delitem__(self, key):
        old = self._headers[key]
        self._headers.__delitem__[key]
        self.counts[old.token] -= 1

    def __len__(self):
        return sum(self.counts.values())

    def insert(self, pos, item):
        self._inc_cnt(item)
        self._headers.insert(pos, item)

    def _inc_cnt(self, header):
        self.counts[header.token] += 1


header_meta = {
    'region': {'ver': 'v1'},
    'group': {'ver': 'v1'},
    'control': {'ver': 'v2'},
    'global': {'ver': 'v2'},
    'curve': {'ver': 'v2'},
    'effect': {'ver': 'v2'},
    'master': {'ver': 'aria'},
    'midi': {'ver': 'aria'},
}
