import pytest
from sqlalchemy import *
from sqlalchemy import testing
from sqlalchemy.testing import (
    eq_,
    fixtures,
)
from sqlalchemy.testing.schema import (
    Column,
    Table,
)


class _UpdateTestBase:
    @classmethod
    def define_tables(cls, metadata):
        cls.schema = "TEST"
        Table(
            "mytable",
            metadata,
            Column("myid", Integer),
            Column("name", String(30)),
            Column("description", String(50)),
            schema=cls.schema,
        )
        Table(
            "myothertable",
            metadata,
            Column("otherid", Integer),
            Column("othername", String(30)),
            schema=cls.schema,
        )
        users = Table(
            "users",
            metadata,
            Column("id", Integer, primary_key=True, test_needs_autoincrement=True),
            Column("name", String(30), nullable=False),
            schema=cls.schema,
        )
        addresses = Table(
            "addresses",
            metadata,
            Column("id", Integer, primary_key=True, test_needs_autoincrement=True),
            Column("user_id", None, ForeignKey(users.c.id)),
            Column("name", String(30), nullable=False),
            Column("email_address", String(50), nullable=False),
            schema=cls.schema,
        )
        Table(
            "dingalings",
            metadata,
            Column("id", Integer, primary_key=True, test_needs_autoincrement=True),
            Column("address_id", None, ForeignKey(addresses.c.id)),
            Column("data", String(30)),
            schema=cls.schema,
        )

    @classmethod
    def fixtures(cls):
        return {
            f"{cls.schema}.users": (
                ("id", "name"),
                (7, "jack"),
                (8, "ed"),
                (9, "fred"),
                (10, "chuck"),
            ),
            f"{cls.schema}.addresses": (
                ("id", "user_id", "name", "email_address"),
                (1, 7, "x", "jack@bean.com"),
                (2, 8, "x", "ed@wood.com"),
                (3, 8, "x", "ed@bettyboop.com"),
                (4, 8, "x", "ed@lala.com"),
                (5, 9, "x", "fred@fred.com"),
            ),
            f"{cls.schema}.dingalings": (
                ("id", "address_id", "data"),
                (1, 2, "ding 1/2"),
                (2, 5, "ding 2/5"),
            ),
        }


@pytest.mark.skipif(
    testing.db.dialect.driver == "turbodbc", reason="not supported by turbodbc"
)
class UpdateTest(_UpdateTestBase, fixtures.TablesTest):
    __backend__ = True

    def test_update_simple(self):
        """test simple update and assert that exasol returns the right rowcount"""
        users = self.tables[f"{self.schema}.users"]
        result = testing.db.execute(
            users.update().values(name="peter").where(users.c.id == 10)
        )
        expected = [(7, "jack"), (8, "ed"), (9, "fred"), (10, "peter")]
        assert result.rowcount == 1
        self._assert_users(users, expected)

    def test_update_simple_multiple_rows_rowcount(self):
        """test simple update and assert that exasol returns the right rowcount"""
        users = self.tables[f"{self.schema}.users"]
        result = testing.db.execute(
            users.update().values(name="peter").where(users.c.id >= 9)
        )
        expected = [(7, "jack"), (8, "ed"), (9, "peter"), (10, "peter")]
        assert result.rowcount == 2
        self._assert_users(users, expected)

    def test_update_executemany(self):
        """test that update with executemany work as well, but rowcount
        is undefined for executemany updates"""
        users = self.tables[f"{self.schema}.users"]

        stmt = (
            users.update()
            .where(users.c.name == bindparam("oldname"))
            .values(name=bindparam("newname"))
        )

        values = [
            {"oldname": "jack", "newname": "jack2"},
            {"oldname": "fred", "newname": "fred2"},
        ]

        result = testing.db.execute(stmt, values)
        expected = [(7, "jack2"), (8, "ed"), (9, "fred2"), (10, "chuck")]
        assert result.rowcount == -1
        self._assert_users(users, expected)

    def _assert_addresses(self, addresses, expected):
        stmt = addresses.select().order_by(addresses.c.id)
        eq_(testing.db.execute(stmt).fetchall(), expected)

    def _assert_users(self, users, expected):
        stmt = users.select().order_by(users.c.id)
        eq_(testing.db.execute(stmt).fetchall(), expected)
