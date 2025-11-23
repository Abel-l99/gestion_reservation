from flask import Flask, render_template_string
import requests

app = Flask(__name__)

PAGE_WEB = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hôtel Distributed</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            color: #333;
        }
        .container { 
            max-width: 900px; 
            margin: 0 auto; 
            background: #f8f9fa; 
            padding: 30px; 
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .service-status { 
            background: white; 
            margin: 15px 0; 
            padding: 20px; 
            border-radius: 8px; 
            border-left: 5px solid #28a745;
        }
        .reservation-box { 
            background: #e8f5e8; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 25px 0;
            border: 1px solid #28a745;
        }
        .online { color: #28a745; font-weight: bold; }
        .offline { color: #dc3545; font-weight: bold; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .communication { background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0; }
        .btn-actualiser { 
            padding: 10px 20px; 
            background: #007bff; 
            color: white; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 16px;
        }
        .btn-actualiser:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>TABLEAU DE BORD - SYSTEME DISTRIBUE HOTEL</h1>
        
        <div class="service-status">
            <h2>ETAT DES SERVICES</h2>
            <p><strong>Service Clients:</strong> <span class="{{ classe_clients }}">{{ statut_clients }}</span></p>
            <p><strong>Service Chambres:</strong> <span class="{{ classe_chambres }}">{{ statut_chambres }}</span></p>
            <p><strong>Service Reservations:</strong> <span class="{{ classe_reservations }}">{{ statut_reservations }}</span></p>
        </div>
        
        <div class="communication">
            <h2>COMMUNICATION VIA APP_WEB (PONT)</h2>
            <p>2. <strong>app_web</strong> -> <strong>Service Chambres</strong> : récupère les informations sur la chambre </p>
            <p>3. <strong>app_web</strong> -> <strong>Service clients</strong> : récupère les informations sur le client </p>
            <p>1. <strong>app_web</strong> -> <strong>Service Réservations</strong> : créer/annuler une réservation avec les informations récupérées</p>
            <p>4. <strong>Service réservations</strong> -> <strong>Base de données</strong> : Enregistre/modifie les données dans la base de données</p>
        </div>
        
        <div style="text-align: center; margin-top: 30px;">
            <button onclick="window.location.reload()" class="btn-actualiser">
                Actualiser la page
            </button>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def afficher_dashboard():
    try:
        requests.get("http://localhost:5001/chambres", timeout=2)
        statut_chambres = "EN LIGNE"
        classe_chambres = "online"
    except:
        statut_chambres = "HORS LIGNE"
        classe_chambres = "offline"
    
    try:
        requests.get("http://localhost:5002/clients", timeout=2)
        statut_clients = "EN LIGNE"
        classe_clients = "online"
    except:
        statut_clients = "HORS LIGNE"
        classe_clients = "offline"
    
    try:
        reservations_data = requests.get("http://localhost:5003/reservations", timeout=2)
        statut_reservations = "EN LIGNE"
        classe_reservations = "online"
        
        reservations = reservations_data.json()
        
        if reservations and isinstance(reservations, list) and len(reservations) > 0:
            derniere_reservation = reservations[-1]
        elif reservations and isinstance(reservations, dict) and len(reservations) > 0:
            derniere_reservation = list(reservations.values())[-1]
        else:
            derniere_reservation = None
            
    except Exception as e:
        statut_reservations = "HORS LIGNE"
        classe_reservations = "offline"
        derniere_reservation = None
    
    return render_template_string(PAGE_WEB,
        statut_chambres=statut_chambres,
        classe_chambres=classe_chambres,
        statut_clients=statut_clients,
        classe_clients=classe_clients,
        statut_reservations=statut_reservations,
        classe_reservations=classe_reservations,
        reservation=derniere_reservation
    )

if __name__ == '__main__':
    print("Tableau de bord Hotel -> http://localhost:5005")
    app.run(port=5005, debug=True)
