import unittest
from app.auth import hash_password, verify_password


class TestAuth(unittest.TestCase):
    def test_password_hashing(self):
        password = "password123"

        hashed = hash_password(password)

        self.assertNotEqual(hashed, password)
        self.assertTrue(verify_password(password, hashed))
        self.assertFalse(verify_password("wrong-password", hashed))


if __name__ == "__main__":
    unittest.main()
