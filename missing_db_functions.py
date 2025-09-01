
# Missing database functions for agreement generation
# Add these functions to crm_database.py

def get_partes_by_caso_and_tipo(case_id: int, tipo: str) -> List[Dict]:
    """
    Get parties by case ID and role type.
    This function is called by ai_agreement_generator.py but doesn't exist.

    Args:
        case_id: Case ID
        tipo: Role type ('ACTOR', 'DEMANDADO', 'ABOGADO', etc.)

    Returns:
        List of parties with the specified role type
    """
    try:
        query = """
            SELECT
                r.id as rol_id,
                r.caso_id,
                r.contacto_id,
                r.rol_principal,
                r.rol_secundario,
                r.representa_a_id,
                r.datos_bancarios,
                c.nombre_completo,
                c.dni,
                c.cuit,
                c.domicilio_real,
                c.domicilio_legal,
                c.email,
                c.telefono
            FROM roles_en_caso r
            JOIN contactos c ON r.contacto_id = c.id
            WHERE r.caso_id = %s AND r.rol_principal = %s
            ORDER BY c.nombre_completo
        """

        parties = execute_query(query, (case_id, tipo.upper()), fetch_all=True)
        return parties if parties else []

    except Exception as e:
        print(f"Error getting parties by case and type: {e}")
        return []

def get_representantes_by_party(case_id: int, party_id: int) -> List[Dict]:
    """
    Get representatives (lawyers) for a specific party.

    Args:
        case_id: Case ID
        party_id: Party ID (contacto_id)

    Returns:
        List of representatives for the party
    """
    try:
        query = """
            SELECT
                r.id as rol_id,
                r.contacto_id,
                r.rol_principal,
                r.rol_secundario,
                c.nombre_completo,
                c.dni,
                c.cuit,
                c.domicilio_real,
                c.domicilio_legal,
                c.email,
                c.telefono
            FROM roles_en_caso r
            JOIN contactos c ON r.contacto_id = c.id
            WHERE r.caso_id = %s
              AND (r.representa_a_id = %s OR r.contacto_id = %s)
              AND r.rol_principal IN ('ABOGADO', 'APODERADO')
            ORDER BY r.rol_principal, c.nombre_completo
        """

        representatives = execute_query(query, (case_id, party_id, party_id), fetch_all=True)
        return representatives if representatives else []

    except Exception as e:
        print(f"Error getting representatives for party: {e}")
        return []

def get_abogados_by_caso_and_tipo(case_id: int, tipo_party: str) -> List[Dict]:
    """
    Get lawyers by case and party type.

    Args:
        case_id: Case ID
        tipo_party: Party type ('ACTOR', 'DEMANDADO')

    Returns:
        List of lawyers representing the specified party type
    """
    try:
        # First get the parties of the specified type
        parties = get_partes_by_caso_and_tipo(case_id, tipo_party)

        if not parties:
            return []

        lawyers = []
        for party in parties:
            party_lawyers = get_representantes_by_party(case_id, party['contacto_id'])
            lawyers.extend(party_lawyers)

        return lawyers

    except Exception as e:
        print(f"Error getting lawyers by case and party type: {e}")
        return []
