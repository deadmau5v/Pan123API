from flask import Flask
from Pan123API import Pan123API

app = Flask(__name__)
pan = Pan123API()

@app.route("/")
def hello():
    return pan.get_file_list()

if __name__ == '__main__':
    app.run(debug=True, port=5000, host="0.0.0.0")