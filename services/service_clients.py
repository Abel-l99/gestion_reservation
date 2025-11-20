from flask import Flask, jsonify
import mysql.connector

app = Flask(__name__)

db_config = {
    'host': 'localhost',
    'user': 'root', 
    'password': '',
    'database': 'service_clients'
}

@app.route('/clients', methods=['GET'])
def get_clients():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM client")
    clients = cursor.fetchall()
    conn.close()
    return jsonify(clients)

@app.route('/client/<int:id>', methods=['GET'])
def get_client(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM client WHERE id_client = %s", (id,))
    client = cursor.fetchone()
    conn.close()
    return jsonify(client) if client else ({"error": "Client non trouvé"}, 404)

if __name__ == '__main__':
    print("👥 Service Clients → http://localhost:5002")
    app.run(port=5002, debug=True)