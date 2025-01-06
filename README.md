# Flask-App
Simple Flask Application which convert a file from (.pdf) to .mp3 and download it. After that, the record in the database is deleted to optimize space. Deployed on 'pythonanywhere'. 
<img width="1440" alt="text_2_speech" src="https://github.com/bvoytash/Flask-App/assets/99912133/f2da83c7-acdb-41ae-822a-39a6af912058">


## 1. Build Docker image
```
docker build -t flaskapp:1.0.0 . 
```
## 2. Run the container
```
docker run -d -p 8000:8000 flaskapp:1.0.0
```
