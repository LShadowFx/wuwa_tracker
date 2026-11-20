"""Pruebas UNITARIAS de modelos y del motor de tiradas (gacha/pity.py).

Se prueba cada funcion aislada. El azar se reemplaza con mock para que el resultado
sea siempre el mismo.
"""
from unittest import mock

from django.contrib.auth.models import User
from django.test import TestCase

from gacha import pity
from gacha.models import Banner, EstadoPity, Item, Tirada

from .helpers import crear_mundo


class ItemModeloTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def test_probabilidad_real_unico_competidor_es_100(self):
        self.assertEqual(self.m.jiyan.probabilidad_real(), 100)

    def test_probabilidad_real_reparte_por_peso(self):
        # Danjin 30 y Sanhua 10 (4★ del permanente): 75 % y 25 %.
        self.assertEqual(self.m.danjin.probabilidad_real(), 75.0)
        self.assertEqual(self.m.sanhua.probabilidad_real(), 25.0)

    def test_probabilidad_real_ignora_otras_rarezas(self):
        # Calcharo (5★) solo compite con Verina (5★), no con los 4★ del mismo banner.
        self.assertEqual(self.m.calcharo.probabilidad_real(), 75.0)

    def test_probabilidad_real_con_peso_total_cero_devuelve_cero(self):
        Item.objects.filter(banner=self.m.perm, rareza=4).update(probabilidad=0)
        item = Item.objects.get(pk=self.m.danjin.pk)
        self.assertEqual(item.probabilidad_real(), 0)

    def test_slug_se_genera_desde_el_nombre(self):
        self.assertEqual(self.m.verdant.slug, 'verdant-summit')

    def test_slug_repetido_agrega_numero(self):
        a = Item.objects.create(nombre='Nombre X', categoria='arma', rareza=4, banner=self.m.perm)
        b = Item.objects.create(nombre='nombre x!', categoria='arma', rareza=4, banner=self.m.perm)
        self.assertEqual(a.slug, 'nombre-x')
        self.assertEqual(b.slug, 'nombre-x-1')

    def test_item_destacado_del_banner(self):
        self.assertEqual(self.m.lim_arma.item_destacado(), self.m.verdant)

    def test_banner_sin_destacado_devuelve_none(self):
        self.assertIsNone(self.m.perm.item_destacado())
        self.assertIsNone(self.m.vacio.item_destacado())


class ProbabilidadCincoEstrellasTests(TestCase):
    def test_antes_del_soft_pity_es_la_base(self):
        for pity_actual in (1, 30, 59):
            self.assertEqual(pity.probabilidad_5_estrellas(pity_actual), pity.PROBABILIDAD_BASE_5E)

    def test_soft_pity_sube_con_cada_tirada(self):
        self.assertAlmostEqual(pity.probabilidad_5_estrellas(60), 0.058)
        self.assertGreater(pity.probabilidad_5_estrellas(65), pity.probabilidad_5_estrellas(64))

    def test_nunca_supera_100_por_ciento(self):
        for pity_actual in range(1, 200):
            self.assertLessEqual(pity.probabilidad_5_estrellas(pity_actual), 1.0)


class ElegirPorProbabilidadTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def test_lista_vacia_devuelve_none(self):
        self.assertIsNone(pity._elegir_por_probabilidad([]))

    def test_usa_el_peso_de_cada_item(self):
        items = [self.m.danjin, self.m.sanhua]
        with mock.patch('gacha.pity.random.choices', return_value=[self.m.danjin]) as choices:
            self.assertEqual(pity._elegir_por_probabilidad(items), self.m.danjin)
        self.assertEqual(choices.call_args.kwargs['weights'], [30, 10])

    def test_limitacion_conocida_pesos_en_cero_revientan(self):
        """Solo se llega ahi saltandose los formularios (shell o .update()). Ver PLAN_DE_PRUEBAS.md."""
        Item.objects.filter(banner=self.m.perm, rareza=4).update(probabilidad=0)
        items = list(Item.objects.filter(banner=self.m.perm, rareza=4))
        with self.assertRaises(ValueError):
            pity._elegir_por_probabilidad(items)


class ElegirCincoEstrellasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()
        cls.user = User.objects.create_user('u', password='x')

    def estado(self, banner, garantizado=False):
        return EstadoPity(usuario=self.user, banner=banner, garantizado=garantizado)

    def test_arma_limitada_entrega_siempre_el_destacado_sin_50_50(self):
        item, gano = pity._elegir_item_cinco_estrellas(self.m.lim_arma, self.estado(self.m.lim_arma))
        self.assertEqual(item, self.m.verdant)
        self.assertIsNone(gano)

    def test_personaje_gana_el_50_50(self):
        est = self.estado(self.m.lim_pj)
        with mock.patch('gacha.pity.random.random', return_value=0.1):
            item, gano = pity._elegir_item_cinco_estrellas(self.m.lim_pj, est)
        self.assertEqual((item, gano, est.garantizado), (self.m.jiyan, True, False))

    def test_personaje_pierde_el_50_50_y_queda_garantizado(self):
        est = self.estado(self.m.lim_pj)
        with mock.patch('gacha.pity.random.random', return_value=0.9):
            item, gano = pity._elegir_item_cinco_estrellas(self.m.lim_pj, est)
        self.assertIn(item, (self.m.calcharo, self.m.verina))  # sale del pool del permanente
        self.assertFalse(gano)
        self.assertTrue(est.garantizado)

    def test_personaje_garantizado_entrega_el_destacado_sin_tirar_el_dado(self):
        est = self.estado(self.m.lim_pj, garantizado=True)
        with mock.patch('gacha.pity.random.random', return_value=0.99):
            item, gano = pity._elegir_item_cinco_estrellas(self.m.lim_pj, est)
        self.assertEqual((item, gano, est.garantizado), (self.m.jiyan, True, False))

    def test_permanente_elige_entre_sus_5_estrellas(self):
        item, gano = pity._elegir_item_cinco_estrellas(self.m.perm, self.estado(self.m.perm))
        self.assertIn(item, (self.m.calcharo, self.m.verina))
        self.assertIsNone(gano)


class SimularUnaTiradaTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()
        cls.user = User.objects.create_user('u', password='x')

    def estado(self, banner, **kw):
        return EstadoPity(usuario=self.user, banner=banner, **kw)

    def test_cada_tirada_suma_pity(self):
        est = self.estado(self.m.perm)
        with mock.patch('gacha.pity.random.random', return_value=0.99):
            res = pity.simular_una_tirada(self.m.perm, est)
        self.assertEqual((res['rareza'], est.pity_actual, est.pity_4_actual), (3, 1, 1))
        self.assertIsNone(res['item'])

    def test_hard_pity_a_las_80_da_5_estrellas_aunque_el_azar_diga_que_no(self):
        # Se anula la probabilidad normal para probar solo el hard pity.
        est = self.estado(self.m.lim_arma, pity_actual=79)
        with mock.patch('gacha.pity.probabilidad_5_estrellas', return_value=0.0), \
                mock.patch('gacha.pity.random.random', return_value=0.99):
            res = pity.simular_una_tirada(self.m.lim_arma, est)
        self.assertEqual((res['rareza'], res['pity_en_momento']), (5, 80))
        self.assertEqual(res['item'], self.m.verdant)
        self.assertEqual((est.pity_actual, est.pity_4_actual), (0, 0))

    def test_un_pity_antes_del_hard_pity_no_garantiza_nada(self):
        est = self.estado(self.m.lim_arma, pity_actual=78)  # esta tirada es la 79
        with mock.patch('gacha.pity.probabilidad_5_estrellas', return_value=0.0), \
                mock.patch('gacha.pity.random.random', return_value=0.99):
            res = pity.simular_una_tirada(self.m.lim_arma, est)
        self.assertEqual((res['rareza'], est.pity_actual), (3, 79))

    def test_pity_de_4_estrellas_garantiza_un_4_cada_10(self):
        est = self.estado(self.m.perm, pity_actual=20, pity_4_actual=9)
        with mock.patch('gacha.pity.random.random', return_value=0.99):
            res = pity.simular_una_tirada(self.m.perm, est)
        self.assertEqual(res['rareza'], 4)
        self.assertIn(res['item'], (self.m.danjin, self.m.sanhua))
        self.assertEqual(est.pity_4_actual, 0)
        self.assertEqual(est.pity_actual, 21)  # el pity de 5★ sigue corriendo


class SimularTiradasTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()
        cls.user = User.objects.create_user('u', password='x')

    def test_guarda_las_tiradas_de_4_y_5_estrellas(self):
        with mock.patch('gacha.pity.random.random', return_value=0.0):
            tiradas = pity.simular_tiradas(self.user, self.m.lim_arma, 10)
        self.assertEqual(len(tiradas), 10)
        self.assertEqual(Tirada.objects.filter(usuario=self.user).count(), 10)
        self.assertTrue(all(t.item == self.m.verdant for t in tiradas))

    def test_las_de_3_estrellas_no_se_guardan_pero_el_pity_si(self):
        with mock.patch('gacha.pity.random.random', return_value=0.99):
            tiradas = pity.simular_tiradas(self.user, self.m.perm, 3)
        self.assertEqual(tiradas, [])
        estado = EstadoPity.objects.get(usuario=self.user, banner=self.m.perm)
        self.assertEqual(estado.pity_actual, 3)

    def test_un_estado_de_pity_por_usuario_y_banner(self):
        with mock.patch('gacha.pity.random.random', return_value=0.99):
            pity.simular_tiradas(self.user, self.m.perm, 1)
            pity.simular_tiradas(self.user, self.m.perm, 1)
        self.assertEqual(EstadoPity.objects.filter(usuario=self.user, banner=self.m.perm).count(), 1)
        self.assertEqual(EstadoPity.objects.get(usuario=self.user, banner=self.m.perm).pity_actual, 2)

    def test_limitacion_conocida_banner_limitado_sin_destacado_gasta_el_pity_sin_resultado(self):
        """El hueco que cerro el formulario: si un banner limitado se queda sin destacado,
        el pity se reinicia pero no se crea ninguna Tirada. Documenta el comportamiento actual."""
        EstadoPity.objects.create(usuario=self.user, banner=self.m.vacio, pity_actual=79)
        with mock.patch('gacha.pity.random.random', return_value=0.99):
            tiradas = pity.simular_tiradas(self.user, self.m.vacio, 1)
        self.assertEqual(tiradas, [])
        self.assertEqual(EstadoPity.objects.get(usuario=self.user, banner=self.m.vacio).pity_actual, 0)
