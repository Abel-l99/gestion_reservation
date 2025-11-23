from flask import Flask, jsonify, request
from pymongo import MongoClient
from datetime import datetime
import random
from bson.objectid import ObjectId

app = Flask(__name__)

# Connexion MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['hotel_reservations']
reservations_collection = db['reservations']

@app.route('/reserver', methods=['POST'])
def reserver():
    try:
        data = request.json
        client_id = data.get('client_id')
        chambre_id = data.get('chambre_id')
        nuits = data.get('nuits', 1)
        
        # ✅ Vérifications basiques
        if not client_id or not chambre_id:
            return jsonify({"success": False, "error": "client_id et chambre_id requis"}), 400
        
        # ✅ Calcul prix: accepter prix_total fourni par app_web, sinon défaut
        prix_total = data.get('prix_total')
        if prix_total is None:
            prix_total = 100 * nuits
        
        # ✅ Création réservation
        reservation = {
            "client_id": client_id,
            "chambre_id": chambre_id,
            "nuits": nuits,
            "prix_total": prix_total,
            "date_reservation": datetime.now().isoformat(),
            "statut": "en cours",
            "numero_reservation": f"RES{random.randint(1000, 9999)}"
        }
        
        result = reservations_collection.insert_one(reservation)
        
        return jsonify({
            "success": True, 
            "message": "Réservation créée avec succès",
            "reservation_id": str(result.inserted_id),
            "numero_reservation": reservation['numero_reservation']
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur: {str(e)}"}), 500

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

@app.route('/reservations/client/<client_id>', methods=['GET'])
def get_reservations_client(client_id):
    """Voir les réservations d'un client"""
    try:
        reservations = list(reservations_collection.find({"client_id": client_id}))
        for resa in reservations:
            resa['_id'] = str(resa['_id'])
        return jsonify(reservations)
    except Exception as e:
        return jsonify({"error": f"Erreur: {str(e)}"}), 500

def changer_statut_reservation(reservation_id, nouveau_statut="annulée"):
    """Service interne qui change seulement le statut d'une réservation"""
    try:
        print(f"🔄 Changement statut {reservation_id} → {nouveau_statut}")
        
        reservation = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
        
        if not reservation:
            return {"success": False, "error": "Réservation non trouvée"}
        
        # Vérifier si déjà annulée
        if reservation.get('statut') == 'annulée':
            return {"success": False, "error": "Réservation déjà annulée"}
        
        # Modification du statut
        result = reservations_collection.update_one(
            {"_id": ObjectId(reservation_id)},
            {"$set": {
                "statut": nouveau_statut,
                "date_annulation": datetime.now().isoformat() if nouveau_statut == "annulée" else None
            }}
        )
        
        if result.modified_count == 1:
            success_message = f"✅ Statut changé: {reservation_id} → {nouveau_statut}"
            print(success_message)
            return {
                "success": True, 
                "message": success_message,
                "chambre_id": reservation.get('chambre_id'),
                "numero_reservation": reservation.get('numero_reservation')
            }
        else:
            return {"success": False, "error": "Échec du changement de statut"}
            
    except Exception as e:
        error_message = f"Erreur: {str(e)}"
        print(error_message)
        return {"success": False, "error": error_message}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "OK", "service": "Réservations", "database": "MongoDB"})

@app.route('/reservations/<reservation_id>/statut', methods=['PUT'])
def update_statut_reservation(reservation_id):
    try:
        data = request.json or {}
        nouveau_statut = data.get('statut', 'annulée')
        reservation = reservations_collection.find_one({"_id": ObjectId(reservation_id)})
        if not reservation:
            return jsonify({"success": False, "error": "Réservation non trouvée"}), 404
        result = reservations_collection.update_one(
            {"_id": ObjectId(reservation_id)},
            {"$set": {
                "statut": nouveau_statut,
                "date_annulation": datetime.now().isoformat() if nouveau_statut == "annulée" else None
            }}
        )
        if result.modified_count == 1:
            return jsonify({
                "success": True,
                "chambre_id": reservation.get('chambre_id'),
                "numero_reservation": reservation.get('numero_reservation')
            })
        else:
            return jsonify({"success": False, "error": "Échec du changement de statut"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur: {str(e)}"}), 500

if __name__ == '__main__':
    print("Service Réservations -> http://localhost:5003")
    app.run(port=5003, debug=True)
