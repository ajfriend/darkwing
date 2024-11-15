import random
import string

from . import query
from ._get_if_file import _get_if_file

from duckdb import DuckDBPyRelation


class Database:
    """
    Table names must be included **explicitly** when applying a SQL snippet.
    """
    def __init__(self, **tables):
        self.tables = {
            k: Table(v)
            for k,v in tables.items()
        }

    def sql(self, s: str):
        s = _get_if_file(s)
        tables = {k: v.rel for k,v in self.tables.items()}
        rel = query(s, **tables)
        return Table(rel)

    def __getitem__(self, key):
        return self.tables[key].raw

    def _do_one(self, other: 'Any'):
        if other in {'arrow', 'pandas'}:
            return self.hold(kind=other)
        if callable(other):
            return other(self)
        else:
            return self.sql(other)

    def do(self, *others):
        cur = self
        for other in others:
            cur = cur._do_one(other)
        return cur

    def __or__(self, other):
        return self.do(other)
    def __rshift__(self, other):
        return self.do(other)

    # TODO: how best to hide the majority of the surface-level code here so we can have people focus on the core mechanics?
    #   seems like good hygine. most of this stuff is functional, not object-oriented. make that separation clear
    def __repr__(self):
        tables = self._yield_table_lines()
        tables = [
            f'\n    {t}'
            for t in tables
        ]
        tables = ''.join(tables)
        tables = tables or ' None'

        out = 'Database:' + tables

        return out
    
    def _yield_table_lines(self):
        for name, tbl in self.tables.items():
            if isinstance(tbl.raw, str):
                yield f"{name}: '{tbl.raw}'"
            else:
                n = self >> f'select count() from {name}' >> int
                columns = self >> f'select column_name from (describe from {name})' >> list
                yield f'{name}: {n} x {columns}'

    def hold(self, kind='arrow'):
        """
        Materialize the Database as a collection of PyArrow Tables or Pandas DataFrames
        """
        return Database(**{
            name: self >> f'from {name}' >> kind
            for name in self.tables
        })

# TODO: do this with a class decorator instead?
# TODO: move in more shared functionality between the two classes? do/sql, etc.
class RightShiftMeta(type):
    def __rrshift__(cls, other):
        return cls(other)

class Table(metaclass=RightShiftMeta):
    """
    The table name is always included implicitly when applying a SQL snippet.
    """
    def __init__(self, other):
        if isinstance(other, Table):
            self.raw = other.raw
            self.rel = other.rel
        else:
            self.raw = other
            self.rel = _load(other)

    def __repr__(self):
        return repr(self.rel)

    def sql(self, s: str):
        """
        Run a SQL snippet via DuckDB, prepended with `from <table_name>`,
        where `<table_name>` will be a unique and random name to avoid collisions.
        """
        name = '_tlb_' + ''.join(random.choices(string.ascii_lowercase, k=10))
        rel = self.rel.query(name, f'from {name} ' + s)
        return Table(rel)

    # TODO: let it take in multipple arguments
    # TODO: add a bunch of wacky binary operators that the user can optionally use
    def _do_one(self, other: 'Any'):
        if isinstance(other, str):
            s = other.strip()
            if s.startswith('as '):
                s = s[3:]
                d = {s: self}
                return Database(**d)

        if isinstance(other, list):
            return self.do(*other)

        if other in {'arrow', 'pandas'}:
            return self.hold(kind=other)
        if other in {int, str, bool}:
            return self.asitem()
        if other is list:
            return self.aslist()
        if other is dict:
            return self.asdict()
        if callable(other):
            return other(self)
        
        return self.sql(other)

    # TODO: do and do_one is just `eval`. clean it up!
    # TODO: should `eval` just be a separate? we may hit a recursion limit... cool!
    # TODO: we can maybe combine the `eval` for both table and database into a single function
    def do(self, *others):
        cur = self
        for other in others:
            cur = cur._do_one(other)
        return cur

    def __or__(self, other):
        return self.do(other)
    def __rshift__(self, other):
        return self.do(other)

    def df(self):
        return self.rel.df()

    def arrow(self):
        return self.rel.arrow()

    def aslist(self):
        """Transform a df with one row or one column to a list"""
        df = self.df()
        if len(df.columns) == 1:
            col = df.columns[0]
            out = list(df[col])
        elif len(df) == 1:
            out = list(df.loc[0])
        else:
            raise ValueError(f'DataFrame should have a single row or column, but has shape f{df.shape}')

        return out

    def asitem(self):
        """Transform a df with one row and one column to single element"""
        # _insist_single_row(df)
        # _insist_single_col(df)
        return self.aslist()[0]

    def asdict(self):
        """Transform a df with one row to a dict
        """
        # _insist_single_row(df)
        df = self.df()
        return dict(df.iloc[0])

    def hold(self, kind='arrow'):
        """
        Materialize the Table as a PyArrow Table or Pandas DataFrame.
        """
        if kind == 'arrow':
            return self.arrow()
        if kind == 'pandas':
            return self.df()


def _load_string(s) -> DuckDBPyRelation:
    return query(f'select * from "{s}"')

def _load_other(x) -> DuckDBPyRelation:
    return query('select * from x', x=x)

def _load(x) -> DuckDBPyRelation:
    """
    inputs: string of filename, actual file, string of remote file, dataframe, dictionary, polars, pyarrow, filename of database
    """
    # intention: take a pandas, polars, or string/URL and convert it to something that we can register
    # also convert relations from other connections to something we can register.
    # if isinstance(df, Relation):
    #     df = df.arrow()
    if isinstance(x, str):
        return _load_string(x)
    else:
        return _load_other(x)
