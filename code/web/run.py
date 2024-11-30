from app import create_app
from app.database import Database
app = create_app()

if __name__=='__main__':
    db = Database()
    # db.create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)