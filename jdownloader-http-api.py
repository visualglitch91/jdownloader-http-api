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
jd.connect(email, password)


def update_device():
    global device
    try:
        jd.update_devices()
        device = jd.get_device(device_name)
    except Exception as e:
        device = None


def get_device():
    if not device:
        update_device()
    return device


update_device()
print(f"Device updated: {device}")


def retry_operation(operation, *args, **kwargs):
    max_retries = 2  # Maximum number of retries
    retry_count = 0

    while retry_count < max_retries:
        try:
            result = operation(*args, **kwargs)
            return result  # If successful, return the result
        except Exception as e:
            print(f"An error occurred: {e}")
            update_device()  # Call update_device() to potentially fix the issue
            retry_count += 1
            print(f"Retrying... Attempt {retry_count}/{max_retries}")

    # If max_retries reached without success, handle or raise an exception
    print("Maximum retries reached. Operation failed.")
    # Handle or raise an exception here
    raise Exception("Maximum retries reached. Operation failed.")


@app.route('/links', methods=['GET'])
def get_links():
    try:
        def get_links_function():
            return get_device().downloads.query_links()

        response = retry_operation(get_links_function)
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': e}), 500


@app.route('/links', methods=['POST'])
def add_link():
    data = request.json
    if 'url' in data:
        try:
            def add_links_function():
                return get_device().linkgrabber.add_links([{
                    "autostart": True,
                    "links": data.get('url'),
                }])

            new_link = retry_operation(add_links_function)
            return jsonify(new_link), 201
        except Exception as e:
            return jsonify({'error': e}), 500
    else:
        return jsonify({'error': 'Invalid request'}), 400


@app.route('/links/delete', methods=['POST'])
def delete_link():
    data = request.json
    if 'ids' in data:
        try:
            def delete_links_function():
                return get_device().downloads.remove_links(link_ids=data.get("ids"))

            retry_operation(delete_links_function)
            return jsonify({success: True}), 200
        except Exception as e:
            return jsonify({'error': e}), 500
    else:
        return jsonify({'error': 'Invalid request'}), 400


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=port)
