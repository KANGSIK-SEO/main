import unittest

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import Base, enable_sqlite_foreign_keys
from app.models import Book, Loan, User
from app.security import hash_password, verify_password
from app.services.library import LibraryError, borrow_book, return_book


class LibraryServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        event.listen(self.engine, "connect", enable_sqlite_foreign_keys)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(username="tester", password_hash=hash_password("correct-horse"))
        self.book = Book(title="테스트 도서", author="테스트 저자")
        self.db.add_all([self.user, self.book])
        self.db.commit()
        self.db.refresh(self.user)
        self.db.refresh(self.book)

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_password_hash_is_verified_without_storing_plaintext(self):
        hashed = hash_password("correct-horse")
        self.assertNotEqual(hashed, "correct-horse")
        self.assertTrue(verify_password("correct-horse", hashed))
        self.assertFalse(verify_password("wrong", hashed))

    def test_borrow_links_user_and_book_then_return_changes_status(self):
        loan = borrow_book(self.db, self.user, self.book.id)
        loaded = self.db.scalar(select(Loan).where(Loan.id == loan.id))
        self.assertEqual(loaded.user.username, "tester")
        self.assertEqual(loaded.book.title, "테스트 도서")
        self.assertEqual(self.user.loans[0].book, self.book)
        self.assertEqual(loaded.status, "borrowed")

        returned = return_book(self.db, self.user, loan.id)
        self.assertEqual(returned.status, "returned")
        self.assertIsNotNone(returned.returned_at)

    def test_cannot_borrow_book_twice_or_return_another_users_loan(self):
        loan = borrow_book(self.db, self.user, self.book.id)
        other_user = User(username="other", password_hash="unused")
        self.db.add(other_user)
        self.db.commit()
        with self.assertRaises(LibraryError):
            borrow_book(self.db, other_user, self.book.id)
        with self.assertRaises(LibraryError):
            return_book(self.db, other_user, loan.id)

    def test_referenced_user_and_book_cannot_be_deleted(self):
        borrow_book(self.db, self.user, self.book.id)
        self.db.delete(self.user)
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()
        self.db.delete(self.book)
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()


if __name__ == "__main__":
    unittest.main()
