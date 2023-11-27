import json
import myjdapi
from flask import Flask, jsonify, request

with open('config.json') as f:
    config = json.load(f)

email = config['email']
password = config['password']
device_name = config['device_name']
port = config['port']

device = None
app = Flask(__name__)
jd = myjdapi.Myjdapi()

def get_device():
    global device

    if device is None:
        jd.connect(email, password)
        jd.update_devices()
        device = jd.get_device(device_name)

    return device


@app.route('/links', methods=['GET'])
def get_links():
    global device

    try:
        response = get_device().downloads.query_links()
        return jsonify(response)
    except Exception as e:
        device = None
        return jsonify({'error': e}), 500


@app.route('/links', methods=['POST'])
def add_link():
    global device
    data = request.json
    if 'url' in data:
        try:
            new_link = get_device().linkgrabber.add_links([{
                "autostart": True,
                "links": data.get('url'),
            }])
            return jsonify(new_link), 201
        except Exception as e:
            device = None
            return jsonify({'error': e}), 500
    else:
        return jsonify({'error': 'Invalid request'}), 400


@app.route('/links/delete', methods=['POST'])
def delete_link():
    global device
    data = request.json
    if 'ids' in data:
        try:
            get_device().downloads.remove_links(link_ids=data.get("ids"))
            return jsonify({"success": True}), 200
        except Exception as e:
            device = None
            return jsonify({'error': e}), 500
    else:
        return jsonify({'error': 'Invalid request'}), 400


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=port)
