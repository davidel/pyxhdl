import collections

from .utils import *


class _Phi:

  def __init__(self, parent):
    self._parent = parent
    self._phid = dict()

  def set_version(self, name, ver):
    cver = self._phid.get(name, 0)
    if cver >= ver:
      fatal(f'New version must be greater: {cver} >= {ver}')

    self._phid[name] = ver

  def get_version(self, name):
    ver = self._phid.get(name, 0)
    # The root Phi does not generate new versions, only collects commits.
    if ver == 0 and self._parent is not None:
      pphi = self._parent
      while pphi is not None:
        ver = pphi._phid.get(name, 0)
        if ver > 0:
          break

        pphi = pphi._parent

      ver += 1
      self._phid[name] = ver

    return ver

  def cur_version(self, name):
    pphi = self
    while pphi is not None:
      ver = pphi._phid.get(name, 0)
      if ver > 0:
        return ver

      pphi = pphi._parent

    return 0

  def __len__(self):
    return len(self._phid)

  def __iter__(self):
    return iter(self._phid.items())


class Phis:

  def __init__(self):
    self._phis = [_Phi(None)]

  @staticmethod
  def versioned_name(name, ver):
    return f'{name}_{ver}' if ver else name

  @property
  def top_phi(self):
    return self._phis[-1]

  def push_phi(self):
    phi = _Phi(self.top_phi)
    self._phis.append(phi)

    return phi

  def pop_phi(self):
    return self._phis.pop()

  def get_version(self, name):
    return self.top_phi.get_version(name)

  def cur_version(self, name):
    return self.top_phi.cur_version(name)

  def commit(self, commits):
    cphi = self.top_phi
    for name, cver in commits.items():
      cphi.set_version(name, cver)

  def flush(self, branches_phis, assign_fn):
    commits = collections.defaultdict(int)
    for bphi in branches_phis:
      for name, ver in bphi:
        commits[name] = max(commits[name], ver)

    for bphi in branches_phis:
      for name, cver in commits.items():
        bver = bphi.cur_version(name)
        if cver > bver:
          # Assign FROM (bver), TO (cver) versions.
          assign_fn(bphi, name, bver, cver)

    self.commit(commits)

  def load_var(self, name):
    ver = self.cur_version(name)
    return Phis.versioned_name(name, ver)

  def store_var(self, name):
    ver = self.get_version(name)
    return Phis.versioned_name(name, ver)

  def __len__(self):
    return len(self._phis)




# def load_var(name):
#   vname = phis.load_var(name)
#   # Load vname
#   ...


# def handle_assign(name, value):
#   var = load_var(name)
#   if isinstance(var, Value):
#     vname = phis.store_var(name)
#     # Assign vname = value
#     ...


# def put_assign(place, name, from_ver, to_ver):
#   from_name = Phis.versioned_name(name, from_ver)
#   to_name = Phis.versioned_name(name, to_ver)
#   # Emit an assigment to_name = from_name
#   ...



# def handle_if(node):
#   emit_if_cond(node)

#   iphi = phis.push_phi()
#   icode = emit_if_body(node)
#   pif = emit_placement()
#   phis.pop_phi()

#   ephi = phis.push_phi()
#   ecode = emit_else_body(node)
#   pelse = emit_placement()
#   phis.pop_phi()

#   fdist = {id(iphi): pif, id(ephi): pelse}

#   def fassign(phi, name, from_ver, to_ver):
#     place = fdist[id(phi)]
#     put_assign(place, name, from_ver, to_ver)

#   phis.flush((iphi, ephi), fassign)

