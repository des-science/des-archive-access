import time
import fitsio
import numpy as np

from des_archive_access.dbfiles import get_des_archive_access_db_conn


def _print_time(t0, nrows):
    print("found %d rows in %f seconds (%f rows/s)" % (nrows, t0, nrows/t0))


def _print_table(columns, rows, t0):
    _print_time(t0, len(rows))
    rows = [
        tuple(str(r) for r in row)
        for row in rows
    ]
    mlens = []
    for i in range(len(columns)):
        mlens.append(max(
            len(cr[i])
            for cr in ([columns] + rows)
        ))
    fmt = ""
    for mlen in mlens:
        fmt += " %-" + str(mlen) + "s"
    fmt = fmt[1:]

    print("\n" + fmt % columns)
    for row in rows:
        print(fmt % row)


def _write_table(columns, curr, fname, t0):
    rows = curr.fetchall()
    _print_time(t0, len(rows))
    if len(rows) > 0:
        descr = []
        for i, col in enumerate(columns):
            if isinstance(rows[0][i], str):
                mlen = max(
                    len(r[i])
                    for r in rows
                )
                mlen = max(mlen, 1)
                descr.append((col, "U%d" % mlen))
            elif isinstance(rows[0][i], int):
                descr.append((col, "i8"))
            elif isinstance(rows[0][i], float):
                descr.append((col, "f8"))
            else:
                raise RuntimeError("Did not recognize type %s" % type(rows[0][i]))
        d = np.array(rows, dtype=descr)
        fitsio.write(fname, d, clobber=True)
    else:
        raise RuntimeError("No data found in query! Cannot write file!")


def parse_and_execute_query(query):
    """Parse and execute a SQL `query`."""
    query = query.replace("\n", " ").strip()

    if "; > " in query:
        query, fname = query.rsplit("; > ", 1)
        query = query.strip()
        fname = fname.strip()
    else:
        fname = None

    conn = get_des_archive_access_db_conn()
    try:
        curr = conn.cursor()
        curr.arraysize = 100
        t0 = time.time()
        curr.execute(query)
        t0 = time.time() - t0
        columns = tuple(d[0] for d in curr.description)
        if fname is not None:
            _write_table(columns, curr, fname, t0)
        else:
            rows = curr.fetchall()
            _print_table(columns, rows, t0)
    finally:
        curr.close()
