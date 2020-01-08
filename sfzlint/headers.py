# -*- coding: utf-8 -*-


from collections import defaultdict, abc


class Header(dict):
    '''A dictionary with a name

    used to store opcode pairs under their header tag
    e.g. <global>hivel=25 -> Header<global>{'hivel': 25}
    '''
    def __init__(self, name, *args, **kwargs):
        self.name = name
        super(Header, self).__init__(*args, **kwargs)

    def __repr__(self):
        return f'Header<{self.name}>{super(Header, self).__repr__()}'


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
        if old.name != header.name:
            self._inc_cnt(header.name)
            self.counts[old.name] -= 1

    def __delitem__(self, key):
        old = self._headers[key]
        self._headers.__delitem__[key]
        self.counts[old.name] -= 1

    def __len__(self):
        return sum(self.counts.values())

    def insert(self, pos, item):
        self._inc_cnt(item)
        self._headers.insert(pos, item)

    def _inc_cnt(self, header):
        if self.counts.get(header.name) and header_meta[header.name]['single']:
            raise AttributeError(f'only one {header.name} header allowed')
        self.counts[header.name] += 1


header_meta = {
    'region': {'ver': 'v1', 'single': False},
    'group': {'ver': 'v1', 'single': False},
    'control': {'ver': 'v2', 'single': True},
    'global': {'ver': 'v2', 'single': True},
    'curve': {'ver': 'v2', 'single': False},
    'effect': {'ver': 'v2', 'single': True},
    'master': {'ver': 'aria', 'single': False},
    'midi': {'ver': 'aria', 'single': True},
}
