import unittest
from types import SimpleNamespace

from app.matching import calculate_match


class TestMatching(unittest.TestCase):
    def test_matching_returns_high_score_for_matching_student(self):
        user = SimpleNamespace(
            branch="Computer Science",
            year=3,
            cgpa=8.5,
            skills=[
                SimpleNamespace(skill="python"),
                SimpleNamespace(skill="sql"),
            ],
            preferences=SimpleNamespace(
                roles=["python developer"],
                locations=["mumbai"],
                work_mode="hybrid",
                min_compensation=8000,
            ),
        )

        job = SimpleNamespace(
            min_cgpa=7.0,
            eligible_branches="Computer Science,IT",
            eligible_years="2,3,4",
            skills=[
                SimpleNamespace(skill="python"),
                SimpleNamespace(skill="sql"),
            ],
            title="Python Developer Intern",
            role_type="internship",
            location="Mumbai",
            work_mode="hybrid",
            compensation=12000,
        )

        score, explanation = calculate_match(user, job)

        self.assertGreater(score, 0.7)
        self.assertIn("Eligible", explanation)

    def test_ineligible_cgpa_gets_zero(self):
        user = SimpleNamespace(
            branch="Computer Science",
            year=3,
            cgpa=5.5,
            skills=[],
            preferences=SimpleNamespace(
                roles=[],
                locations=[],
                work_mode="any",
                min_compensation=0,
            ),
        )

        job = SimpleNamespace(
            min_cgpa=7.0,
            eligible_branches="Computer Science",
            eligible_years="3",
            skills=[],
            title="Developer",
            role_type="internship",
            location="Mumbai",
            work_mode="onsite",
            compensation=10000,
        )

        score, _ = calculate_match(user, job)

        self.assertEqual(score, 0)


if __name__ == "__main__":
    unittest.main()
