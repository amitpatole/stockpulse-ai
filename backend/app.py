```python
from flask import Flask
from flask_cors import CORS
from backend.database import Database
from backend.health import health_blueprint

app = Flask(__name__)
CORS(app)

db = Database(db_url=app.config['DB_URL'], db_type=app.config['DB_TYPE'])

app.register_blueprint(health_blueprint, url_prefix='/api')

@app.before_first_request
def setup_database():
    db.migrate_database()

if __name__ == '__main__':
    app.run()
```