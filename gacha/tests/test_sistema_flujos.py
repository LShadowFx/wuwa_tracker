"""Pruebas de SISTEMA: recorridos completos de punta a punta, como los haria una persona
en el navegador (login, formularios, tiradas, historial), sin llamar a funciones internas."""
from unittest import mock

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from gacha.models import Banner, EstadoPity, Item, Tirada

from .helpers import CLAVE, crear_mundo, crear_usuarios, datos_banner, datos_item


class FlujoBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()
        cls.u = crear_usuarios()

    def mensajes(self, r):
        """Mensajes de la pagina; el ultimo es el de la accion recien hecha."""
        return [str(x) for x in r.context['messages']]


class FlujoAdminArmeBannerTests(FlujoBase):
    """El admin monta un banner de arma limitada y un jugador tira en el."""

    def test_recorrido_completo(self):
        admin, jugador = Client(), Client()
        admin.force_login(self.u.admin)

        # 1) Crea el banner (arma limitada) y queda sin items.
        r = admin.post(reverse('gacha:banner_crear'),
                       datos_banner(nombre='Armas de Prueba', tipo='arma'), follow=True)
        banner = Banner.objects.get(nombre='Armas de Prueba')
        self.assertRedirects(r, reverse('gacha:banner_detalle', args=[banner.id]))

        # 2) Tirar en un banner sin items se avisa y no se guarda nada.
        jugador.force_login(self.u.jugador)
        r = jugador.post(reverse('gacha:simular'), {'banner': banner.id, 'cantidad': '1'}, follow=True)
        self.assertIn('todavía no tiene items', self.mensajes(r)[-1])
        self.assertEqual(Tirada.objects.count(), 0)

        # 3) Un 5★ sin destacado en banner limitado se rechaza...
        r = admin.post(reverse('gacha:item_crear'),
                       datos_item(banner, nombre='Espada Real', categoria='arma', rareza='5'))
        self.assertContains(r, 'debe ser el destacado')
        # ...y con el destacado marcado se acepta.
        admin.post(reverse('gacha:item_crear'), datos_item(
            banner, nombre='Espada Real', categoria='arma', rareza='5', es_destacado='on'))
        self.assertEqual(banner.item_destacado().nombre, 'Espada Real')

        # 4) Un segundo destacado se rechaza; un personaje en un banner de armas, tambien.
        r = admin.post(reverse('gacha:item_crear'), datos_item(
            banner, nombre='Otra Espada', categoria='arma', rareza='5', es_destacado='on'))
        self.assertContains(r, 'ya tiene un destacado (Espada Real)')
        r = admin.post(reverse('gacha:item_crear'), datos_item(banner, nombre='Heroe', categoria='personaje'))
        self.assertContains(r, 'solo admite armas')

        # 5) Agrega un 4★ y el banner ya tiene contenido.
        admin.post(reverse('gacha:item_crear'), datos_item(banner, nombre='Daga Comun', categoria='arma'))
        self.assertEqual(banner.items.count(), 2)

        # 6) El jugador tira x10 (azar forzado a 5★): todas salen el destacado.
        with mock.patch('gacha.pity.random.random', return_value=0.0):
            r = jugador.post(reverse('gacha:simular'), {'banner': banner.id, 'cantidad': '10'})
        self.assertRedirects(r, reverse('gacha:resultado'))
        self.assertEqual(Tirada.objects.filter(usuario=self.u.jugador, item__nombre='Espada Real').count(), 10)
        self.assertEqual(jugador.get(reverse('gacha:resultado')).status_code, 200)

        # 7) El dashboard muestra su pity e historial; comparte una tirada y aparece en el feed.
        self.assertContains(jugador.get(reverse('gacha:dashboard')), 'Armas de Prueba')
        tirada = Tirada.objects.filter(usuario=self.u.jugador).first()
        jugador.post(reverse('gacha:compartir', args=[tirada.id]))
        self.assertContains(Client().get(reverse('gacha:feed')), 'jugador')

        # 8) Con tiradas hechas, ni el item ni el banner se pueden eliminar.
        r = admin.post(reverse('gacha:item_eliminar', args=[banner.item_destacado().id]), follow=True)
        self.assertIn('No se puede eliminar', self.mensajes(r)[-1])
        r = admin.post(reverse('gacha:banner_eliminar', args=[banner.id]), follow=True)
        self.assertIn('No se puede eliminar el banner', self.mensajes(r)[-1])
        self.assertTrue(Banner.objects.filter(pk=banner.id).exists())


class FlujoCincuentaCincuentaTests(FlujoBase):
    """Banner de personaje limitado: perder el 50/50 deja la siguiente tirada garantizada."""

    def tirar(self, valores):
        c = Client()
        c.force_login(self.u.jugador)
        with mock.patch('gacha.pity.random.random', side_effect=valores):
            c.post(reverse('gacha:simular'), {'banner': self.m.lim_pj.id, 'cantidad': '1'})

    def test_perder_y_luego_ganar_garantizado(self):
        # Tirada 1: sale 5★ (0.0) y pierde el 50/50 (0.9) -> item del permanente.
        self.tirar([0.0, 0.9])
        t1 = Tirada.objects.get()
        self.assertIn(t1.item, (self.m.calcharo, self.m.verina))
        self.assertIs(t1.gano_50_50, False)
        self.assertTrue(EstadoPity.objects.get().garantizado)

        # Tirada 2: sale 5★ (0.0) y, estando garantizado, entrega el destacado sin dado.
        self.tirar([0.0])
        t2 = Tirada.objects.order_by('id').last()
        self.assertEqual(t2.item, self.m.jiyan)
        self.assertIs(t2.gano_50_50, True)
        self.assertFalse(EstadoPity.objects.get().garantizado)
        self.assertEqual(t2.pity_en_momento, 1)


class FlujoStaffTests(FlujoBase):
    """El staff solo ve y edita: puede cambiar pesos, pero no crear ni eliminar."""

    def test_staff_edita_pesos_pero_no_crea_ni_elimina(self):
        staff = Client()
        staff.force_login(self.u.staff)
        self.assertContains(staff.get(reverse('gacha:item_gestionar')), 'Danjin')
        staff.post(reverse('gacha:item_editar', args=[self.m.sanhua.id]),
                   datos_item(self.m.perm, nombre='Sanhua', probabilidad='30'))
        self.m.sanhua.refresh_from_db()
        self.m.danjin.refresh_from_db()
        self.assertEqual((self.m.danjin.probabilidad_real(), self.m.sanhua.probabilidad_real()), (50.0, 50.0))
        self.assertEqual(staff.get(reverse('gacha:item_crear')).status_code, 403)
        self.assertEqual(staff.post(reverse('gacha:item_eliminar', args=[self.m.sanhua.id])).status_code, 403)
        self.assertEqual(staff.post(reverse('gacha:banner_eliminar', args=[self.m.vacio.id])).status_code, 403)


class FlujoCambioDeTipoTests(FlujoBase):
    """Cambiar el tipo de un banner solo se permite cuando sus items lo admiten."""

    def test_bloqueado_hasta_arreglar_los_items(self):
        admin = Client()
        admin.force_login(self.u.admin)
        url = reverse('gacha:banner_editar', args=[self.m.lim_arma.id])
        r = admin.post(url, datos_banner(nombre='Arma Prueba', tipo='permanente'))
        self.assertContains(r, 'no tiene item destacado')

        # Para pasarlo a permanente hay que sacar el destacado: el item se elimina (admin)...
        admin.post(reverse('gacha:item_eliminar', args=[self.m.verdant.id]))
        # ...y como el 4★ sigue siendo arma, el permanente ya lo acepta.
        r = admin.post(url, datos_banner(nombre='Arma Prueba', tipo='permanente'), follow=True)
        self.assertIn('Se actualizó el banner', self.mensajes(r)[-1])
        self.m.lim_arma.refresh_from_db()
        self.assertEqual(self.m.lim_arma.tipo, 'permanente')


class SeguridadTests(FlujoBase):
    def test_csrf_se_exige_en_formularios_que_modifican_datos(self):
        c = Client(enforce_csrf_checks=True)
        c.force_login(self.u.jugador)
        r = c.post(reverse('gacha:simular'), {'banner': self.m.perm.id, 'cantidad': '1'})
        self.assertEqual(r.status_code, 403)
        c.force_login(self.u.admin)
        r = c.post(reverse('gacha:item_eliminar', args=[self.m.sanhua.id]))
        self.assertEqual(r.status_code, 403)
        self.assertTrue(Item.objects.filter(pk=self.m.sanhua.id).exists())

    def test_no_se_puede_compartir_la_tirada_de_otro_jugador(self):
        t = Tirada.objects.create(usuario=self.u.otro, banner=self.m.perm, item=self.m.danjin, pity_en_momento=1)
        c = Client()
        c.force_login(self.u.jugador)
        self.assertEqual(c.post(reverse('gacha:compartir', args=[t.id])).status_code, 404)
        t.refresh_from_db()
        self.assertFalse(t.compartida)

    def test_cada_jugador_solo_ve_su_resultado_y_su_historial(self):
        Tirada.objects.create(usuario=self.u.otro, banner=self.m.perm, item=self.m.danjin, pity_en_momento=1)
        c = Client()
        c.force_login(self.u.jugador)
        self.assertEqual(c.get(reverse('gacha:dashboard')).context['total_tiradas'], 0)

    def test_login_correcto_incorrecto_y_redireccion_segura(self):
        c = Client()
        r = c.post(reverse('cuentas:login'), {'username': 'jugador', 'password': 'mala'})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('_auth_user_id', c.session)

        # Vuelve a la pagina que pedia (next)...
        r = c.post(reverse('cuentas:login'), {'username': 'jugador', 'password': CLAVE,
                                              'next': reverse('gacha:dashboard')})
        self.assertRedirects(r, reverse('gacha:dashboard'), fetch_redirect_response=False)
        # ...pero nunca a un sitio externo.
        c = Client()
        r = c.post(reverse('cuentas:login'), {'username': 'jugador', 'password': CLAVE,
                                              'next': 'https://sitio-malicioso.com/'})
        self.assertRedirects(r, reverse('gacha:catalogo'), fetch_redirect_response=False)

    def test_cerrar_sesion_solo_por_post(self):
        c = Client()
        c.force_login(self.u.jugador)
        c.get(reverse('cuentas:logout'))
        self.assertIn('_auth_user_id', c.session)
        c.post(reverse('cuentas:logout'))
        self.assertNotIn('_auth_user_id', c.session)

    def test_los_datos_con_html_se_escapan_en_las_paginas(self):
        Item.objects.create(nombre='<script>alert(1)</script>', categoria='arma', rareza=4, banner=self.m.perm)
        r = Client().get(reverse('gacha:catalogo'))
        self.assertNotContains(r, '<script>alert(1)</script>')
        self.assertContains(r, '&lt;script&gt;')
