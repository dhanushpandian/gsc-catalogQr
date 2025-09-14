import requests

from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy

import random
import string

import qrcode
import base64
from io import BytesIO

import yaml

with open("config.yml", "r") as config_file:
    config = yaml.safe_load(config_file)

ip_address = config["flask"]["ip_address"]
port = config["flask"]["port"]
base_url = config["flask"]["base_url"]

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pc_parts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db = SQLAlchemy(app)


class PCPartData(db.Model):
    id = db.Column(db.String(10), primary_key=True)  # unique user ID
    cpu_name = db.Column(db.String(100), nullable=False)
    cpu_purchase_date = db.Column(db.String(10), nullable=False)
    cpu_warranty_years = db.Column(db.Integer, nullable=False)

    gpu_name = db.Column(db.String(100), nullable=False)
    gpu_purchase_date = db.Column(db.String(10), nullable=False)
    gpu_warranty_years = db.Column(db.Integer, nullable=False)

    ram_name = db.Column(db.String(100), nullable=False)
    ram_purchase_date = db.Column(db.String(10), nullable=False)
    ram_warranty_years = db.Column(db.Integer, nullable=False)

    motherboard_name = db.Column(db.String(100), nullable=False)
    motherboard_purchase_date = db.Column(db.String(10), nullable=False)
    motherboard_warranty_years = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"PCPartData({self.id}, {self.cpu_name}, {self.gpu_name}, {self.ram_name}, {self.motherboard_name})"


@app.route('/')
def home():
    url = "https://www.gurushreecomputers.com/"
    response = requests.get(url)
    content = response.text
    return render_template('index.html', content=content)


@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':

        user_id = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=10))

        cpu_name = request.form['cpu_name']
        cpu_purchase_date = request.form['cpu_purchase_date']
        cpu_warranty_years = request.form['cpu_warranty_years']

        gpu_name = request.form['gpu_name']
        gpu_purchase_date = request.form['gpu_purchase_date']
        gpu_warranty_years = request.form['gpu_warranty_years']

        ram_name = request.form['ram_name']
        ram_purchase_date = request.form['ram_purchase_date']
        ram_warranty_years = request.form['ram_warranty_years']

        motherboard_name = request.form['motherboard_name']
        motherboard_purchase_date = request.form['motherboard_purchase_date']
        motherboard_warranty_years = request.form['motherboard_warranty_years']

        new_entry = PCPartData(
            id=user_id,
            cpu_name=cpu_name,
            cpu_purchase_date=cpu_purchase_date,
            cpu_warranty_years=cpu_warranty_years,
            gpu_name=gpu_name,
            gpu_purchase_date=gpu_purchase_date,
            gpu_warranty_years=gpu_warranty_years,
            ram_name=ram_name,
            ram_purchase_date=ram_purchase_date,
            ram_warranty_years=ram_warranty_years,
            motherboard_name=motherboard_name,
            motherboard_purchase_date=motherboard_purchase_date,
            motherboard_warranty_years=motherboard_warranty_years
        )

        db.session.add(new_entry)
        db.session.commit()

        url = f'http://{ip_address}:{port}/{user_id}'

        img = qrcode.make(url)

        img_io = BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)

        img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        return render_template('form.html', user_id=user_id, qr_code=img_base64)

    return render_template('form.html')


@app.route('/<user_id>', methods=['GET'])
def user_data(user_id):
    user_data = PCPartData.query.filter_by(id=user_id).first()

    if user_data:
        return render_template('user_data.html', user_data=user_data)
    else:
        return f"User with ID {user_id} not found."


@app.route('/download_qr/<user_id>')
def download_qr(user_id):
    # url = f'http://192.168.0.104:5000/{user_id}'
    url = base_url.format(ip_address=ip_address, port=port, user_id=user_id)
    img = qrcode.make(url)

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name=f"{user_id}_qr.png")


if __name__ == '__main__':
    # Create the database if it doesn't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True, host=ip_address, port=port)
