class SystemStats(object):
    def __init__(self):
        self.uptime = 0.
        self.uptime_idle = 0.
        self.one_minute_load = 0.
        self.five_minute_load = 9.
        self.fifteen_minute_load = 0.
        self.running_threads = 0
        self.total_threads = 0
        self.last_pid = 0
        self.vmstats = {}

class SmapsPermissions(object):
    def __init__(self):
        self.readable = False
        self.writable = False
        self.executable = False
        self.shared = False
        self.private = False

class MemoryRegion(object):
    def __init__(self, free):
        self.free = free
        self.pid = -1
        self.start_addr = 0L
        self.end_addr = 0L
        self.offset = 0L
        self.permissions = SmapsPermissions()
        self.name = ''
        self.rss = 0
        self.pss = 0
        self.shared_clean = 0
        self.shared_dirty = 0
        self.private_clean = 0
        self.private_dirty = 0
        self.referenced = 0
        self.anonymous = 0
        self.anonymous_huge = 0
        self.shared_hugetlb = 0
        self.private_hugetlb = 0
        self.swap = 0
        self.swap_pss = 0
        self.kernel_page_size = 0
        self.mmu_page_size = 0
        self.locked = 0
        self.vm_flags = []

    @property
    def size(self):
        return self.end_addr - self.start_addr

    @property
    def readonly(self):
        return (self.permissions.readable and
                not self.permissions.writable and
                not self.permissions.executable)

    @property
    def rw(self):
        return (self.permissions.readable and
                self.permissions.writable and
                not self.permissions.executable)

    @property
    def rx(self):
        return (self.permissions.readable and
                not self.permissions.writable and
                self.permissions.executable)

    @property
    def rwx(self):
        return (self.permissions.readable and
                self.permissions.writable and
                self.permissions.executable)

    @property
    def ro_shared(self):
        return self.readonly and self.permissions.shared

    @property
    def ro_private(self):
        return self.readonly and self.permissions.private

    @property
    def rw_shared(self):
        return self.rw and self.permissions.shared

    @property
    def rw_private(self):
        return self.rw and self.permissions.private

    @property
    def rx_shared(self):
        return self.rx and self.permissions.shared

    @property
    def rx_private(self):
        return self.rx and self.permissions.private

    @property
    def rwx_shared(self):
        return self.rwx and self.permissions.shared

    @property
    def rwx_private(self):
        return self.rwx and self.permissions.private

    def __lt__(self, other):
        """MemoryRegions are sorted by their position in memory"""
        return self.start_addr < other.start_addr

    def __gt__(self, other):
        """MemoryRegions are sorted by their position in memory"""
        return self.start_addr > other.start_addr


class MemoryStats(object):
    def __init__(self):
        self.maps = []
        self.meminfo = {}

    def append(self, memory_region):
        # Don't sort now, sort when getting an iterator.
        self.maps.append(memory_region)

    def get(self, key, default=None):
        return self.meminfo.get(key, default)

    def __iter__(self):
        # Always return memory regions in sorted order
        self.maps.sort()
        return self.maps

    def __len__(self):
        return len(self.maps)

    def __repr__(self):
        if len(self.maps) == 0:
            return """<MemoryStats: empty>"""
        else:
            self.maps.sort()
            return """<MemoryStats: regions={}, from=0x{:02x}, to=0x{:02x}>""".format(
                len(self.maps), self.maps[0].start_addr, self.maps[-1].end_addr)


class Process(object):
    def __init__(self, pid, argv=[]):
        self.pid = pid
        self.argv = argv
        # Memory maps in the process' address space.
        self.maps = []
        # For documentation of these see parsers/stat.py
        self.comm = ''
        self.minor_faults = 0
        self.major_faults = 0
        self.user_time = 0
        self.system_time = 0
        self.start_time = 0

    @property
    def name(self):
        return self.argv[0]

    @property
    def num_fragments(self):
        return len(self.maps)

    @property
    def pss(self):
        return sum([mem.pss for mem in self.maps])

    @property
    def heap(self):
        return sum([mem.pss for mem in self.maps if mem.name == '[heap]'])

    @property
    def stack(self):
        return sum([mem.pss for mem in self.maps if mem.name == '[stack]'])

    @property
    def ro_shared(self):
        return sum([mem.pss for mem in self.maps
                    if mem.ro_shared
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def ro_private(self):
        return sum([mem.pss for mem in self.maps
                    if mem.ro_private
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def rw_shared(self):
        return sum([mem.pss for mem in self.maps
                    if mem.rw_shared
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def rw_private(self):
        return sum([mem.pss for mem in self.maps
                    if mem.rw_private
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def rx_shared(self):
        return sum([mem.pss for mem in self.maps
                    if mem.rx_shared
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def rx_private(self):
        return sum([mem.pss for mem in self.maps
                    if mem.rx_private
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def rwx_shared(self):
        return sum([mem.pss for mem in self.maps
                    if mem.rwx_shared
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def rwx_private(self):
        return sum([mem.pss for mem in self.maps
                    if mem.rwx_private
                    and mem.name not in ['[heap]', 'stack]']])

    @property
    def shared_clean(self):
        return sum([mem.shared_clean for mem in self.maps])

    @property
    def shared_dirty(self):
        return sum([mem.shared_dirty for mem in self.maps])

    @property
    def private_clean(self):
        return sum([mem.private_clean for mem in self.maps])

    @property
    def private_dirty(self):
        return sum([mem.private_dirty for mem in self.maps])

    @property
    def referenced(self):
        return sum([mem.referenced for mem in self.maps])

    @property
    def anonymous(self):
        return sum([mem.anonymous for mem in self.maps])


class ProcessList(object):
    def __init__(self):
        self.processes = {}

    def get(self, pid):
        try:
            return self.processes[pid]
        except KeyError:
            proc = Process(pid)
            self.processes[pid] = proc
            return proc

    def __len__(self):
        return len(self.processes)

    def __iter__(self):
        for process in self.processes.values():
            yield process
