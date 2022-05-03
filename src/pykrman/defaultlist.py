# noinspection PyPep8Naming
class defaultlist(list):

    def __init__(self, factory=None):
        """
        List extending automatically to the maximum requested length.
        Keyword Args:
            factory: Function called for every missing index.
        """
        self.__factory = factory or defaultlist.__nonefactory

    @staticmethod
    def __nonefactory():
        return None

    def __fill(self, index):
        missing = index - len(self) + 1
        if missing > 0:
            self += [self.__factory() for idx in range(missing)]

    def __setitem__(self, index, value):
        if isinstance(index, slice):
            self.__setslice(index.start, index.stop, index.step, value)
        else:
            self.__fill(index)
            list.__setitem__(self, index, value)

    def __setslice(self, start, stop, step, value):
        end = max((start or 0, stop or 0, 0))
        step = 1 if step is None else step
        if end:
            self.__fill(end - step)
        start = self.__normidx(start, 0)
        stop = self.__normidx(stop, len(self))
        step = step or 1
        r = defaultlist(factory=self.__factory)
        if isinstance(value, list) and len(value) == len(list(range(start, stop, step))):
            for idx, val in zip(range(start, stop, step), value):
                list.__setitem__(self, idx, val)
        else:
            for idx in range(start, stop, step):
                list.__setitem__(self, idx, value)
        return r

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self.__getslice(index.start, index.stop, index.step)
        else:
            self.__fill(index)
            return list.__getitem__(self, index)

    def __normidx(self, idx, default):
        if idx is None:
            idx = default
        elif idx < 0:
            idx += len(self)
        return idx

    def __getslice(self, start, stop, step):
        end = max((start or 0, stop or 0, 0))
        if end:
            self.__fill(end)
        start = self.__normidx(start, 0)
        stop = self.__normidx(stop, len(self))
        step = step or 1
        r = defaultlist(factory=self.__factory)
        for idx in range(start, stop, step):
            r.append(list.__getitem__(self, idx))
        return r

    def __add__(self, other):
        if isinstance(other, list):
            r = self.copy()
            r += other
            return r
        else:
            return list.__add__(self, other)

    def copy(self):
        """Return a shallow copy of the list. Equivalent to a[:]."""
        r = defaultlist(factory=self.__factory)
        r += self
        return r
