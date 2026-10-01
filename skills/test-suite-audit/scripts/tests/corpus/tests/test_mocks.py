from unittest import mock

import shop.pricing as pricing


@mock.patch("shop.pricing.round", create=True)
@mock.patch("shop.pricing.sum", create=True)
def test_total_heavily_mocked(mock_sum, mock_round):
    # Planted: five patches; the test checks the mocks more than the code.
    with mock.patch.object(pricing, "discount"), mock.patch.object(pricing, "parse_price"), mock.patch.object(pricing, "format_price"):
        mock_sum.return_value = 3
        mock_round.return_value = 3
        assert pricing.total([1, 2]) == 3
        mock_sum.assert_called_once()


def test_unspecced_mock():
    # Planted: executes no product code; it only exercises a Mock without a spec.
    client = mock.Mock()
    client.fetch.return_value = 5
    assert client.fetch() == 5
