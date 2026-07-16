"""pytest 共享配置与 SQLite BigInteger 兼容层。

SQLite 仅对 INTEGER PRIMARY KEY 自增，对 BIGINT PRIMARY KEY 无效。
使用 SQLAlchemy @compiles 装饰器在 SQLite 方言下将 BigInteger 编译为 INTEGER，
使测试中能正确自增主键。
"""

from sqlalchemy import BigInteger
from sqlalchemy.ext.compiler import compiles


@compiles(BigInteger, "sqlite")
def _compile_biginteger_sqlite(element, compiler, **kw):
    """SQLite only auto-increments INTEGER PRIMARY KEY, not BIGINT.  Override. """
    return "INTEGER"
