import functools


_IS_HDL = '_is_hdl'
_HDL_ARGS = '_hdl_args'


def hdl(func):
  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    return func(*args, **kwargs)

  set_is_hdl(func)
  set_is_hdl(wrapper)

  return wrapper


def hdl_process(**hwargs):
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      return func(*args, **kwargs)

    set_is_hdl(func)
    set_is_hdl(wrapper)
    setattr(wrapper, _HDL_ARGS, hwargs)

    return wrapper

  return decorator


def set_is_hdl(obj):
  setattr(obj, _IS_HDL, True)


def is_hdl_function(func):
  return getattr(func, _IS_HDL, False)


def get_hdl_args(func):
  return getattr(func, _HDL_ARGS, None)

