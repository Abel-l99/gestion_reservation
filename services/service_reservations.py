from flask import Flask, jsonify, request
import requests
from pymongo import MongoClient
from datetime import datetime
import random
from bson.objectid import ObjectId

app = Flask(__name__)

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['hotel_reservations']
reservations_collection = db['reservations']

def mettre_a_jour_disponibilite_chambre(chambre_id, disponible):
    """Met à jour la disponibilité d'une chambre dans MySQL"""
    try:
        response = requests.put(
            f'http://localhost:5001/chambre/{chambre_id}/disponible',
            json={"disponible": disponible}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur mise à jour chambre {chambre_id}: {e}")
        return False

@app.route('/reserver', methods=['POST'])
def reserver():
    """Faire une nouvelle réservation"""
    try:
        data = request.json
        client_id = data.get('client_id')
        chambre_id = data.get('chambre_id')
        nuits = data.get('nuits', 1)
        
        print(f"📝 Tentative réservation: Client {client_id}, Chambre {chambre_id}, {nuits} nuits")
        
        # 1. Vérifier la chambre
        response_chambre = requests.get(f'http://localhost:5001/chambre/{chambre_id}')
        if response_chambre.status_code != 200:
            return jsonify({"error": "Chambre non trouvée"}), 400
        chambre = response_chambre.json()
        
        if not chambre['disponible']:
            return jsonify({"error": "Chambre déjà occupée"}), 400
        
        # 2. Vérifier le client
        response_client = requests.get(f'http://localhost:5002/client/{client_id}')
        if response_client.status_code != 200:
            return jsonify({"error": "Client non trouvé"}), 400
        client = response_client.json()
        
        # 3. Calculer le prix (avec service prix si disponible)
        try:
            response_prix = requests.post('http://localhost:5004/calculer', json={
                "prix_nuit": chambre['prix'],
                "nuits": nuits
            })
            calcul = response_prix.json()
            prix_total = calcul['total_final']
            remise = calcul.get('remise', '0%')
        except:
            # Fallback si service prix indisponible
            prix_total = chambre['prix'] * nuits
            remise = '0%'
        
        # 4. METTRE À JOUR LA DISPONIBILITÉ (False = occupée)
        if not mettre_a_jour_disponibilite_chambre(chambre_id, False):
            return jsonify({"error": "Impossible de bloquer la chambre"}), 500
        
        # 5. Créer la réservation dans MongoDB
        reservation = {
            "client_info": client,
            "chambre_info": chambre,
            "nuits": nuits,
            "prix_total": prix_total,
            "date_reservation": datetime.now().isoformat(),
            "statut": "en cours",
            "numero_reservation": f"RES{random.randint(1000, 9999)}"
        }
        
        result = reservations_collection.insert_one(reservation)
        reservation_id = str(result.inserted_id)
        
        print(f"✅ Réservation créée: {reservation['numero_reservation']}")
        
        return jsonify({
            "success": True,
            "id_reservation": reservation_id,
            "numero_reservation": reservation['numero_reservation'],
            "message": "Réservation confirmée !",
            "prix_total": prix_total,
            "remise": remise,
            "reservation": reservation
        })
        
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route('/reservations', methods=['GET'])
def get_reservations():
    """Voir toutes les réservations"""
    try:
        reservations = list(reservations_collection.find())
        for resa in reservations:
            resa['_id'] = str(resa['_id'])
        return jsonify(reservations)
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route('/reservations/client/<int:client_id>', methods=['GET'])
def get_reservations_client(client_id):
    """Voir les réservations d'un client"""
    try:
        reservations = list(reservations_collection.find({"client_id": client_id}))
        for resa in reservations:
            resa['_id'] = str(resa['_id'])
        return jsonify(reservations)
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route('/annuler/<reservation_id>', methods=['DELETE'])
def annuler_reservation(reservation_id):
    """Annuler une réservation et libérer la chambre"""
    try:
        # Récupérer la réservation
        reservation = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
        
        if not reservation:
            return jsonify({"error": "Réservation non trouvée"}), 404
        
        # Libérer la chambre (mettre disponible = True)
        if not mettre_a_jour_disponibilite_chambre(reservation['chambre_id'], True):
            return jsonify({"error": "Impossible de libérer la chambre"}), 500
        
        # Supprimer la réservation
        result = reservations_collection.delete_one({"_id": ObjectId(reservation_id)})
        
        if result.deleted_count == 1:
            return jsonify({
                "success": True, 
                "message": f"Réservation annulée - Chambre {reservation['chambre_id']} libérée"
            })
        else:
            return jsonify({"error": "Réservation non trouvée"}), 404
            
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "OK", "service": "Réservations", "database": "MongoDB"})

if __name__ == '__main__':
    print("📅 Service Réservations (MongoDB) → http://localhost:5003")
    print("🗄️  Base: hotel_reservations, Collection: reservations")
    app.run(port=5003, debug=True)