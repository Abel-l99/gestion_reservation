from flask import Flask, render_template_string
import requests

app = Flask(__name__)

# Le CODE HTML de la page web
PAGE_WEB = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hôtel Distributed</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background: rgba(255,255,255,0.95); 
            padding: 30px; 
            border-radius: 15px;
            color: #333;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .service-status { 
            background: #f8f9fa; 
            margin: 15px 0; 
            padding: 20px; 
            border-radius: 10px; 
            border-left: 5px solid #28a745;
        }
        .reservation-box { 
            background: #e8f5e8; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 25px 0;
            border: 2px solid #28a745;
        }
        .online { color: #28a745; font-weight: bold; }
        .offline { color: #dc3545; font-weight: bold; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .communication { background: #e3f2fd; padding: 15px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏨 SYSTÈME HÔTELIER DISTRIBUÉ</h1>
        
        <div class="service-status">
            <h2>📊 ÉTAT DES SERVICES</h2>
            <p>🏨 <strong>Service Chambres:</strong> <span class="{{ classe_chambres }}">{{ statut_chambres }}</span></p>
            <p>👥 <strong>Service Clients:</strong> <span class="{{ classe_clients }}">{{ statut_clients }}</span></p>
            <p>💰 <strong>Service Prix:</strong> <span class="{{ classe_prix }}">{{ statut_prix }}</span></p>
            <p>📅 <strong>Service Réservations:</strong> <span class="{{ classe_reservations }}">{{ statut_reservations }}</span></p>
        </div>
        
        {% if reservation %}
        <div class="reservation-box">
            <h2>🎯 DERNIÈRE RÉSERVATION</h2>
            <p><strong>👤 Client:</strong> {{ reservation.client.prenom }} {{ reservation.client.nom }}</p>
            <p><strong>🏠 Chambre:</strong> {{ reservation.chambre.type }}</p>
            <p><strong>📅 Nuits:</strong> {{ reservation.nuits }}</p>
            <p><strong>💰 Total:</strong> {{ reservation.total }}€ (Remise: {{ reservation.remise }})</p>
            <p><strong>📅 Date:</strong> {{ reservation.date }}</p>
        </div>
        {% endif %}
        
        <div class="communication">
            <h2>🔄 COMMUNICATION ENTRE SERVICES</h2>
            <p>1. 📞 <strong>Service Réservations</strong> → <strong>Service Chambres</strong> : "Chambre disponible ?"</p>
            <p>2. 📞 <strong>Service Réservations</strong> → <strong>Service Clients</strong> : "Client existe ?"</p>
            <p>3. 📞 <strong>Service Réservations</strong> → <strong>Service Prix</strong> : "Calculer le prix final"</p>
            <p>4. ✅ <strong>Service Réservations</strong> : Combine toutes les réponses → <strong>Réservation créée !</strong></p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.location.reload()" style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 5px; cursor: pointer;">
                🔄 Actualiser la page
            </button>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def afficher_dashboard():
    # Teste si chaque service fonctionne
    try:
        requests.get("http://localhost:5001/chambres", timeout=2)
        statut_chambres = "✅ EN LIGNE"
        classe_chambres = "online"
    except:
        statut_chambres = "❌ HORS LIGNE"
        classe_chambres = "offline"
    
    try:
        requests.get("http://localhost:5002/clients", timeout=2)
        statut_clients = "✅ EN LIGNE"
        classe_clients = "online"
    except:
        statut_clients = "❌ HORS LIGNE"
        classe_clients = "offline"
    
    try:
        requests.post("http://localhost:5004/calculer", json={"prix_nuit": 100, "nuits": 2}, timeout=2)
        statut_prix = "✅ EN LIGNE"
        classe_prix = "online"
    except:
        statut_prix = "❌ HORS LIGNE"
        classe_prix = "offline"
    
    try:
        reservations_data = requests.get("http://localhost:5003/reservations", timeout=2)
        statut_reservations = "✅ EN LIGNE"
        classe_reservations = "online"
        # Récupère la dernière réservation
        reservations = reservations_data.json()
        derniere_reservation = list(reservations.values())[-1] if reservations else None
    except:
        statut_reservations = "❌ HORS LIGNE"
        classe_reservations = "offline"
        derniere_reservation = None
    
    return render_template_string(PAGE_WEB,
        statut_chambres=statut_chambres, classe_chambres=classe_chambres,
        statut_clients=statut_clients, classe_clients=classe_clients,
        statut_prix=statut_prix, classe_prix=classe_prix,
        statut_reservations=statut_reservations, classe_reservations=classe_reservations,
        reservation=derniere_reservation
    )

if __name__ == '__main__':
    print("🌐 DASHBOARD Hôtel → http://localhost:5005")
    print("📱 Ouvre ton navigateur et va sur cette adresse!")
    app.run(port=5005, debug=True)