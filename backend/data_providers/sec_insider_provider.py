```python
"""
TickerPulse AI - SEC Insider Provider
Fetches Form 4 filings from SEC EDGAR and parses transaction details.
"""

import logging
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

SEC_EDGAR_BASE = "https://www.sec.gov"
SEC_EDGAR_BROWSE = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar"


@dataclass
class InsiderTransaction:
    """Represents a Form 4 insider transaction"""
    cik: str
    ticker: str
    insider_name: str
    title: str
    transaction_type: str  # purchase, sale, grant, exercise
    shares: int
    price: float
    value: float
    filing_date: datetime
    transaction_date: datetime
    sentiment_score: float
    is_derivative: bool
    filing_url: str
    form4_url: str


class SECInsiderProvider:
    """Fetches and parses SEC Form 4 filings for insider transactions."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TickerPulse AI (educational use)'
        })

    def get_cik_for_ticker(self, ticker: str) -> Optional[str]:
        """Look up CIK for a given ticker symbol.
        
        Parameters
        ----------
        ticker : str
            Stock ticker (e.g., 'AAPL')
            
        Returns
        -------
        str or None
            10-digit CIK with leading zeros, or None if not found
        """
        try:
            params = {
                'action': 'getcompany',
                'company': ticker,
                'type': '',
                'dateb': '',
                'owner': 'exclude',
                'count': 1,
            }
            response = self.session.get(
                SEC_EDGAR_BROWSE,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            # Parse HTML to find CIK link (format: /cgi-bin/browse-edgar?action=getcompany&CIK=0000320193)
            if 'CIK=' in response.text:
                # Extract CIK from URL pattern
                import re
                match = re.search(r'CIK=(\d+)', response.text)
                if match:
                    return match.group(1).zfill(10)
            return None
        except Exception as e:
            logger.warning(f"Failed to lookup CIK for {ticker}: {e}")
            return None

    def fetch_form4_filings(self, cik: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch recent Form 4 filings for a CIK.
        
        Parameters
        ----------
        cik : str
            SEC Central Index Key
        limit : int
            Maximum number of filings to fetch
            
        Returns
        -------
        list
            List of filing info dicts with keys: accession_number, filing_date, company_name
        """
        try:
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': '4',
                'dateb': '',
                'owner': 'exclude',
                'count': limit,
                'search_text': '',
                'rss': '1'
            }
            response = self.session.get(
                SEC_EDGAR_BROWSE,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            # Parse RSS feed
            filings = []
            try:
                root = ET.fromstring(response.content)
                for item in root.findall('.//item'):
                    title = item.findtext('title', '')
                    link = item.findtext('link', '')
                    pub_date = item.findtext('pubDate', '')
                    
                    if '4' in title and link:
                        # Extract accession number from link
                        import re
                        match = re.search(r'(\d{10}-\d{2}-\d{6})', link)
                        accession = match.group(1) if match else None
                        
                        if accession:
                            filings.append({
                                'accession_number': accession,
                                'filing_date': pub_date,
                                'title': title,
                                'link': link,
                            })
            except ET.ParseError as e:
                logger.warning(f"Failed to parse Form 4 RSS for {cik}: {e}")

            return filings
        except Exception as e:
            logger.warning(f"Failed to fetch Form 4 filings for {cik}: {e}")
            return []

    def parse_form4_xml(self, form4_content: str, cik: str, ticker: str) -> List[InsiderTransaction]:
        """Parse Form 4 XML document and extract transactions.
        
        Parameters
        ----------
        form4_content : str
            Raw Form 4 XML document
        cik : str
            SEC Central Index Key
        ticker : str
            Stock ticker
            
        Returns
        -------
        list
            List of InsiderTransaction objects
        """
        transactions = []
        try:
            # Remove namespace for easier parsing
            form4_content = form4_content.replace('xmlns=', 'xmlnamespace=')
            root = ET.fromstring(form4_content)

            # Find header info
            issuer_elem = root.find('.//issuer')
            company_name = issuer_elem.findtext('company-name', '') if issuer_elem else ''

            # Find reporting owner
            reporting_owner = root.find('.//reportingOwner')
            insider_name = ''
            insider_title = ''
            if reporting_owner:
                ro_info = reporting_owner.find('reportingOwnerId')
                if ro_info:
                    insider_name = ro_info.findtext('rptOwnerName', '')
                    insider_title = ro_info.findtext('rptOwnerTitle', '')

            # Find transactions
            form_data = root.find('.//nonDerivativeTable')
            if form_data:
                for row in form_data.findall('.//nonDerivativeHolding'):
                    txn = self._parse_transaction_row(
                        row, cik, ticker, insider_name, insider_title, is_derivative=False
                    )
                    if txn:
                        transactions.append(txn)

            # Also get derivative transactions
            deriv_form = root.find('.//derivativeTable')
            if deriv_form:
                for row in deriv_form.findall('.//derivativeHolding'):
                    txn = self._parse_transaction_row(
                        row, cik, ticker, insider_name, insider_title, is_derivative=True
                    )
                    if txn:
                        transactions.append(txn)

            return transactions
        except Exception as e:
            logger.warning(f"Failed to parse Form 4 XML for {cik}: {e}")
            return []

    def _parse_transaction_row(
        self,
        row: ET.Element,
        cik: str,
        ticker: str,
        insider_name: str,
        insider_title: str,
        is_derivative: bool
    ) -> Optional[InsiderTransaction]:
        """Parse a single transaction row from Form 4."""
        try:
            # Extract security and transaction info
            security = row.findtext('securityTitle/value', '')
            txn_type_elem = row.find('transactionType')
            txn_type = txn_type_elem.findtext('transactionFormType', '') if txn_type_elem else ''

            shares = 0
            shares_elem = row.find('transactionAmounts')
            if shares_elem:
                shares_str = shares_elem.findtext('transactionShares/value', '0')
                try:
                    shares = int(float(shares_str))
                except (ValueError, TypeError):
                    shares = 0

            price = 0.0
            price_elem = row.find('transactionAmounts')
            if price_elem:
                price_str = price_elem.findtext('transactionPrice/value', '0')
                try:
                    price = float(price_str)
                except (ValueError, TypeError):
                    price = 0.0

            value = shares * price
            value = min(value, 1_000_000_000)  # Cap at 1B
            value = max(value, 0)

            # Parse dates
            txn_date_elem = row.find('transactionDate')
            txn_date_str = txn_date_elem.findtext('value', '') if txn_date_elem else ''
            transaction_date = self._parse_date(txn_date_str)

            # Determine transaction type (purchase/sale/grant/exercise)
            transaction_type = self._map_transaction_type(txn_type)
            if not transaction_type:
                return None

            # Calculate sentiment score
            if transaction_type == 'purchase':
                sentiment = 1.0
            elif transaction_type == 'sale':
                sentiment = -1.0
            elif transaction_type == 'grant':
                sentiment = 0.5
            elif transaction_type == 'exercise':
                sentiment = 0.3
            else:
                sentiment = 0.0

            # Weight by shares for magnitude
            if shares > 0:
                sentiment = min(sentiment, 1.0)
                sentiment = max(sentiment, -1.0)

            filing_url = f"{SEC_EDGAR_BASE}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=4"
            form4_url = filing_url

            return InsiderTransaction(
                cik=cik,
                ticker=ticker,
                insider_name=insider_name or 'Unknown',
                title=insider_title or 'Unknown',
                transaction_type=transaction_type,
                shares=shares,
                price=price,
                value=value,
                filing_date=datetime.utcnow(),
                transaction_date=transaction_date,
                sentiment_score=sentiment,
                is_derivative=is_derivative,
                filing_url=filing_url,
                form4_url=form4_url,
            )
        except Exception as e:
            logger.warning(f"Failed to parse transaction row: {e}")
            return None

    def _map_transaction_type(self, form_type: str) -> Optional[str]:
        """Map Form 4 transaction type to our categories."""
        form_type = form_type.upper()
        if form_type in ('P', 'BUY'):
            return 'purchase'
        elif form_type in ('S', 'SELL'):
            return 'sale'
        elif form_type in ('G',):
            return 'grant'
        elif form_type in ('E', 'M'):
            return 'exercise'
        return None

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string in YYYY-MM-DD format."""
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except (ValueError, TypeError):
            return datetime.utcnow()
```