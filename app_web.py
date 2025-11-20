from flask import Flask, render_template, request, redirect, url_for
import requests

app = Flask(__name__)

# URLs des services
SERVICES = {
    'chambres': 'http://localhost:5001',
    'clients': 'http://localhost:5002', 
    'reservations': 'http://localhost:5003'
}

def check_service_available(service_name, endpoint=""):
    """Vérifie si un service est disponible avec plus de robustesse"""
    # Pour le service réservations, on utilise /health qui existe
    if service_name == 'reservations' and not endpoint:
        endpoint = 'health'  # Utilise /health au lieu de la racine
    
    url = f"{SERVICES[service_name]}/{endpoint}" if endpoint else f"{SERVICES[service_name]}"
    
    print(f"🔍 Vérification de {service_name} sur {url}")
    
    try:
        response = requests.get(url, timeout=3)
        print(f"✅ {service_name} répond: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur pour {service_name}: {e}")
        return False

def get_service_data(service_name, endpoint=""):
    """Récupère les données d'un service seulement s'il est disponible"""
    # Définir les endpoints par défaut pour chaque service
    default_endpoints = {
        'chambres': 'chambres',
        'clients': 'clients', 
        'reservations': 'reservations'  # Cet endpoint existe dans ton service
    }
    
    if not endpoint:
        endpoint = default_endpoints.get(service_name, "")
    
    if check_service_available(service_name, endpoint):
        url = f"{SERVICES[service_name]}/{endpoint}" if endpoint else f"{SERVICES[service_name]}"
        try:
            response = requests.get(url, timeout=3)
            return response.json() if response.status_code == 200 else []
        except:
            return []
    else:
        return None  # None = service indisponible

@app.route('/')
def accueil():
    """Page d'accueil avec gestion élégante des services indisponibles"""
    try:
        # Récupérer les données avec statut de disponibilité
        chambres_data = get_service_data('chambres', 'chambres')
        clients_data = get_service_data('clients', 'clients')
        reservations_data = get_service_data('reservations', 'reservations')
        
        # Déterminer quels services sont disponibles
        services_status = {
            'chambres': chambres_data is not None,
            'clients': clients_data is not None,
            'reservations': reservations_data is not None
        }
        
        # Utiliser les données ou des listes vides pour le template
        chambres = chambres_data if chambres_data is not None else []
        clients = clients_data if clients_data is not None else []
        reservations = reservations_data if reservations_data is not None else []
        
        return render_template('accueil.html',
            chambres=chambres,
            clients=clients, 
            reservations=reservations,
            services_status=services_status
        )
        
    except Exception as e:
        print(f"Erreur: {e}")
        return render_template('accueil.html',
            chambres=[],
            clients=[],
            reservations=[],
            services_status={'chambres': False, 'clients': False, 'reservations': False}
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
        
        response = requests.post(url, json=data, timeout=2)
        
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
        if not check_service_available('reservations', 'health'):
            return redirect(url_for('accueil') + '?error=Service réservations indisponible')
            
        response = requests.delete(f"{SERVICES['reservations']}/annuler/{reservation_id}", timeout=5)
        if response.status_code == 200:
            return redirect(url_for('accueil') + '?success=2')
        else:
            error_data = response.json()
            return redirect(url_for('accueil') + f'?error={error_data.get("error", "Erreur")}')
    except Exception as e:
        return redirect(url_for('accueil') + f'?error={str(e)}')

if __name__ == '__main__':
    print("🌐 Application Web → http://localhost:5000")
    app.run(port=5000, debug=True)