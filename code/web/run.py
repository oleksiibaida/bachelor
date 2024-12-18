from app import app


if __name__=='__main__':
    # init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
    # app.run(debug=True, host='127.0.0.1', port=3000)