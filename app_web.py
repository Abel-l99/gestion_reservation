from flask import Flask, render_template, request, redirect, url_for
import requests
import concurrent.futures

app = Flask(__name__)

# URLs des services
SERVICES = {
    'chambres': 'http://localhost:5001',
    'clients': 'http://localhost:5002', 
    'reservations': 'http://localhost:5003'
}

def check_service_available(service_name, endpoint=""):
    """Vérifie si un service est disponible"""
    health_endpoints = {
        'chambres': 'chambres',
        'clients': 'clients', 
        'reservations': 'health'
    }
    
    endpoint = health_endpoints.get(service_name, endpoint)
    url = f"{SERVICES[service_name]}/{endpoint}" if endpoint else SERVICES[service_name]
    
    print(f"🎯 TEST {service_name}: {url}")
    
    try:
        response = requests.get(url, timeout=2)
        print(f"📡 RÉPONSE {service_name}:")
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        print(f"   Content: {response.text}")
        print(f"   URL appelée: {response.url}")
        
        # Test plus permissif
        if response.status_code == 200:
            print(f"✅ {service_name} = DISPONIBLE")
            return True
        else:
            print(f"❌ {service_name} = Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectTimeout:
        print(f"⏰ {service_name} = TIMEOUT")
        return False
    except requests.exceptions.ConnectionError:
        print(f"🔌 {service_name} = CONNECTION REFUSED")
        return False
    except Exception as e:
        print(f"💥 {service_name} = ERREUR: {e}")
        return False

def get_service_data(service_name, endpoint=""):
    """Récupère les données d'un service"""
    default_endpoints = {
        'chambres': 'chambres',
        'clients': 'clients', 
        'reservations': 'reservations'
    }
    
    if not endpoint:
        endpoint = default_endpoints.get(service_name, "")
    
    url = f"{SERVICES[service_name]}/{endpoint}" if endpoint else SERVICES[service_name]
    
    try:
        print(f"📡 Récupération données {service_name} depuis {url}")
        response = requests.get(url, timeout=5)  # Timeout plus long
        if response.status_code == 200:
            print(f"✅ Données {service_name} récupérées avec succès")
            return response.json()
        else:
            print(f"❌ Erreur {service_name}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"💥 Erreur récupération {service_name}: {e}")
        return None

@app.route('/')
def accueil():
    """Page d'accueil avec vérification parallèle des services"""
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Récupère les 4 services EN MÊME TEMPS
            future_chambres = executor.submit(get_service_data, 'chambres')
            future_clients = executor.submit(get_service_data, 'clients')
            future_reservations = executor.submit(get_service_data, 'reservations')
            future_agences = executor.submit(get_service_data, 'chambres', 'agences')  # Nouveau
            
            # Récupère tous les résultats
            chambres_data = future_chambres.result(timeout=8)
            clients_data = future_clients.result(timeout=8)
            reservations_data = future_reservations.result(timeout=8)
            agences_data_result = future_agences.result(timeout=8)  # Renomme la variable
        
        # Créer un mapping agence_id → nom agence
        agences_map = {}
        if agences_data_result:  # Utilise la bonne variable
            for agence in agences_data_result:
                agences_map[agence['id_agence']] = agence['localisation']
        
        # Déterminer quels services sont disponibles
        services_status = {
            'chambres': chambres_data is not None,
            'clients': clients_data is not None,
            'reservations': reservations_data is not None,
            'agences': agences_data_result is not None  # Utilise la bonne variable
        }
        
        return render_template('accueil.html',
            chambres=chambres_data if chambres_data is not None else [],
            clients=clients_data if clients_data is not None else [],
            reservations=reservations_data if reservations_data is not None else [],
            agences_map=agences_map,
            services_status=services_status
        )
        
    except concurrent.futures.TimeoutError:
        print("⏰ Timeout lors de la récupération des données")
        return render_template('accueil.html',
            chambres=[], clients=[], reservations=[],
            agences_map={},
            services_status={'chambres': False, 'clients': False, 'reservations': False, 'agences': False}
        )

@app.route('/reserver', methods=['POST'])
def reserver():
    """Faire une réservation"""
    try:
        client_id = request.form['client_id']
        chambre_id = request.form['chambre_id'] 
        nuits = request.form['nuits']
        
        print(f"🔍 DEBUG: Données reçues - client:{client_id}, chambre:{chambre_id}, nuits:{nuits}")
        
        # Vérifier si le service réservations est disponible
        if not check_service_available('reservations', 'health'):
            print("❌ DEBUG: Service réservations indisponible")
            return redirect(url_for('accueil') + '?error=Service réservations indisponible')
        
        print("✅ DEBUG: Service réservations disponible, envoi de la réservation...")
        
        # Préparer les données
        data = {
            "client_id": int(client_id),
            "chambre_id": int(chambre_id),
            "nuits": int(nuits)
        }
        
        url = f"{SERVICES['reservations']}/reserver"
        print(f"🌐 DEBUG: Envoi à {url}")
        
        response = requests.post(url, json=data, timeout=10)
        
        print(f"📡 DEBUG: Réponse - Status: {response.status_code}")
        print(f"📄 DEBUG: Contenu: {response.text}")
        
        if response.status_code == 200:
            print("✅ DEBUG: Réservation réussie!")
            return redirect(url_for('accueil') + '?success=1')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", "Erreur inconnue")
                print(f"❌ DEBUG: Erreur du service: {error_msg}")
            except:
                error_msg = response.text
                print(f"❌ DEBUG: Erreur brute: {error_msg}")
            
            return redirect(url_for('accueil') + f'?error={error_msg}')
            
    except Exception as e:
        print(f"💥 DEBUG: Erreur inattendue: {e}")
        return redirect(url_for('accueil') + f'?error={str(e)}')

@app.route('/annuler/<reservation_id>', methods=['POST'])
def annuler(reservation_id):
    """Annuler une réservation"""
    try:
        print(f"🔍 DEBUG Annulation: début pour {reservation_id}")
        
        # Vérifier si le service réservations est disponible
        if not check_service_available('reservations', 'health'):
            error_msg = "Service réservations indisponible"
            print(f"❌ DEBUG: {error_msg}")
            return redirect(url_for('accueil') + f'?error={error_msg}')
        
        print(f"✅ DEBUG: Service réservations disponible")
        
        # Appeler le service réservations
        url = f"{SERVICES['reservations']}/annuler/{reservation_id}"
        print(f"🌐 DEBUG: Appel à {url}")
        
        reponse = reservations_collection.update_one(
            {"_id": ObjectId(reservation_id)},
            {"$set": {"statut": "annulée"}}  # ← SEUL le statut change
        )
        
        print(f"📡 DEBUG: Réponse du service - Status: {response.status_code}")
        print(f"📄 DEBUG: Contenu: {response.text}")
        
        if response.status_code == 200:
            print("✅ DEBUG: Annulation réussie côté service!")
            return redirect(url_for('accueil') + '?success=2')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", "Erreur inconnue du service")
            except:
                error_msg = response.text or "Erreur sans message"
            
            print(f"❌ DEBUG: Erreur du service: {error_msg}")
            return redirect(url_for('accueil') + f'?error={error_msg}')
            
    except Exception as e:
        error_msg = f"Erreur technique: {str(e)}"
        print(f"💥 DEBUG: Erreur inattendue: {e}")
        return redirect(url_for('accueil') + f'?error={error_msg}')

if __name__ == '__main__':
    print("🌐 Application Web → http://localhost:5000")
    app.run(port=5000, debug=True)