def get_class(kls):
    """
    Returns an instantiated class object from a fully specified name.
    """
    parts = kls.split(".")
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m