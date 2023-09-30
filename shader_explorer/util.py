import functools


def future_init(func):
    """Decorator for possibly blocking getters.

    The underlying function should have two yeilds.

    The first yield should be a setup (running a process etc)
    The second yield should block until the result has become available.

    e.g:

        query_proc = subprocess.Popen(...)
        yeild

        query_proc.wait()
        result = ...
        yield result

    Args:
        func (function): Function to wrap.

    Returns:
        object: Result provded by underlying function.
    """
    evaluator = func()

    # first yield, does the setup
    next(evaluator)

    fence = False
    result = None

    @functools.wraps(func)
    def wrapped():
        nonlocal result
        nonlocal evaluator
        nonlocal fence

        if not fence:
            fence = True
            result = next(evaluator)
            del evaluator
        return result

    return wrapped
