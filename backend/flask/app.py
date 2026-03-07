```python
from flask import Flask, request, jsonify
from backend.database import Database
from backend.config import get_db_url

app = Flask(__name__)

@app.route('/api/data', methods=['GET'])
def get_data():
    locale = request.args.get('locale', 'en')
    db = Database(get_db_url())
    data = db.fetch_one(f"SELECT * FROM news WHERE locale='{locale}'")
    return jsonify({
        'locale': locale,
        'data': data
    })

@app.route('/api/settings', methods=['GET'])
def get_settings():
    locale = request.args.get('locale', 'en')
    # Fetch and return settings based on the locale
    return jsonify({
        'locale': locale,
        'settings': {
            'language': locale
        }
    })

if __name__ == '__main__':
    app.run(debug=True)
```