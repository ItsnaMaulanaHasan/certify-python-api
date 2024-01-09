from flask import Flask, request, abort, jsonify, send_from_directory
import cv2
import os
import datetime
import numpy as np
from PIL import Image
import json
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={
    r"/decrypt": {"origins": "http://localhost:8083"},
    r"/encrypt": {"origins": "http://localhost:8083"},
    r"/get_image/*": {"origins": "http://localhost:8083"}
    })

def data2binary(data):
    if type(data) == str:
        p = ''.join([format(ord(i), '08b')for i in data])
    elif type(data) == bytes or type(data) == np.ndarray:
        p = [format(i, '08b')for i in data]
    return p

@app.route('/encrypt', methods=['POST'])
def encrypt():
    image_file = request.files['image']
    no_field = request.form['no']
    name_field = request.form['name']
    email_field = request.form['email']
    info_field = request.form['info']

    image = cv2.imdecode(np.frombuffer(
        image_file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    json_data = {
        "no": no_field,
        "nama": name_field,
        "email": email_field,
        "info": info_field,
    }

    text_json = json.dumps(json_data)
    text_json += "$t3g0"

    d_index = 0
    b_data = data2binary(text_json)
    len_data = len(b_data)

    for value in image:
        for px in value:
            r, g, b, *other_values = data2binary(px)
            if d_index < len_data:
                px[0] = int(r[:-1] + b_data[d_index])
                d_index += 1
            if d_index < len_data:
                px[1] = int(g[:-1] + b_data[d_index])
                d_index += 1
            if d_index < len_data:
                px[2] = int(b[:-1] + b_data[d_index])
                d_index += 1
            if d_index >= len_data:
                break

    enc_data = image

    assets_folder = "assets"

    if not os.path.exists(assets_folder):
        os.makedirs(assets_folder)

    name = name_field.lower().replace(" ", "_")
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    filename = f"{name}_{current_time}.png"

    encrypted_image_path = os.path.join(assets_folder, filename)

    cv2.imwrite(encrypted_image_path, enc_data)

    return jsonify({"message": "Image encrypted successfully!", "filename": filename})

@app.route('/decrypt', methods=['POST'])
def decrypt():
    image_file = request.files['image']
    stego_image = cv2.imdecode(np.frombuffer(
        image_file.read(), np.uint8), cv2.IMREAD_UNCHANGED)

    bin_data = ""
    for value in stego_image:
        for px in value:
            r, g, b, *other_values = data2binary(px)
            bin_data += r[-1]
            bin_data += g[-1]
            bin_data += b[-1]

    all_bytes = [bin_data[i: i + 8] for i in range(0, len(bin_data), 8)]

    readable_data = ""
    for i in all_bytes:
        readable_data += chr(int(i, 2))
        if readable_data[-5:] == "$t3g0":
            break

    msg = readable_data[:-5]

    return jsonify(msg)

@app.route('/get_image/<filename>')
def get_image(filename):
    try:
        return send_from_directory('assets', filename)
    except FileNotFoundError:
        return jsonify({"error": "File not found"})

if __name__ == '__main__':
    app.run(debug=True)
