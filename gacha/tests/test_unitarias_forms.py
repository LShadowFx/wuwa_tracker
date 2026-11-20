"""Pruebas UNITARIAS de los formularios (gacha/forms.py): una regla por prueba."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from gacha.forms import (
    BannerForm, FiltroBannerForm, FiltroCatalogoForm, ItemForm, SimularTiradaForm,
)
from gacha.models import Banner, Item

from .helpers import crear_mundo, datos_banner, datos_item


class ItemFormCamposTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def form(self, **cambios):
        return ItemForm(datos_item(self.m.perm, **cambios))

    def test_item_valido(self):
        self.assertTrue(self.form().is_valid(), self.form().errors)

    # --- nombre
    def test_nombre_de_un_caracter_se_rechaza(self):
        f = self.form(nombre='A')
        self.assertFalse(f.is_valid())
        self.assertIn('al menos 2', f.errors['nombre'][0])

    def test_nombre_repetido_se_rechaza_sin_importar_mayusculas(self):
        f = self.form(nombre='jiyan')
        self.assertFalse(f.is_valid())
        self.assertIn('Ya existe', f.errors['nombre'][0])

    def test_un_item_puede_conservar_su_propio_nombre_al_editarse(self):
        f = ItemForm(datos_item(self.m.perm, nombre='Danjin'), instance=self.m.danjin)
        self.assertTrue(f.is_valid(), f.errors)

    def test_nombre_se_limpia_de_espacios_dobles(self):
        f = self.form(nombre='  Nombre   Con   Espacios ')
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['nombre'], 'Nombre Con Espacios')

    # --- probabilidad
    def test_probabilidad_fuera_de_rango_se_rechaza(self):
        for valor in ('0', '101', '-5'):
            f = self.form(probabilidad=valor)
            self.assertFalse(f.is_valid(), valor)
            self.assertIn('probabilidad', f.errors)

    def test_probabilidad_en_los_limites_se_acepta(self):
        for valor in ('1', '100'):
            self.assertTrue(self.form(probabilidad=valor).is_valid(), valor)

    def test_probabilidad_vacia_o_con_letras_se_rechaza(self):
        for valor in ('', 'abc', '5.5'):
            self.assertFalse(self.form(probabilidad=valor).is_valid(), valor)

    # --- ataque base
    def test_ataque_base_fuera_de_100_a_800_se_rechaza(self):
        for valor in ('99', '801'):
            f = self.form(ataque_base=valor)
            self.assertFalse(f.is_valid(), valor)
            self.assertIn('entre 100 y 800', f.errors['ataque_base'][0])

    def test_ataque_base_en_limites_o_vacio_se_acepta(self):
        for valor in ('100', '800', ''):
            self.assertTrue(self.form(ataque_base=valor).is_valid(), valor)

    # --- descripcion
    def test_descripcion_muy_corta_se_rechaza(self):
        f = self.form(descripcion='hola')
        self.assertFalse(f.is_valid())
        self.assertIn('al menos 10', f.errors['descripcion'][0])

    def test_descripcion_de_mas_de_600_se_rechaza(self):
        f = self.form(descripcion='x' * 601)
        self.assertFalse(f.is_valid())
        self.assertIn('máximo es 600', f.errors['descripcion'][0])

    def test_descripcion_vacia_o_en_limites_se_acepta(self):
        for texto in ('', 'x' * 10, 'x' * 600):
            self.assertTrue(self.form(descripcion=texto).is_valid(), len(texto))

    # --- imagen (se prueba el metodo directo: no depende de Pillow)
    def _clean_imagen(self, archivo):
        f = ItemForm()
        f.cleaned_data = {'imagen': archivo}
        return f.clean_imagen()

    def test_imagen_con_formato_no_permitido_se_rechaza(self):
        from django import forms
        with self.assertRaisesMessage(forms.ValidationError, 'Formato no permitido'):
            self._clean_imagen(SimpleUploadedFile('a.gif', b'x'))

    def test_imagen_de_mas_de_2mb_se_rechaza(self):
        from django import forms
        with self.assertRaisesMessage(forms.ValidationError, 'más de 2 MB'):
            self._clean_imagen(SimpleUploadedFile('a.png', b'x' * (2 * 1024 * 1024 + 1)))

    def test_imagen_valida_se_acepta(self):
        archivo = SimpleUploadedFile('a.webp', b'x' * 100)
        self.assertIs(self._clean_imagen(archivo), archivo)


class ItemFormReglasDeNegocioTests(TestCase):
    """clean(): categoria contra banner y reglas del destacado."""

    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def errores(self, banner, **cambios):
        f = ItemForm(datos_item(banner, **cambios))
        f.is_valid()
        return f.errors

    # --- categoria vs tipo de banner
    def test_arma_en_banner_de_personaje_se_rechaza(self):
        e = self.errores(self.m.lim_pj, categoria='arma')
        self.assertIn('solo admite personajes', e['categoria'][0])

    def test_personaje_en_banner_de_arma_se_rechaza(self):
        e = self.errores(self.m.lim_arma, categoria='personaje')
        self.assertIn('solo admite armas', e['categoria'][0])

    def test_el_permanente_admite_las_dos_categorias(self):
        for categoria in ('personaje', 'arma'):
            self.assertNotIn('categoria', self.errores(self.m.perm, categoria=categoria))

    # --- destacado
    def test_destacado_en_un_4_estrellas_se_rechaza(self):
        e = self.errores(self.m.vacio, categoria='arma', rareza='4', es_destacado='on')
        self.assertIn('Solo un item de 5 estrellas', e['es_destacado'][0])

    def test_destacado_en_banner_permanente_se_rechaza(self):
        e = self.errores(self.m.perm, rareza='5', es_destacado='on')
        self.assertIn('permanente no tiene item destacado', e['es_destacado'][0])

    def test_segundo_destacado_en_el_mismo_banner_se_rechaza_y_nombra_al_actual(self):
        e = self.errores(self.m.lim_arma, categoria='arma', rareza='5', es_destacado='on')
        self.assertIn('ya tiene un destacado (Verdant Summit)', e['es_destacado'][0])

    def test_5_estrellas_en_banner_limitado_sin_destacado_se_rechaza(self):
        e = self.errores(self.m.vacio, categoria='arma', rareza='5')
        self.assertIn('debe ser el destacado', e['es_destacado'][0])

    def test_primer_5_estrellas_destacado_de_un_banner_limitado_se_acepta(self):
        f = ItemForm(datos_item(self.m.vacio, categoria='arma', rareza='5', es_destacado='on'))
        self.assertTrue(f.is_valid(), f.errors)

    def test_5_estrellas_sin_destacado_en_permanente_se_acepta(self):
        f = ItemForm(datos_item(self.m.perm, rareza='5'))
        self.assertTrue(f.is_valid(), f.errors)

    def test_4_estrellas_en_banner_limitado_con_destacado_se_acepta(self):
        f = ItemForm(datos_item(self.m.lim_arma, categoria='arma', rareza='4'))
        self.assertTrue(f.is_valid(), f.errors)


class ItemFormDestacadoFijoTests(TestCase):
    """Candado del servidor: el destacado de un banner limitado no puede dejar su sitio."""

    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def test_el_destacado_de_un_limitado_queda_fijo(self):
        f = ItemForm(instance=self.m.verdant)
        self.assertTrue(f.destacado_fijo)
        bloqueados = sorted(n for n, c in f.fields.items() if c.disabled)
        self.assertEqual(bloqueados, ['banner', 'es_destacado', 'rareza'])

    def test_no_se_fija_en_los_demas_casos(self):
        casos = {
            'item que no es destacado': ItemForm(instance=self.m.espada4),
            'item nuevo': ItemForm(),
            '5★ del permanente': ItemForm(instance=self.m.calcharo),
        }
        for nombre, f in casos.items():
            self.assertFalse(f.destacado_fijo, nombre)
            self.assertFalse(any(c.disabled for c in f.fields.values()), nombre)

    def test_post_manipulado_no_mueve_ni_degrada_al_destacado(self):
        """Intenta bajar a 4★, quitar el destacado y cambiar de banner en el mismo envio."""
        post = datos_item(self.m.perm, nombre='Verdant Summit', categoria='arma', rareza='4')
        f = ItemForm(post, instance=Item.objects.get(pk=self.m.verdant.pk))
        self.assertTrue(f.is_valid(), f.errors)
        item = f.save()
        item.refresh_from_db()
        self.assertEqual((item.rareza, item.es_destacado, item.banner_id),
                         (5, True, self.m.lim_arma.id))

    def test_los_demas_campos_del_destacado_si_se_pueden_editar(self):
        post = {'nombre': 'Verdant Renombrada', 'categoria': 'arma', 'probabilidad': '10',
                'descripcion': 'Una descripcion valida'}
        f = ItemForm(post, instance=Item.objects.get(pk=self.m.verdant.pk))
        self.assertTrue(f.is_valid(), f.errors)
        self.assertEqual(f.save().nombre, 'Verdant Renombrada')


class BannerFormTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def test_banner_valido(self):
        self.assertTrue(BannerForm(datos_banner()).is_valid())

    def test_nombre_de_menos_de_3_caracteres_se_rechaza(self):
        f = BannerForm(datos_banner(nombre='ab'))
        self.assertFalse(f.is_valid())
        self.assertIn('al menos 3', f.errors['nombre'][0])

    def test_nombre_repetido_se_rechaza(self):
        f = BannerForm(datos_banner(nombre='banner vacio'))
        self.assertFalse(f.is_valid())
        self.assertIn('Ya existe un banner', f.errors['nombre'][0])

    def test_descripcion_de_mas_de_400_se_rechaza(self):
        f = BannerForm(datos_banner(descripcion='x' * 401))
        self.assertFalse(f.is_valid())
        self.assertIn('máximo es 400', f.errors['descripcion'][0])

    def test_tipo_obligatorio_y_solo_los_tres_valores(self):
        for valor in ('', 'otro'):
            self.assertFalse(BannerForm(datos_banner(tipo=valor)).is_valid(), valor)

    # --- cambio de tipo al editar (lo que valida clean())
    def editar(self, banner, tipo):
        return BannerForm(datos_banner(nombre=banner.nombre, tipo=tipo), instance=banner)

    def test_no_se_puede_pasar_a_permanente_si_tiene_destacado(self):
        f = self.editar(self.m.lim_arma, 'permanente')
        self.assertFalse(f.is_valid())
        self.assertIn('no tiene item destacado', f.errors['tipo'][0])

    def test_no_se_puede_cambiar_a_un_tipo_que_no_admite_sus_items(self):
        f = self.editar(self.m.lim_arma, 'personaje')
        self.assertFalse(f.is_valid())
        self.assertIn('no son personajes', f.errors['tipo'][0])
        f = self.editar(self.m.lim_pj, 'arma')
        self.assertFalse(f.is_valid())
        self.assertIn('no son armas', f.errors['tipo'][0])

    def test_permanente_con_5_estrellas_sin_destacado_no_pasa_a_limitado(self):
        # Verina y Calcharo son personajes 5★ sin destacado: personaje limitado exigiria un destacado.
        f = self.editar(self.m.perm, 'personaje')
        self.assertFalse(f.is_valid())
        self.assertIn('solo puede tener como 5★ al item destacado', f.errors['tipo'][0])

    def test_conservar_el_mismo_tipo_es_valido(self):
        self.assertTrue(self.editar(self.m.lim_arma, 'arma').is_valid())

    def test_banner_vacio_puede_cambiar_a_cualquier_tipo(self):
        for tipo in ('personaje', 'arma', 'permanente'):
            self.assertTrue(self.editar(self.m.vacio, tipo).is_valid(), tipo)

    def test_al_crear_no_se_aplican_las_reglas_de_items(self):
        self.assertTrue(BannerForm(datos_banner(nombre='Otro Nuevo', tipo='arma')).is_valid())


class OtrosFormulariosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()

    def test_simular_acepta_solo_x1_y_x10(self):
        for cantidad, ok in (('1', True), ('10', True), ('5', False), ('abc', False), ('', False)):
            f = SimularTiradaForm({'banner': self.m.perm.id, 'cantidad': cantidad})
            self.assertEqual(f.is_valid(), ok, cantidad)

    def test_simular_exige_un_banner_existente(self):
        for valor in ('', '99999'):
            self.assertFalse(SimularTiradaForm({'banner': valor, 'cantidad': '1'}).is_valid(), valor)

    def test_filtro_de_banners_valida_el_tipo(self):
        self.assertTrue(FiltroBannerForm({'q': 'x', 'tipo': 'arma'}).is_valid())
        self.assertTrue(FiltroBannerForm({}).is_valid())
        self.assertFalse(FiltroBannerForm({'tipo': 'inventado'}).is_valid())

    def test_filtro_del_catalogo_valida_rareza_y_orden(self):
        self.assertTrue(FiltroCatalogoForm({'rareza': '5', 'orden': 'nombre'}).is_valid())
        self.assertFalse(FiltroCatalogoForm({'rareza': '9'}).is_valid())
        self.assertFalse(FiltroCatalogoForm({'orden': 'inventado'}).is_valid())
