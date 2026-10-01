from trainer.evaluation import _order


def test_blind_order_is_deterministic_and_complete() -> None:
    assert _order("evidence") == _order("evidence")
    assert set(_order("accountability")) == {"base", "candidate"}
