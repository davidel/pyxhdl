import functools


_IS_HDL = '_is_hdl'
_HDL_ARGS = '_hdl_args'


def hdl(func):
  @functools.wraps(func)
  def wrapper(*args, **kwargs):
    return func(*args, **kwargs)

  set_hdl_function(wrapper)

  return wrapper


def hdl_process(**hwargs):
  def decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
      return func(*args, **kwargs)

    set_hdl_function(wrapper)
    setattr(wrapper, _HDL_ARGS, hwargs)

    return wrapper

  return decorator


def set_hdl_function(func):
  setattr(func, _IS_HDL, True)


def is_hdl_function(func):
  return getattr(func, _IS_HDL, False)


def get_hdl_args(func):
  return getattr(func, _HDL_ARGS, None)

