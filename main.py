from flask import Flask

app = Flask('SAS Birthdays')


@app.route('/')
def Index():
    return 'hello world'


if __name__ == '__main__':
    app.run(debug=True)
