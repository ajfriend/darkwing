# Darkwing

[ajfriend.github.io/darkwing](https://ajfriend.github.io/darkwing/) | [github.com/ajfriend/darkwing](https://github.com/ajfriend/darkwing)

```python
pip install git+https://github.com/ajfriend/darkwing
```

Darkwing is a work-in-progress "dataframe library" that
I use in personal interactive data analysis projects.
(I use quotes because it's really just a light wrapper around the
[DuckDB relational API](https://duckdb.org/docs/api/python/relational_api).)

You can concatenate SQL snippets (often omitting `select *` and `from ...`) to incrementally build up complex queries.
Expressions are evaluated lazily and optimized by DuckDB, so queries are fast, without the need for intermediate tables or data transfers.

This approach results in a mixture of Python and SQL that, I think, is semantically very similar to
[Google's Pipe Syntax for SQL](https://research.google/pubs/sql-has-problems-we-can-fix-them-pipe-syntax-in-sql/):
We can leverage our existing knowledge of SQL, while making a few small changes to make it more ergonomic and composable.

When doing interactive data analysis, I find this approach easier to read and write than
fluent APIs (like in [Polars](https://pola.rs/) or [Ibis](https://ibis-project.org/)) or typical [Pandas](https://pandas.pydata.org/) code.
If some operation is easier in other libraries, Darking makes it straightforward translate between them, either directly or through Apache Arrow.

I'd love to hear any feedback on the approach here, so feel free to reach out through
[Issues](https://github.com/ajfriend/darkwing/issues)
or
[Discussions](https://github.com/ajfriend/darkwing/discussions).
