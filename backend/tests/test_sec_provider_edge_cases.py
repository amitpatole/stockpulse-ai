"""
Edge case and error handling tests for SECInsiderProvider.
Covers: malformed XML, missing fields, zero/large values, network failures, rate limiting.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from backend.data_providers.sec_insider_provider import SECInsiderProvider, InsiderTransaction


@pytest.fixture
def provider():
    """Create provider instance."""
    return SECInsiderProvider(timeout=30)


class TestParseForm4XmlErrorHandling:
    """Edge cases: malformed XML, missing fields, partial failures."""

    def test_parse_form4_xml_missing_issuer_defaults_empty_company(self, provider):
        """Edge case: issuer element missing → company_name defaults to empty string."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John Doe</rptOwnerName>
                                <rptOwnerTitle>Officer</rptOwnerTitle>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType>
                                    <transactionFormType>P</transactionFormType>
                                </transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>100</value></transactionShares>
                                    <transactionPrice><value>100.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].insider_name == 'John Doe'

    def test_parse_form4_xml_missing_reporting_owner_defaults_unknown(self, provider):
        """Edge case: reporting owner missing → insider_name/title default to 'Unknown'."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer>
                            <company-name>Test Corp</company-name>
                        </issuer>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType>
                                    <transactionFormType>P</transactionFormType>
                                </transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>50</value></transactionShares>
                                    <transactionPrice><value>50.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].insider_name == 'Unknown'
        assert transactions[0].title == 'Unknown'

    def test_parse_form4_xml_malformed_xml_logged_and_returns_empty(self, provider):
        """Error case: malformed XML → logged, returns empty list (not raised)."""
        malformed_xml = "<SEC-DOCUMENT><broken>"

        with patch('backend.data_providers.sec_insider_provider.logger') as mock_logger:
            transactions = provider.parse_form4_xml(malformed_xml, '0000320193', 'AAPL')

            assert transactions == []
            mock_logger.warning.assert_called_once()
            assert "Failed to parse Form 4 XML" in str(mock_logger.warning.call_args)

    def test_parse_form4_xml_no_holding_tables_returns_empty(self, provider):
        """Edge case: Form 4 with no transaction tables → empty list."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer>
                            <company-name>Test</company-name>
                        </issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert transactions == []


class TestTransactionRowParsingBoundaryValues:
    """Edge cases: zero/missing prices, very large values, NULL handling."""

    def test_parse_transaction_zero_shares_valid(self, provider):
        """Edge case: zero shares transaction is valid (not skipped)."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                                <rptOwnerTitle>CEO</rptOwnerTitle>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>P</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>0</value></transactionShares>
                                    <transactionPrice><value>100.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].shares == 0
        assert transactions[0].value == 0.0

    def test_parse_transaction_missing_price_defaults_zero(self, provider):
        """Edge case: missing transactionPrice → price=0.0, value=0."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>P</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>100</value></transactionShares>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].price == 0.0
        assert transactions[0].value == 0.0

    def test_parse_transaction_very_large_value_capped_at_1b(self, provider):
        """Edge case: shares * price > 1B → capped to 1B (prevents overflow)."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>P</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>2000000000</value></transactionShares>
                                    <transactionPrice><value>1000.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].value == 1_000_000_000  # Capped at 1B

    def test_parse_transaction_negative_shares_handled(self, provider):
        """Edge case: negative shares parsed as-is (abs would change semantics)."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>S</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>-100</value></transactionShares>
                                    <transactionPrice><value>100.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].shares == -100


class TestNetworkErrorHandling:
    """Error cases: timeouts, network failures, rate limiting."""

    @patch('backend.data_providers.sec_insider_provider.requests.Session.get')
    def test_get_cik_for_ticker_timeout_returns_none(self, mock_get, provider):
        """Error: network timeout → None returned (not raised)."""
        import requests
        mock_get.side_effect = requests.Timeout("Connection timeout")

        with patch('backend.data_providers.sec_insider_provider.logger') as mock_logger:
            cik = provider.get_cik_for_ticker('AAPL')

            assert cik is None
            mock_logger.warning.assert_called_once()

    @patch('backend.data_providers.sec_insider_provider.requests.Session.get')
    def test_fetch_form4_filings_connection_error_returns_empty(self, mock_get, provider):
        """Error: connection error → empty list returned."""
        import requests
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        with patch('backend.data_providers.sec_insider_provider.logger') as mock_logger:
            filings = provider.fetch_form4_filings('0000320193')

            assert filings == []
            mock_logger.warning.assert_called_once()

    @patch('backend.data_providers.sec_insider_provider.requests.Session.get')
    def test_get_cik_rate_limit_429_returns_none(self, mock_get, provider):
        """Error: 429 rate limit → None returned."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("429 Too Many Requests")
        mock_get.return_value = mock_response

        with patch('backend.data_providers.sec_insider_provider.logger') as mock_logger:
            cik = provider.get_cik_for_ticker('AAPL')

            assert cik is None
            mock_logger.warning.assert_called_once()


class TestSentimentScoringEdgeCases:
    """Sentiment calculation for different transaction types."""

    def test_sentiment_purchase_is_positive_one(self, provider):
        """Purchase transaction type → sentiment = +1.0."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>P</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>100</value></transactionShares>
                                    <transactionPrice><value>100.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert transactions[0].sentiment_score == 1.0

    def test_sentiment_sale_is_negative_one(self, provider):
        """Sale transaction type → sentiment = -1.0."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>S</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>100</value></transactionShares>
                                    <transactionPrice><value>100.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert transactions[0].sentiment_score == -1.0

    def test_sentiment_grant_is_positive_moderate(self, provider):
        """Grant transaction type → sentiment = +0.5 (employee compensation)."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <nonDerivativeTable>
                            <nonDerivativeHolding>
                                <securityTitle><value>Stock</value></securityTitle>
                                <transactionType><transactionFormType>G</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>100</value></transactionShares>
                                    <transactionPrice><value>100.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </nonDerivativeHolding>
                        </nonDerivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert transactions[0].sentiment_score == 0.5

    def test_sentiment_exercise_is_low_positive(self, provider):
        """Exercise transaction type → sentiment = +0.3 (partial bullish signal)."""
        xml = """<?xml version="1.0"?>
        <SEC-DOCUMENT>
            <DOCUMENT>
                <TYPE>4</TYPE>
                <TEXT>
                    <FORM4>
                        <issuer><company-name>Test</company-name></issuer>
                        <reportingOwner>
                            <reportingOwnerId>
                                <rptOwnerName>John</rptOwnerName>
                            </reportingOwnerId>
                        </reportingOwner>
                        <derivativeTable>
                            <derivativeHolding>
                                <securityTitle><value>Stock Option</value></securityTitle>
                                <transactionType><transactionFormType>E</transactionFormType></transactionType>
                                <transactionAmounts>
                                    <transactionShares><value>100</value></transactionShares>
                                    <transactionPrice><value>50.00</value></transactionPrice>
                                </transactionAmounts>
                                <transactionDate><value>2026-03-01</value></transactionDate>
                            </derivativeHolding>
                        </derivativeTable>
                    </FORM4>
                </TEXT>
            </DOCUMENT>
        </SEC-DOCUMENT>
        """

        transactions = provider.parse_form4_xml(xml, '0000320193', 'AAPL')

        assert len(transactions) == 1
        assert transactions[0].sentiment_score == 0.3
        assert transactions[0].is_derivative is True
