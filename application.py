#!/usr/bin/env python2.7
import json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select

home_page = """<p>- `POST` request at `/temp`
- `GET` request at `/errors`
- `DELETE` request at `/errors`</p>"""
DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'

db = SQLAlchemy()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///temp_error.db"
db.init_app(app)


class TempError(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.String, unique=False, nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def hello_world():
    return home_page


@app.route('/errors', methods=['DELETE', 'GET'])
def errors():
    if request.method == 'DELETE':
        # delete all errors
        db.session.query(TempError).delete()
        db.session.commit()
        return "DELETE action SUCCESS"
    else:
        # show all data strings with errors
        result = db.session.execute(select(TempError.data))
        result_formatted = []
        for row in result:
            result_formatted.append(row[0])
        return jsonify({"errors": result_formatted})


@app.route('/temp', methods=['POST'])
def record_temp():
    data = request.get_data().decode()
    if data:
        data = json.loads(data).get('data', '')
    else:
        data = request.form.get('data', '')
    value_list = data.split(':')
    if len(value_list) != 4:
        # wrong format: not 4 ':' separated strings. Based on the requirement, we are not expecting the input to have :
        return store_error_and_respond(data)
    device_id, epoch_ms, temp_str, temp = value_list
    # check each data_field type
    try:
        device_id = int(device_id)
    except ValueError:
        return store_error_and_respond(data)
    try:
        epoch_ms = int(epoch_ms)
    except ValueError:
        return store_error_and_respond(data)
    if temp_str != "'Temperature'":
        return store_error_and_respond(data)
    try:
        temp = float(temp)
    except ValueError:
        return store_error_and_respond(data)
    # device_id out of bound
    if not 0 <= device_id <= (1 << 31) - 1:
        return store_error_and_respond(data)
    # epoch_ms out of bound
    if not 0 <= epoch_ms <= (1 << 63) - 1:
        return store_error_and_respond(data)
    formatted_time = datetime.fromtimestamp(epoch_ms//1000).strftime(DATETIME_FORMAT)
    if temp > 90:
        return jsonify({"overtemp": True, "device_id": device_id, "formatted_time": formatted_time})
    else:
        return """{"overtemp": false}"""


def store_error_and_respond(data):
    temp_error = TempError(
        data=data,
    )
    db.session.add(temp_error)
    db.session.commit()
    return """{"error": "bad request"}""", 400


if __name__ == "__main__":
    app.run(port=5000)
