import os, errno
import warnings

def deprecated(func):
    """This is a decorator which can be used to mark functions
    as deprecated. It will result in a warning being emmitted
    when the function is used."""
    def newFunc(*args, **kwargs):
        warnings.warn("Call to deprecated function %s." % func.__name__,
                      category=DeprecationWarning)
        return func(*args, **kwargs)
    newFunc.__name__ = func.__name__
    newFunc.__doc__ = func.__doc__
    newFunc.__dict__.update(func.__dict__)
    return newFunc

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def loc(filepath):
    from philharmonic import conf
    new_path = os.path.join(conf.output_folder, os.path.dirname(filepath))
    mkdir_p(new_path)
    return os.path.join(conf.output_folder, filepath)

def common_loc(filepath):
    from philharmonic import conf
    new_path = os.path.join(conf.common_output_folder,
                            os.path.dirname(filepath))
    mkdir_p(new_path)
    return os.path.join(conf.common_output_folder, filepath)

class CommonEqualityMixin(object):

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)
