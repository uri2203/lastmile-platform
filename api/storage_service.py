"""
LAST MILE DELIVERY - Storage Service
Sube comprobantes de entrega (foto/firma) a Supabase Storage via su API REST.
No usa el SDK oficial (supabase-py) para no agregar una dependencia nueva --
`requests` ya es dependencia del proyecto y la API de Storage es simple.
"""
import os
import base64
import logging
import uuid

logger = logging.getLogger('lastmile.storage')

SUPABASE_URL = os.environ.get('SUPABASE_URL', '').rstrip('/')
# Puede ser una service_role key clasica (JWT, "eyJ...") o una API key nueva
# de Supabase ("sb_secret_..."). Para el endpoint de Storage, ambas se mandan
# solo en el header `apikey` -- mandar tambien `Authorization: Bearer` rompe
# la subida con las keys nuevas ("Invalid Compact JWS", porque Storage intenta
# decodificarla como JWT para RLS y el formato sb_secret_ no lo es).
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
BUCKET = os.environ.get('SUPABASE_EVIDENCIA_BUCKET', 'entregas-evidencia')

ENABLED = bool(SUPABASE_URL and SUPABASE_SERVICE_KEY)
if ENABLED:
    logger.info(f'[STORAGE] Supabase Storage configurado (bucket={BUCKET})')
else:
    logger.info('[STORAGE] SUPABASE_URL/SUPABASE_SERVICE_KEY no configurados - evidencia se guarda solo como referencia local')


def upload_evidencia(file_b64, content_type, emp_id, ent_id):
    """Sube una foto o firma (base64, sin el prefijo data:...;base64,) a
    Supabase Storage. Devuelve la URL publica o None si el storage no esta
    configurado o la subida falla -- en ambos casos el caller debe seguir
    funcionando con la referencia local que ya tenia (best-effort, igual que
    el resto de las integraciones opcionales de la plataforma)."""
    if not ENABLED or not file_b64:
        return None
    try:
        file_bytes = base64.b64decode(file_b64)
    except Exception as e:
        logger.warning(f'[STORAGE] base64 invalido: {str(e)}')
        return None

    ext = 'png' if 'png' in (content_type or '') else 'jpg'
    filename = f'emp{emp_id}/ent{ent_id}_{uuid.uuid4().hex[:8]}.{ext}'

    try:
        import requests
        resp = requests.post(
            f'{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}',
            headers={
                'apikey': SUPABASE_SERVICE_KEY,
                'Content-Type': content_type or 'image/jpeg',
                'x-upsert': 'true',
            },
            data=file_bytes,
            timeout=20
        )
        if resp.status_code in (200, 201):
            return f'{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}'
        logger.warning(f'[STORAGE] Upload fallo ({resp.status_code}): {resp.text[:200]}')
    except Exception as e:
        logger.warning(f'[STORAGE] Upload exception: {str(e)}')
    return None
