from trainer.code_evaluation import PATCH_CASES, REAL_PATCH_CASES, extract_code


def test_extract_code_prefers_fenced_block() -> None:
    assert extract_code("Here:\n```swift\nprint(\"ok\")\n```") == 'print("ok")'


def test_patch_fixtures_have_distinct_file_names_and_testable_content() -> None:
    assert len({case.filename for case in PATCH_CASES}) == len(PATCH_CASES)
    assert all("unittest" in case.test_code and case.existing_code for case in PATCH_CASES)


def test_real_patch_fixtures_are_distinct_and_have_controlled_mutations() -> None:
    assert len({case.id for case in REAL_PATCH_CASES}) == len(REAL_PATCH_CASES)
    assert all(case.expected_line != case.broken_line for case in REAL_PATCH_CASES)
