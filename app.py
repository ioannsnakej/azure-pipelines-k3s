from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics
import prometheus_client

app = Flask(__name__)
metrics = PrometheusMetrics(app)

@app.route('/metrics')
def metrics():
  return Response(prometheus_client_latest(), mimetype='text/plain')

@app.route('/')
def hello_world():
  return 'Hello, World!'

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000, debug=True)