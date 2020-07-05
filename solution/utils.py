def naturals(offset: int = 0):
    n = offset
    while True:
        yield n
        n += 1
