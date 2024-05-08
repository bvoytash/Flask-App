from io import BytesIO
import io
import secrets
import PyPDF2
from socket import gethostname

from flask import Flask, request, redirect, flash, url_for, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask.templating import render_template
from sqlalchemy import LargeBinary, create_engine
from gtts import gTTS

app = Flask(__name__, static_url_path='/static')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.secret_key = secrets.token_hex(16)
ALLOWED_EXTENSIONS = {'pdf'}
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024  # 2 MB


class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(LargeBinary)

    def get_data_as_string(self, encoding='utf-8'):
        if self.data:
            return self.data.decode(encoding)
        else:
            return None


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def text_to_speech(text, language):
    output = gTTS(text=text, lang=language, slow=False)
    audio_content = BytesIO()
    output.write_to_fp(audio_content)
    audio_content.seek(0)
    return audio_content


def extract_data_from_pdf(file):
    file_content = io.BytesIO(file.read())
    pdf_reader = PyPDF2.PdfReader(file_content)
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        text += pdf_reader.pages[page_num].extract_text()
    return text


@app.route('/', methods=["GET", "POST"])
def dashboard():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            if file.content_length > app.config['MAX_CONTENT_LENGTH']:
                flash('File size exceeds the limit')
                return redirect(request.url)

            text = extract_data_from_pdf(file)
            my_bytes = text.encode()

            new_record = Record(data=my_bytes)
            db.session.add(new_record)
            db.session.commit()
            id = new_record.id
            return redirect(url_for('my_list', id=id))
    return render_template("index.html")


@app.route('/my_list/<int:id>')
def my_list(id):
    record = db.session.query(Record).filter_by(id=id).first()
    text = record.get_data_as_string()
    id = record.id
    return render_template('index.html', record=record)


@app.route('/download/<int:id>')
def download(id):
    record = db.session.query(Record).filter_by(id=id).first()
    if not record:
        abort(404)
    text = record.get_data_as_string()
    audio_content = text_to_speech(text, 'en')
    try:
        return send_file(audio_content, as_attachment=True, download_name=f"audio{id}.mp3")
    finally:
        db.session.delete(record)
        db.session.commit()


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    # db.create_all()
    if 'liveconsole' not in gethostname():
        app.run()
