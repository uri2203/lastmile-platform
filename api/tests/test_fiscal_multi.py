"""Tests for multi-country fiscal + payment endpoints."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from server import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


@pytest.fixture
def auth_token(client):
    r = client.post('/api/auth/login', json={'user': 'admin', 'pass': 'admin123'})
    return r.get_json().get('token', '')


def auth_header(token):
    return {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}


# ===== FISCAL ENDPOINTS =====

class TestFiscalCountries:
    def test_get_countries(self, client, auth_token):
        r = client.get('/api/fiscal/countries', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert len(d['data']) == 8
        codes = [c['code'] for c in d['data']]
        assert 'MX' in codes
        assert 'BR' in codes
        assert 'CO' in codes
        assert 'AR' in codes
        assert 'CL' in codes
        assert 'PE' in codes
        assert 'UY' in codes
        assert 'EC' in codes


class TestFiscalProviders:
    def test_get_providers(self, client, auth_token):
        r = client.get('/api/fiscal/providers', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert len(d['data']) == 8
        for p in d['data']:
            assert 'code' in p
            assert 'currency' in p
            assert 'provider' in p


class TestFiscalConfig:
    def test_get_config_empty(self, client, auth_token):
        r = client.get('/api/fiscal/config', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_put_config(self, client, auth_token):
        r = client.put('/api/fiscal/config', headers=auth_header(auth_token),
                       json={'country_code': 'MX', 'api_key': 'test_key_123'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_get_config_after_put(self, client, auth_token):
        client.put('/api/fiscal/config', headers=auth_header(auth_token),
                   json={'country_code': 'BR', 'api_key': 'br_test'})
        r = client.get('/api/fiscal/config', headers=auth_header(auth_token))
        d = r.get_json()
        assert d['success'] is True
        assert d['config'] is not None
        assert d['config']['TFC_COUNTRY_CODE'] == 'BR'


class TestFiscalTestConnection:
    def test_test_connection_mx(self, client, auth_token):
        r = client.post('/api/fiscal/test-connection', headers=auth_header(auth_token),
                        json={'country_code': 'MX'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert d['provider'] == 'MexicoProvider'

    def test_test_connection_br(self, client, auth_token):
        r = client.post('/api/fiscal/test-connection', headers=auth_header(auth_token),
                        json={'country_code': 'BR'})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert d['provider'] == 'BrazilProvider'

    def test_test_connection_all_countries(self, client, auth_token):
        for cc in ['MX', 'BR', 'CO', 'AR', 'CL', 'PE', 'UY', 'EC']:
            r = client.post('/api/fiscal/test-connection', headers=auth_header(auth_token),
                            json={'country_code': cc})
            assert r.status_code == 200
            assert r.get_json()['success'] is True


class TestFiscalEmit:
    def test_emit_no_config(self, client, auth_token):
        r = client.post('/api/fiscal/emit', headers=auth_header(auth_token),
                        json={'test': True})
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is False


class TestFiscalCancel:
    def test_cancel_no_config(self, client, auth_token):
        r = client.post('/api/fiscal/cancel', headers=auth_header(auth_token),
                        json={'document_id': 'test', 'reason': 'test'})
        assert r.status_code == 200


# ===== PAYMENT ENDPOINTS =====

class TestPaymentCountries:
    def test_get_payment_countries(self, client, auth_token):
        r = client.get('/api/payment/countries', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert 'MX' in d['data']
        assert 'BR' in d['data']


class TestPaymentMethods:
    def test_get_methods_mx(self, client, auth_token):
        r = client.get('/api/payment/methods/MX', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert len(d['data']) >= 1

    def test_get_methods_br(self, client, auth_token):
        r = client.get('/api/payment/methods/BR', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True

    def test_get_methods_all(self, client, auth_token):
        for cc in ['MX', 'BR', 'CO', 'AR', 'CL', 'PE', 'UY', 'EC']:
            r = client.get(f'/api/payment/methods/{cc}', headers=auth_header(auth_token))
            assert r.status_code == 200
            assert r.get_json()['success'] is True


# ===== WEBHOOK ENDPOINTS (PUBLIC) =====

class TestWebhooks:
    def test_stripe_webhook_raw(self, client):
        r = client.post('/api/webhooks/stripe',
                        data='{"type":"test","data":{}}',
                        content_type='application/json')
        assert r.status_code == 200
        assert r.get_json()['received'] is True

    def test_mp_webhook(self, client):
        r = client.post('/api/webhooks/mercadopago',
                        json={'action': 'payment.created', 'resource': '/v1/payments/123'})
        assert r.status_code == 200
        assert r.get_json()['received'] is True

    def test_stripe_webhook_invalid(self, client):
        r = client.post('/api/webhooks/stripe',
                        data='not json',
                        content_type='text/plain')
        assert r.status_code == 400

    def test_mp_webhook_empty(self, client):
        r = client.post('/api/webhooks/mercadopago', json={})
        assert r.status_code == 200


# ===== MIGRATION =====

class TestMigration:
    def test_migrate(self, client, auth_token):
        r = client.post('/api/system/migrate', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert d['ddl_ok'] >= 6
        assert d['payment_methods'] >= 20


# ===== STATIC FILES =====

class TestStaticFiles:
    def test_i18n_es(self, client):
        r = client.get('/i18n/es.json')
        assert r.status_code == 200
        d = r.get_json()
        assert 'app_name' in d
        assert 'fiscal' in d

    def test_i18n_en(self, client):
        r = client.get('/i18n/en.json')
        assert r.status_code == 200
        d = r.get_json()
        assert 'app_name' in d

    def test_i18n_pt(self, client):
        r = client.get('/i18n/pt.json')
        assert r.status_code == 200

    def test_i18n_js(self, client):
        r = client.get('/js/i18n.js')
        assert r.status_code == 200
        assert 'I18n' in r.data.decode()

    def test_fiscal_settings(self, client):
        r = client.get('/fiscal-settings.html')
        assert r.status_code == 200
        assert b'Fiscal' in r.data

    def test_fiscal_onboarding(self, client):
        r = client.get('/fiscal-onboarding.html')
        assert r.status_code == 200
        assert b'Onboarding' in r.data or b'Fiscal' in r.data

    def test_panel_admin(self, client):
        r = client.get('/panel-admin.html')
        assert r.status_code == 200
        assert b'Last Mile' in r.data


# ===== ANALYTICS =====

class TestMultiCountryAnalytics:
    def test_analytics_requires_auth(self, client):
        r = client.get('/api/analytics/multi-country')
        assert r.status_code == 401

    def test_analytics_ok(self, client, auth_token):
        r = client.get('/api/analytics/multi-country', headers=auth_header(auth_token))
        assert r.status_code == 200
        d = r.get_json()
        assert d['success'] is True
        assert 'countries_supported' in d['data']
        assert 'MX' in d['data']['countries_supported']
        assert len(d['data']['countries_supported']) == 8

    def test_analytics_has_currencies(self, client, auth_token):
        r = client.get('/api/analytics/multi-country', headers=auth_header(auth_token))
        d = r.get_json()
        assert 'currencies' in d['data']
        assert d['data']['currencies']['MX'] == 'mxn'
        assert d['data']['currencies']['BR'] == 'brl'

    def test_analytics_has_fiscal_configured(self, client, auth_token):
        r = client.get('/api/analytics/multi-country', headers=auth_header(auth_token))
        d = r.get_json()
        assert 'fiscal_configured' in d['data']
        assert isinstance(d['data']['fiscal_configured'], list)

    def test_analytics_has_payment_methods(self, client, auth_token):
        r = client.get('/api/analytics/multi-country', headers=auth_header(auth_token))
        d = r.get_json()
        assert 'payment_methods' in d['data']
        assert isinstance(d['data']['payment_methods'], list)


# ===== I18N PANELS =====

class TestI18nPanels:
    def test_panel_chofer_has_i18n(self, client):
        r = client.get('/panel-chofer.html')
        assert r.status_code == 200
        assert b'i18n.js' in r.data

    def test_panel_cliente_has_i18n(self, client):
        r = client.get('/panel-cliente.html')
        assert r.status_code == 200
        assert b'i18n.js' in r.data

    def test_panel_operacion_has_i18n(self, client):
        r = client.get('/panel-operacion.html')
        assert r.status_code == 200
        assert b'i18n.js' in r.data

    def test_panel_tenant_has_i18n(self, client):
        r = client.get('/panel-tenant.html')
        assert r.status_code == 200
        assert b'i18n.js' in r.data

    def test_panel_saas_has_i18n(self, client):
        r = client.get('/panel-saas.html')
        assert r.status_code == 200
        assert b'i18n.js' in r.data

    def test_i18n_has_panel_keys(self, client):
        r = client.get('/i18n/es.json')
        d = r.get_json()
        assert 'operacion' in d
        assert 'chofer' in d
        assert 'cliente' in d
        assert 'tenant' in d
        assert 'saas' in d

    def test_i18n_en_has_panel_keys(self, client):
        r = client.get('/i18n/en.json')
        d = r.get_json()
        assert 'operacion' in d
        assert 'chofer' in d
        assert 'cliente' in d

    def test_i18n_pt_has_panel_keys(self, client):
        r = client.get('/i18n/pt.json')
        d = r.get_json()
        assert 'operacion' in d
        assert 'chofer' in d
        assert 'cliente' in d

    def test_lang_select_in_chofer(self, client):
        r = client.get('/panel-chofer.html')
        assert b'lang-select' in r.data

    def test_lang_select_in_cliente(self, client):
        r = client.get('/panel-cliente.html')
        assert b'lang-select' in r.data

    def test_lang_select_in_operacion(self, client):
        r = client.get('/panel-operacion.html')
        assert b'lang-select' in r.data


# ===== PWA =====

class TestPWA:
    def test_manifest(self, client):
        r = client.get('/manifest.json')
        assert r.status_code == 200
        d = r.get_json()
        assert d['name'] == 'Last Mile - Chofer'
        assert d['display'] == 'standalone'

    def test_service_worker(self, client):
        r = client.get('/sw.js')
        assert r.status_code == 200
        assert b'sync' in r.data
        assert b'push' in r.data
        assert b'indexedDB' in r.data.lower() or b'IndexedDB' in r.data


# ===== NOTIFICATION MULTI-LANG =====

class TestNotificationMultiLang:
    def test_templates_exist(self):
        from notification_service import TEMPLATES_I18N
        assert 'pedido_creado' in TEMPLATES_I18N
        assert 'pedido_entregado' in TEMPLATES_I18N
        assert 'pago_recibido' in TEMPLATES_I18N

    def test_templates_have_3_languages(self):
        from notification_service import TEMPLATES_I18N
        for key, langs in TEMPLATES_I18N.items():
            assert 'es' in langs, f'{key} missing es'
            assert 'en' in langs, f'{key} missing en'
            assert 'pt' in langs, f'{key} missing pt'

    def test_templates_have_required_fields(self):
        from notification_service import TEMPLATES_I18N
        for key, langs in TEMPLATES_I18N.items():
            for lang, tmpl in langs.items():
                assert 'email_subject' in tmpl, f'{key}/{lang} missing email_subject'
                assert 'email_html' in tmpl, f'{key}/{lang} missing email_html'
                assert 'sms' in tmpl, f'{key}/{lang} missing sms'

    def test_country_lang_mapping(self):
        from notification_service import COUNTRY_LANG
        assert COUNTRY_LANG['MX'] == 'es'
        assert COUNTRY_LANG['BR'] == 'pt'
        assert COUNTRY_LANG['CO'] == 'es'

    def test_notification_service_has_get_tenant_lang(self):
        from notification_service import NotificationService
        ns = NotificationService()
        assert hasattr(ns, '_get_tenant_lang')
