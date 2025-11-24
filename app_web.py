from flask import Flask, render_template, request, redirect, url_for, jsonify
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
    
    print(f" TEST {service_name}: {url}")
    
    try:
        response = requests.get(url, timeout=2)
        
        # Test plus permissif
        if response.status_code == 200:
            return True
        else:
            return False
            
    except requests.exceptions.ConnectTimeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except Exception as e:
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
        print(f"Récupération données {service_name} depuis {url}")
        response = requests.get(url, timeout=5)  # Timeout plus long
        if response.status_code == 200:
            print(f"Données {service_name} récupérées avec succès")
            return response.json()
        else:
            print(f"Erreur {service_name}: Status {response.status_code}")
            return None
    except Exception as e:
        print(f"Erreur récupération {service_name}: {e}")
        return None

def mettre_a_jour_disponibilite_chambre(chambre_id, disponible):
    """Met à jour la disponibilité d'une chambre dans MySQL"""
    try:
        response = requests.put(
            f'http://localhost:5001/chambre/{chambre_id}/disponible',
            json={"disponible": disponible}
        )
        return response.status_code == 200
    except Exception as e:
        return False

@app.route('/')
def accueil():
    """Page d'accueil avec vérification parallèle des services"""
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_chambres = executor.submit(get_service_data, 'chambres')
            future_clients = executor.submit(get_service_data, 'clients')
            future_reservations = executor.submit(get_service_data, 'reservations')
            future_agences = executor.submit(get_service_data, 'chambres', 'agences')
            
            chambres_data = future_chambres.result(timeout=8)
            clients_data = future_clients.result(timeout=8)
            reservations_data = future_reservations.result(timeout=8)
            agences_data_result = future_agences.result(timeout=8)

        reservations_en_cours = []
        if reservations_data:
            clients_map = {}
            chambres_map = {}
            if clients_data:
                for c in clients_data:
                    clients_map[c.get('id_client')] = c
            if chambres_data:
                for ch in chambres_data:
                    chambres_map[ch.get('id_chambre')] = ch
            for reservation in reservations_data:
                statut = reservation.get('statut')
                if statut != 'annulée':
                    reservation['client_info'] = clients_map.get(reservation.get('client_id'))
                    reservation['chambre_info'] = chambres_map.get(reservation.get('chambre_id'))
                    reservations_en_cours.append(reservation)
        
        # Créer un mapping agence_id → nom agence
        agences_map = {}
        if agences_data_result:
            for agence in agences_data_result:
                agences_map[agence['id_agence']] = agence['localisation']
        
        services_status = {
            'chambres': chambres_data is not None,
            'clients': clients_data is not None,
            'reservations': reservations_data is not None,
            'agences': agences_data_result is not None
        }
        
        return render_template('accueil.html',
            chambres=chambres_data if chambres_data is not None else [],
            clients=clients_data if clients_data is not None else [],
            reservations=reservations_en_cours,
            agences_map=agences_map,
            services_status=services_status
        )
        
    except concurrent.futures.TimeoutError:
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
        
        print(f"DEBUG: Données reçues - client:{client_id}, chambre:{chambre_id}, nuits:{nuits}")
        
        # Vérifier si le service réservations est disponible
        if not check_service_available('reservations', 'health'):
            return redirect(url_for('accueil') + '?error=Service réservations indisponible')
        
        
        # Préparer les données
        # Récupérer le prix de la chambre et calculer le total
        chambre_resp = requests.get(f"{SERVICES['chambres']}/chambre/{int(chambre_id)}", timeout=5)
        if chambre_resp.status_code != 200:
            return redirect(url_for('accueil') + '?error=Prix chambre introuvable')
        chambre_info = chambre_resp.json()
        prix_nuit = chambre_info.get('prix', 100)
        total = float(prix_nuit) * int(nuits)

        data = {
            "client_id": int(client_id),
            "chambre_id": int(chambre_id),
            "nuits": int(nuits),
            "prix_total": total
        }
        
        url = f"{SERVICES['reservations']}/reserver"
        
        response = requests.post(url, json=data, timeout=10)

        if response.status_code == 200:
            ok = mettre_a_jour_disponibilite_chambre(int(chambre_id), False)
            if not ok:
                return redirect(url_for('accueil') + '?error=Chambre non mise en occupée')
            return redirect(url_for('accueil') + '?success=1')
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get("error", "Erreur inconnue")
            except:
                error_msg = response.text
            
            return redirect(url_for('accueil') + f'?error={error_msg}')
            
    except Exception as e:
        return redirect(url_for('accueil') + f'?error={str(e)}')

@app.route('/annuler/<reservation_id>', methods=['POST'])
def annuler_reservation_complete(reservation_id):
    """Orchestrateur: Appelle les 2 services"""
    try:
        
        r = requests.put(f"{SERVICES['reservations']}/reservations/{reservation_id}/statut", json={"statut": "annulée"}, timeout=8)
        if r.status_code != 200:
            try:
                return jsonify(r.json()), 500
            except Exception:
                return jsonify({"success": False, "error": r.text}), 500
        result_reservation = r.json()
        
        # 2. RÉCUPÉRATION ID CHAMBRE 
        chambre_id = result_reservation.get('chambre_id')
        if not chambre_id:
            try:
                all_reservations = requests.get(f"{SERVICES['reservations']}/reservations", timeout=8).json() or []
                for resa in all_reservations:
                    if str(resa.get('_id')) == str(reservation_id):
                        chambre_id = resa.get('chambre_id')
                        break
            except Exception:
                pass
            if not chambre_id:
                return jsonify({"success": False, "error": "ID chambre manquant"}), 500
        
        # 3. APPEL SERVICE CHAMBRES - Libération chambre 
        ok = mettre_a_jour_disponibilite_chambre(int(chambre_id), True)
        if not ok:
            return jsonify({"success": False, "error": "Échec libération chambre"}), 500
        
        # 4. SUCCÈS COMPLET 
        message_final = f"🎉 Annulation terminée: Réservation annulée + Chambre libérée"
        print(message_final)
        
        return jsonify({
            "success": True,
            "message": message_final,
            "numero_reservation": result_reservation.get('numero_reservation')
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": f"Erreur: {str(e)}"}), 500

if __name__ == '__main__':
    print(" Application Web → http://localhost:5000")
    app.run(port=5000, debug=True)
