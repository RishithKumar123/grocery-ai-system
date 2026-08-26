from sqlalchemy import text


def test_database_connection_execution(db_session):
    """Verifies that SQLAlchemy session factory is functional and executes raw transactional lookups."""
    res = db_session.execute(text("SELECT 1")).scalar()
    assert res == 1
