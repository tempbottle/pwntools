import types, sys, functools
from . import termcap

def eval_when(when):
    if isinstance(when, file) or \
      when in ('always', 'never', 'auto', sys.stderr, sys.stdout):
        if   when == 'always':
            return True
        elif when == 'never':
            return False
        elif when == 'auto':
            return sys.stderr.isatty()
        else:
            return when.isatty()
    else:
        raise ValueError('text.when: must be a file-object or "always", "never" or "auto"')

class Module(types.ModuleType):
    def __init__(self):
        self.__file__ = __file__
        self.__name__ = __name__
        self.num_colors = termcap.get('colors', default = 8)
        self.has_bright = self.num_colors >= 16
        self.has_gray = self.has_bright
        self.when = 'auto'
        self._colors = {
            'black': 0,
            'red': 1,
            'green': 2,
            'yellow': 3,
            'blue': 4,
            'magenta': 5,
            'cyan': 6,
            'white': 7,
            }
        self._reset = '\x1b[m'
        self._attributes = {}
        for x, y in [('italic'   , 'sitm'),
                     ('bold'     , 'bold'),
                     ('underline', 'smul'),
                     ('reverse'  , 'rev')]:
            s = termcap.get(y)
            self._attributes[x] = s
        self._cache = {}

    @property
    def when(self):
        return self._when

    @when.setter
    def when(self, val):
        self._when = eval_when(val)

    def _fg_color(self, c):
        return termcap.get('setaf', c) or termcap.get('setf', c)

    def _bg_color(self, c):
        return termcap.get('setab', c) or termcap.get('setb', c)

    def _decorator(self, desc, init):
        def f(self, s, when = None):
            if when:
                if eval_when(when):
                    return init + s + self._reset
                else:
                    return s
            else:
                if self.when:
                    return init + s + self._reset
                else:
                    return s
        setattr(Module, desc, f)
        return functools.partial(f, self)

    def __getattr__(self, desc):
        try:
            ds = desc.replace('gray', 'bright_black').split('_')
            init = ''
            while ds:
                d = ds[0]
                try:
                    init += self._attributes[d]
                    ds.pop(0)
                except KeyError:
                    break
            def c():
                bright = 0
                c = ds.pop(0)
                if c == 'bright':
                    c = ds.pop(0)
                    if self.has_bright:
                        bright = 8
                return self._colors[c] + bright
            if ds:
                if ds[0] == 'on':
                    ds.pop(0)
                    init += self._bg_color(c())
                else:
                    init += self._fg_color(c())
                    if len(ds):
                        assert ds.pop(0) == 'on'
                        init += self._bg_color(c())
            return self._decorator(desc, init)
        except (IndexError, KeyError):
            raise AttributeError("'module' object has no attribute %r" % desc)

    def get(self, desc):
        return self.__getattr__(desc)

tether = sys.modules[__name__]
sys.modules[__name__] = Module()
