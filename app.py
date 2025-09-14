import requests

from flask import Flask, render_template, request, send_file,jsonify,redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import random
import string

import qrcode
import base64
from io import BytesIO
import uuid
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


class PCComponent(db.Model):
    __tablename__ = 'pc_components'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # unique component ID
    build_name = db.Column(db.String(100), nullable=False)  # group components into a build
    generic_name = db.Column(db.String(50), nullable=False)  # CPU, GPU, RAM, etc.
    model_name = db.Column(db.String(100), nullable=False)  # Model name of the component
    purchase_date = db.Column(db.String(10), nullable=False)  # e.g., "2025-09-14"
    warranty_years = db.Column(db.Integer, nullable=False)  # warranty duration in years

    def __repr__(self):
        return f"<PCComponent(id={self.id}, build_name={self.build_name}, generic_name={self.generic_name}, model_name={self.model_name})>"

@app.route('/')
def home():
    url = "https://www.gurushreecomputers.com/"
    response = requests.get(url)
    content = response.text
    return render_template('index.html', content=content)


@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':

        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No data received"}), 400

        # Generate a random ID for every entry
        record_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        # Extract build name
        build_name = data.get("buildName")  # matches your JS key
        components = data.get("components", [])

        # Example of processing data:
        for comp in components:
            generic_name = comp.get("genericName")
            model_name = comp.get("modelName")
            purchase_date = comp.get("purchaseDate")
            warranty_years = int(comp.get("warranty"))
            print(f"Component: {generic_name}, {model_name}, {purchase_date}, {warranty_years}")
            
            new_component = PCComponent(
                build_name=build_name,
                generic_name=generic_name,
                model_name=model_name,
                purchase_date=purchase_date,
                warranty_years=warranty_years
            )
            db.session.add(new_component)

        db.session.commit()
        
        # url = f'http://{ip_address}:{port}/{build_name}'

        # img = qrcode.make(url)

        # img_io = BytesIO()
        # img.save(img_io, 'PNG')
        # img_io.seek(0)

        # img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

        return redirect(url_for('qr_page',  build_name=build_name))

    return render_template('form.html')


@app.route('/qr/<build_name>', methods=['GET'])
def qr_page(build_name):
    url = f'http://{ip_address}:{port}/{build_name}'
    img = qrcode.make(url)

    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    return render_template('qr.html', build_name=build_name, qr_code=img_base64)

@app.route('/download_qr/<build_name>')
def download_qr(build_name):
    # Generate the QR code URL pointing to the user's build page
    url = f'http://{ip_address}:{port}/{build_name}'

    # Create the QR code image
    img = qrcode.make(url)

    # Save the image to an in-memory file
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Send the image as a downloadable file
    return send_file(
        img_io,
        mimetype='image/png',
        as_attachment=True,
        download_name=f"{build_name}_qr.png"
    )
@app.route('/<build_name>', methods=['GET'])
def user_data(build_name):
    user_data = PCComponent.query.filter_by(build_name=build_name).all()

    if user_data:
        return render_template('user_data.html', user_data=user_data)
    else:
        return f"User with ID {build_name} not found."

if __name__ == '__main__':
    # Create the database if it doesn't exist
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
