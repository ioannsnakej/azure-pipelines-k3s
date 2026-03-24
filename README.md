<h2>Запуск</h2>

source env/bin/activate  
nohup python3 app.py > flask.log 2>&1 &

curl 127.0.0.1:5000
