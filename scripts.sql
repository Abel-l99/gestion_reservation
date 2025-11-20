CREATE DATABASE service_chambres;
USE service_chambres;

CREATE TABLE agence(
    id_agence INTEGER AUTO_INCREMENT PRIMARY KEY,
    localisation TEXT,
    nbre_chambres INTEGER,
    nbre_etages INTEGER
);

CREATE TABLE chambre(
    id_chambre INTEGER AUTO_INCREMENT PRIMARY KEY,
    type_chambre ENUM("seul", "double", "suite"),
    etage INTEGER,
    prix DOUBLE,
    disponible BOOLEAN,
    id_agence INTEGER,
    FOREIGN KEY (id_agence) REFERENCES agence(id_agence)
);

INSERT INTO agence(localisation, nbre_chambres, nbre_etages) VALUES 
('Aneho', 10, 2),
('Baguida', 15, 3);  

INSERT INTO chambre(type_chambre, etage, prix, disponible, id_agence) VALUES
('seul', 1, 25000, TRUE, 1),
('double', 1, 40000, TRUE, 1),
('suite', 2, 75000, TRUE, 1),
('double', 1, 42000, TRUE, 1),
('seul', 2, 28000, TRUE, 1),
('suite', 2, 80000, TRUE, 1),
('suite', 3, 78000, TRUE, 1),
('double', 1, 38000, TRUE, 1),
('double', 2, 45000, TRUE, 2),
('seul', 1, 30000, TRUE, 2),
('seul', 2, 32000, TRUE, 2),
('seul', 3, 35000, TRUE, 2),
('seul', 1, 27000, TRUE, 2),
('double', 2, 48000, TRUE, 1),
('double', 3, 50000, TRUE, 1),
('seul', 1, 32000, TRUE, 1),
('seul', 2, 35000, TRUE, 1),
('suite', 1, 85000, TRUE, 1),
('double', 1, 42000, TRUE, 2),
('seul', 2, 30000, TRUE, 2),
('suite', 2, 82000, TRUE, 2),
('double', 1, 40000, TRUE, 2),
('double', 2, 47000, TRUE, 1),
('seul', 1, 28000, TRUE, 1),
('suite', 2, 88000, TRUE, 1);




CREATE DATABASE service_clients;
USE service_clients;

CREATE TABLE client(
    id_client INTEGER AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    telephone VARCHAR(20),
    date_inscription DATE
);

INSERT INTO client (nom, prenom, email, telephone, date_inscription) VALUES
('kossi', 'Abel', 'abelkossi@gmail.com', '+228 90 12 34 56', '2024-01-15'),
('Kossi', 'Jean', 'jeankossi@gmail.com', '+228 91 23 45 67', '2024-01-20'),
('Mensah', 'Afi', 'afimensah@gmail.com', '+228 92 34 56 78', '2024-02-01'),
('Agbeto', 'Koffi', 'koffiagbeto@gmail.com', '+228 93 45 67 89', '2024-02-10'),
('Adjo', 'Sena', 'senaadjo@gmail.com', '+228 94 56 78 90', '2024-02-15'),
('Gbeckley', 'Komlan', 'komlangbeckley@gmail.com', '+228 95 67 89 01', '2024-02-20'),
('Abalo', 'Mawulolo', 'mawuloloabalo@gmail.com', '+228 96 78 90 12', '2024-03-01'),
('Dosseh', 'Yawo', 'yawodosseh@gmail.com', '+228 97 89 01 23', '2024-03-05'),
('Folly', 'Akou', 'akoufolly@gmail.com', '+228 98 90 12 34', '2024-03-10'),
('Gadri', 'Essi', 'essigadri@gmail.com', '+228 99 01 23 45', '2024-03-15');