```python
"""
TickerPulse AI v3.0 - API Blueprints Package
Import all blueprint objects for convenient registration with the Flask app.
"""

from backend.api.stocks import stocks_bp
from backend.api.news import news_bp
from backend.api.analysis import analysis_bp
from backend.api.chat import chat_bp
from backend.api.settings import settings_bp
from backend.api.agents import agents_bp
from backend.api.scheduler_routes import scheduler_bp
from backend.api.comparison import comparison_bp
from backend.api.ai_compare import ai_compare_bp
from backend.api.metrics import metrics_bp

__all__ = [
    'stocks_bp',
    'news_bp',
    'analysis_bp',
    'chat_bp',
    'settings_bp',
    'agents_bp',
    'scheduler_bp',
    'comparison_bp',
    'ai_compare_bp',
    'metrics_bp',
]
```