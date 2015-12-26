from math import *
from keyhac import *

def configure(keymap):
    keymap.clipboard_history.maxnum = 1

    StandardWin.getTopLevelWindow = keymap.getTopLevelWindow

    # treat Muhenkan as U0
    keymap.replaceKey("(29)", 235)
    keymap.defineModifier(235, "User0")

    spaces = Spaces(9)
    bind = keymap.defineWindowKeymap()

    bind["BACKSLASH"] = keymap.command_InputKey("S-UNDERSCORE")

    bind["U0-C-R"] = keymap.command_ReloadConfig

    bind["U0-V"] = keymap.command_MouseButtonClick()

    bind["U0-Return"] = keymap.command_ShellExecute(None, "C:/msys64/msys2_shell.bat", "-", "C:/msys64/")
    bind["U0-S-C"] = focusedWin(lambda win: win.close())
    bind["U0-R"] = keymap.command_ActivateWindow("clnch.exe")

    focusDirCommand = lambda cond: focusedWin(lambda win: win.getNearestByDirection(cond).focus(), True)
    bind["U0-H"] = focusDirCommand(lambda r: r > pi*3/4 or -pi*3/4 > r)
    bind["U0-J"] = focusDirCommand(lambda r: pi/4 < r and r < pi*3/4)
    bind["U0-K"] = focusDirCommand(lambda r: -pi*3/4 < r and r < -pi/4)
    bind["U0-L"] = focusDirCommand(lambda r: -pi/4 < r and r < pi/4)
    bind["U0-I"] = focusedWin(lambda win: win.getNearestWindow().focus(), True)
    bind["U0-O"] = focusedWin(lambda win: win.getOtherScreenWindow().focus(), True)

    bind["U0-S-H"] = focusedWin(lambda win: win.resizeWithGrids(-0.046875, 0))
    bind["U0-S-L"] = focusedWin(lambda win: win.resizeWithGrids( 0.046875, 0))

    bind["U0-S"] = focusedWin(lambda win: win.setBox(win.grid().west))
    bind["U0-F"] = focusedWin(lambda win: win.setBox(win.grid().east))
    bind["U0-S-I"] = focusedWin(lambda win: win.setBox(win.grid()))
    bind["U0-S-O"] = focusedWin(lambda win: win.moveToOtherScreen())

    bind["U0-M"] = focusedWin(lambda win: win.toggleMaximize())

    switchCommand = lambda index: lambda: spaces.switchTo(index)
    switchWithWinCommand = lambda index: focusedWin(lambda win: spaces.switchTo(index, win))

    for i in range(9):
        key = str(i + 1)
        bind["U0-" + key] = switchCommand(i)
        bind["U0-S-" + key] = switchWithWinCommand(i)

    # reactivate binds
    bind["U0-I"]()

class Box:
    # (x: (int, int, int, int)) -> Box
    # (x, y, w, h: int) -> Box
    def __init__(self, x, y = None, w = None, h = None):
        self.rect = x if y is None else (int(x), int(y), int(x + w), int(y + h))
        self.x = self.rect[0]
        self.y = self.rect[1]
        self.w = self.rect[2] - self.rect[0]
        self.h = self.rect[3] - self.rect[1]

    def __eq__(self, other):
        return self.rect == other.rect

    # (b: Box) -> Box
    def intersect(a, b):
        ar = a.rect
        br = b.rect
        x = max(ar[0], br[0])
        y = max(ar[1], br[1])
        xe = min(ar[2], br[2])
        ye = min(ar[3], br[3])
        return Box(x, y, max(xe - x, 0), max(ye - y, 0))

    # () -> (int, int)
    def center(self):
        return (floor((self.rect[0] + self.rect[2]) / 2), floor((self.rect[1] + self.rect[3]) / 2))

    # () -> int
    def size(self):
        return self.w * self.h

    # (b: Box) -> int
    def distanceTo(a, b):
        ac = a.center()
        bc = b.center()
        return abs(ac[0] - bc[0]) + abs(ac[1] - bc[1])

    # (b: Box) -> float
    def radianTo(a, b):
        ac = a.center()
        bc = b.center()
        return atan2(bc[1] - ac[1], bc[0] - ac[0])

    # <T: Box>(ls: T[]) -> T
    def getContainer(self, ls):
        return maxBy(lambda r: self.intersect(r).size(), ls)

class Space:
    # () -> Space
    def __init__(self):
        self.windows = []

    # (withWin: StandardWin) -> void
    def leave(self, withWin = None):
        self.windows = [w for w in StandardWin.allWindows() if not withWin or w != withWin]
        for w in self.windows: w.win.minimize()

    # () -> void
    def enter(self):
        for w in self.windows: w.win.restore()

class Spaces:
    # (count: int) -> void
    def __init__(self, count):
        self.desktops = [Space() for _ in range(count)]
        self.current = 0

    # (index: int, withWin: StandardWin) -> void
    def switchTo(self, index, withWin = None):
        if index == self.current: return
        self.desktops[self.current].leave(withWin)
        self.desktops[index].enter()
        self.current = index

class Screen(Box):
    # (monitorInfo: MonitorInfo) -> Screen
    def __init__(self, monitorInfo):
        Box.__init__(self, monitorInfo[1])
        self.next = self.prev = None

    # () -> StandardWin[]
    def windows(self):
        return [w for w in StandardWin.allWindows() if w.screen() == self]

    allScreensCache = None

    # () -> Screen[]
    @classmethod
    def allScreens(c):
        if c.allScreensCache: return c.allScreensCache
        c.allScreensCache = [c(m) for m in Window.getMonitorInfo()]
        c.link(c.allScreensCache)
        return c.allScreensCache

    # (ls: Screen[]) -> void
    @staticmethod
    def link(ls):
        for i, screen in enumerate(ls):
            screen.next = ls[(i+1) % len(ls)]
            screen.prev = ls[(i-1) % len(ls)]

# TODO vertical separation
class Grid(Box):
    # (screen: Screen, ...) -> Grid
    def __init__(self, screen, *args):
        self.screen = screen
        Box.__init__(self, *args)
        self.north = self.south = self.east = self.west = self

    allGridsCache = None

    # (horizontalCount: int) -> Grid[]
    @classmethod
    def allGrids(c, horizontalCount = 2):
        if c.allGridsCache: return c.allGridsCache
        c.allGridsCache = [p for screen in Screen.allScreens() for p in c.partition(screen, horizontalCount)]
        c.linkHorizontal(c.allGridsCache)
        return c.allGridsCache

    # (screen: Screen, horizontalCount: int) -> Grid[]
    @classmethod
    def partition(c, screen, horizontalCount = 2):
        width = floor(screen.w / horizontalCount)
        return [c(screen, screen.x + i * width, screen.y, width, screen.h) for i in range(horizontalCount)]

    # (ls: Grid[]) -> void
    @staticmethod
    def linkHorizontal(ls):
        for i, grid in enumerate(ls):
            if i < len(ls) - 1: grid.east = ls[i+1]
            if 0 < i: grid.west = ls[i-1]

class StandardWin(Box):
    # (win: Window) -> StandardWin
    def __init__(self, win):
        self.win = win
        Box.__init__(self, win.getRect())

    def __eq__(a, b):
        return a.win == b.win

    # () -> Screen
    def screen(self):
        return self.getContainer(Screen.allScreens())

    # () -> Grid
    def grid(self):
        return self.getContainer(Grid.allGrids())

    # () -> void
    def focus(self):
        popup = self.win.getLastActivePopup()
        if popup: popup.setForeground()

    # () -> void
    def close(self):
        self.win.sendMessage(WM_SYSCOMMAND, SC_CLOSE)

    # (box: Box) -> void
    def setBox(self, box):
        if box: self.win.setRect(box.rect)

    # () -> void
    def toggleMaximize(self):
        if self.win.isMaximized():
            self.win.restore()
        else:
            self.win.maximize()

    # (cond: float -> bool) -> StandardWin
    def getNearestByDirection(self, cond):
        ls = [w for w in StandardWin.allWindows() if w != self and cond(self.radianTo(w))]
        if not ls: return self
        return minBy(lambda w: self.distanceTo(w), ls)

    # () -> StandardWin
    def getNearestWindow(self):
        ls = [w for w in self.screen().windows() if w != self]
        if not ls: return self
        return maxBy(lambda w: self.intersect(w).size() - self.distanceTo(w), ls)

    # () -> StandardWin
    def getOtherScreenWindow(self):
        for w in StandardWin.allWindows():
            if w.screen() != self.screen(): return w
        return self

    # () -> void
    def moveToOtherScreen(self):
        a = self.screen()
        b = self.screen().next
        self.setBox(Box(self.x + (b.x - a.x), self.y + (b.y - a.y), self.w, self.h))

    # (x, y: float) -> void
    def resizeWithGrids(self, x, y):
        x = x * self.screen().w
        y = y * self.screen().h

        g = self.grid()
        self.setBox(Box(
            self.x + x if g.east is g or g.east.screen != g.screen else self.x,
            self.y - y if g.south is g or g.south.screen != g.screen else self.y,
            self.w + x * (1 if g.west is g or g.west.screen != g.screen else -1),
            self.h - y * (1 if g.north is g or g.north.screen != g.screen else -1)
        ))

    getTopLevelWindow = None

    # () -> StandardWin
    @classmethod
    def focusedWindow(c):
        win = c.getTopLevelWindow()
        return c(win) if c.isStandard(win) else None

    # () -> StandardWin[]
    @classmethod
    def allWindows(c):
        ret = []
        def f(win, _):
            if c.isStandard(win): ret.append(c(win))
            return True
        Window.enum(f, None)
        return ret

    # (win: Window) -> bool
    @staticmethod
    def isStandard(win):
        if win is None: return False
        if win.getText() == "" and win.getClassName() != "mintty": return False
        if not win.isVisible() or win.isMinimized(): return False
        # ignore explorer.exe
        if win.getClassName() == "Progman": return False
        # ignore CoreWindow
        if win.getClassName() == "Windows.UI.Core.CoreWindow": return False
        # ignore clnch.exe
        if win.getClassName() == "ClnchWindowClass": return False
        return True

# <T>(f: T -> ordered, T[]) -> T
def maxBy(f, ls):
    return max([(f(a), i, a) for i, a in enumerate(ls)])[2]

# <T>(f: T -> ordered, T[]) -> T
def minBy(f, ls):
    return min([(f(a), i, a) for i, a in enumerate(ls)])[2]

# (f: StandardWin -> void, orFocus: bool) -> () -> void
def focusedWin(f, orFocus = False):
    def ret():
        win = StandardWin.focusedWindow()
        if win:
            f(win)
        elif orFocus:
            for w in StandardWin.allWindows():
                w.focus()
                return
    return ret

