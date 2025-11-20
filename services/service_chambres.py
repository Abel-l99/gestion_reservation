from flask import Flask, jsonify, request
import mysql.connector

app = Flask(__name__)

# Configuration avec TA base
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'service_chambres'
}

@app.route('/chambres', methods=['GET'])
def get_chambres():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chambre")
    chambres = cursor.fetchall()
    conn.close()
    return jsonify(chambres)

@app.route('/chambres/disponibles', methods=['GET'])
def get_chambres_disponibles():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chambre WHERE disponible = TRUE")
    chambres = cursor.fetchall()
    conn.close()
    return jsonify(chambres)

@app.route('/chambre/<int:id>', methods=['GET'])
def get_chambre(id):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM chambre WHERE id_chambre = %s", (id,))
    chambre = cursor.fetchone()
    conn.close()
    return jsonify(chambre) if chambre else ({"error": "Chambre non trouvée"}, 404)

# ⭐⭐ AJOUTE CETTE NOUVELLE ROUTE ⭐⭐
@app.route('/chambre/<int:id>/disponible', methods=['PUT'])
def update_disponibilite(id):
    """Met à jour la disponibilité d'une chambre"""
    try:
        data = request.json
        disponible = data.get('disponible')
        
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE chambre SET disponible = %s WHERE id_chambre = %s", 
                      (disponible, id))
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True, 
            "message": f"Chambre {id} mise à jour: disponible = {disponible}"
        })
    except Exception as e:
        return jsonify({"error": f"Erreur MySQL: {str(e)}"}), 500

if __name__ == '__main__':
    print("🏨 Service Chambres → http://localhost:5001")
    app.run(port=5001, debug=True)