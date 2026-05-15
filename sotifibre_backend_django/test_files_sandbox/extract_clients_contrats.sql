-- ============================================================
-- SOTIFibre BI Platform - Script d'extraction SQL
-- Objectif : Extraction clients et contrats pour alimentation
--            de la dimension dim_client (SCD Type 2)
-- Source   : sotifibre_db.public
-- Cible    : dim_client (Data Warehouse)
-- Auteur   : Equipe Data Engineering SOTIFibre
-- Version  : 2.1 - 2026-05-15
-- ============================================================

-- 1. Vue intermediaire : Clients avec contrat actif
CREATE OR REPLACE VIEW v_clients_actifs AS
SELECT
    c.id                                        AS client_id,
    c.nom,
    c.prenom,
    c.email,
    c.telephone,
    c.wilaya,
    c.statut                                    AS statut_client,
    ct.id                                       AS contrat_id,
    ct.offre_id,
    o.libelle                                   AS libelle_offre,
    o.debit_descendant_mbps                     AS debit_nominal_mbps,
    o.tarif_mensuel_da,
    ct.date_debut                               AS date_debut_contrat,
    ct.date_fin                                 AS date_fin_contrat,
    ct.statut                                   AS statut_contrat,
    EXTRACT(YEAR FROM AGE(NOW(), c.date_activation))::INTEGER AS anciennete_annees,
    CASE
        WHEN ct.tarif_mensuel_da >= 5000 THEN 'Premium'
        WHEN ct.tarif_mensuel_da >= 3000 THEN 'Standard'
        ELSE 'Essentiel'
    END                                         AS segment_commercial
FROM clients c
INNER JOIN contrats ct ON ct.client_id = c.id
    AND ct.statut = 'actif'
    AND (ct.date_fin IS NULL OR ct.date_fin > NOW())
LEFT JOIN offres o ON o.id = ct.offre_id
WHERE c.statut = 'actif';

-- 2. Detection des changements pour SCD Type 2
WITH clients_actuels AS (
    SELECT
        client_id,
        MD5(CONCAT_WS('|', nom, prenom, email, wilaya, offre_id, statut_contrat)) AS hash_attributs
    FROM v_clients_actifs
),
clients_dw AS (
    SELECT
        code_naturel::INTEGER AS client_id,
        hash_attributs
    FROM dim_client
    WHERE est_courant = TRUE
)
SELECT
    ca.client_id,
    CASE
        WHEN cd.client_id IS NULL     THEN 'NOUVEAU'
        WHEN ca.hash_attributs != cd.hash_attributs THEN 'MODIFIE'
        ELSE 'INCHANGE'
    END AS action_requise
FROM clients_actuels ca
LEFT JOIN clients_dw cd ON cd.client_id = ca.client_id;

-- 3. Extraction finale pour chargement ETL
SELECT
    va.client_id,
    va.nom,
    va.prenom,
    va.email,
    va.telephone,
    va.wilaya,
    va.statut_client,
    va.contrat_id,
    va.offre_id,
    va.libelle_offre,
    va.debit_nominal_mbps,
    va.tarif_mensuel_da,
    va.date_debut_contrat,
    va.anciennete_annees,
    va.segment_commercial,
    NOW()                               AS date_extraction,
    'ETL_Clients_CSV_Dimension_v2.1'    AS source_pipeline
FROM v_clients_actifs va
ORDER BY va.client_id;

-- 4. Statistiques de controle post-extraction
SELECT
    COUNT(*)                            AS total_clients_actifs,
    COUNT(DISTINCT wilaya)              AS nb_wilayas,
    COUNT(DISTINCT offre_id)            AS nb_offres,
    SUM(tarif_mensuel_da)               AS revenu_mensuel_da,
    ROUND(AVG(anciennete_annees), 1)    AS anciennete_moyenne,
    MIN(date_debut_contrat)             AS premier_contrat,
    MAX(date_debut_contrat)             AS dernier_contrat
FROM v_clients_actifs;
