"""Pruebas de INTEGRACION: vistas + formularios + modelos + plantillas trabajando juntos,
con el cliente de pruebas de Django (peticiones HTTP reales contra la aplicacion)."""
from django.test import TestCase
from django.urls import reverse

from gacha import views
from gacha.models import Banner, EstadoPity, Item, Tirada

from .helpers import crear_mundo, crear_usuarios, datos_banner, datos_item, json_script


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.m = crear_mundo()
        cls.u = crear_usuarios()

    def entrar(self, usuario):
        self.client.force_login(usuario)

    def mensajes(self, respuesta):
        return [str(x) for x in respuesta.context['messages']]


class PermisosTests(Base):
    """Matriz de perfiles: visitante, jugador, staff y admin (ver comentario de views.py)."""

    def codigo(self, nombre, usuario=None, args=None, post=False):
        if usuario:
            self.client.force_login(usuario)
        url = reverse(nombre, args=args or [])
        r = self.client.post(url) if post else self.client.get(url)
        self.client.logout()
        return r.status_code

    def test_paginas_publicas_las_ve_un_visitante(self):
        casos = [('gacha:catalogo', []), ('gacha:banners', []), ('gacha:feed', []),
                 ('gacha:banner_detalle', [self.m.perm.id]), ('gacha:item_detalle', [self.m.jiyan.slug])]
        for nombre, args in casos:
            self.assertEqual(self.codigo(nombre, args=args), 200, nombre)

    def test_paginas_con_sesion_redirigen_al_login(self):
        for nombre in ('gacha:dashboard', 'gacha:simular', 'gacha:resultado', 'gacha:item_gestionar',
                       'gacha:banner_gestionar', 'gacha:item_crear', 'gacha:banner_crear'):
            r = self.client.get(reverse(nombre))
            self.assertEqual(r.status_code, 302, nombre)
            self.assertIn('/cuentas/login/', r.url, nombre)

    def test_gestionar_lo_ven_staff_y_admin_pero_no_el_jugador(self):
        for nombre in ('gacha:item_gestionar', 'gacha:banner_gestionar'):
            self.assertEqual(self.codigo(nombre, self.u.jugador), 403, nombre)
            self.assertEqual(self.codigo(nombre, self.u.staff), 200, nombre)
            self.assertEqual(self.codigo(nombre, self.u.admin), 200, nombre)

    def test_crear_solo_el_admin(self):
        for nombre in ('gacha:item_crear', 'gacha:banner_crear'):
            self.assertEqual(self.codigo(nombre, self.u.jugador), 403, nombre)
            self.assertEqual(self.codigo(nombre, self.u.staff), 403, nombre)
            self.assertEqual(self.codigo(nombre, self.u.admin), 200, nombre)

    def test_editar_staff_y_admin_si_jugador_no(self):
        casos = [('gacha:item_editar', [self.m.danjin.id]), ('gacha:banner_editar', [self.m.vacio.id])]
        for nombre, args in casos:
            self.assertEqual(self.codigo(nombre, self.u.jugador, args), 403, nombre)
            self.assertEqual(self.codigo(nombre, self.u.staff, args), 200, nombre)
            self.assertEqual(self.codigo(nombre, self.u.admin, args), 200, nombre)

    def test_eliminar_solo_el_admin_y_solo_por_post(self):
        casos = [('gacha:item_eliminar', [self.m.danjin.id]), ('gacha:banner_eliminar', [self.m.vacio.id])]
        for nombre, args in casos:
            self.assertEqual(self.codigo(nombre, self.u.staff, args, post=True), 403, nombre)
            self.assertEqual(self.codigo(nombre, self.u.jugador, args, post=True), 403, nombre)
            self.assertEqual(self.codigo(nombre, self.u.admin, args), 405, nombre + ' por GET')
        self.assertTrue(Item.objects.filter(pk=self.m.danjin.id).exists())
        self.assertTrue(Banner.objects.filter(pk=self.m.vacio.id).exists())

    def test_staff_y_jugador_no_ven_los_botones_de_crear_ni_eliminar(self):
        self.entrar(self.u.staff)
        html = self.client.get(reverse('gacha:item_gestionar')).content.decode()
        self.assertNotIn('Crear personaje o arma', html)
        self.assertNotIn('data-confirmar', html)
        self.client.logout()
        self.entrar(self.u.admin)
        html = self.client.get(reverse('gacha:item_gestionar')).content.decode()
        self.assertIn('Crear personaje o arma', html)
        self.assertIn('data-confirmar', html)


class GestionarItemsTests(Base):
    """Filtros en vivo + paginacion de 10 en la tabla de items."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for n in range(17):  # 8 items del mundo + 17 = 25 -> 3 paginas
            Item.objects.create(nombre=f'Relleno {n:02d}', categoria='arma' if n % 2 else 'personaje',
                                rareza=4, banner=cls.m.perm)

    def ir(self, **params):
        self.entrar(self.u.staff)
        return self.client.get(reverse('gacha:item_gestionar'), params)

    def test_pagina_de_a_10_con_total_correcto(self):
        r = self.ir()
        self.assertEqual(len(r.context['pagina']), 10)
        self.assertEqual(r.context['pagina'].paginator.num_pages, 3)
        self.assertEqual(r.context['total'], 25)

    def test_ultima_pagina_tiene_el_resto(self):
        self.assertEqual(len(self.ir(page=3).context['pagina']), 5)

    def test_pagina_fuera_de_rango_cae_en_la_ultima_y_no_revienta(self):
        r = self.ir(page=999)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['pagina'].number, 3)

    def test_pagina_con_letras_cae_en_la_primera(self):
        self.assertEqual(self.ir(page='abc').context['pagina'].number, 1)

    def test_buscador_por_nombre_sin_importar_mayusculas(self):
        r = self.ir(q='jIYan')
        self.assertEqual([i.nombre for i in r.context['pagina']], ['Jiyan'])

    def test_filtro_por_categoria_rareza_y_banner(self):
        self.assertEqual(self.ir(categoria='arma').context['total'],
                         Item.objects.filter(categoria='arma').count())
        self.assertEqual(self.ir(rareza='5').context['total'], 4)
        self.assertEqual(self.ir(banner=self.m.lim_arma.id).context['total'], 2)

    def test_filtros_combinados(self):
        r = self.ir(categoria='personaje', rareza='5', banner=self.m.perm.id)
        self.assertEqual(sorted(i.nombre for i in r.context['pagina']), ['Calcharo', 'Verina'])

    def test_sin_resultados_muestra_mensaje_y_enlace_para_ver_todos(self):
        r = self.ir(q='zzzzzz')
        self.assertEqual(r.context['total'], 0)
        self.assertContains(r, 'No hay personajes ni armas que coincidan')

    def test_filtro_invalido_no_revienta_y_muestra_todo(self):
        r = self.ir(rareza='9', orden='inventado')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context['total'], 25)

    def test_orden_por_nombre(self):
        nombres = [i.nombre for i in self.ir(orden='nombre').context['pagina']]
        self.assertEqual(nombres, sorted(nombres))

    def test_los_enlaces_de_paginacion_conservan_los_filtros(self):
        r = self.ir(categoria='personaje')
        self.assertEqual(r.context['querystring'], 'categoria=personaje')
        self.assertContains(r, 'categoria=personaje&amp;page=2')

    def test_la_pagina_trae_lo_que_necesita_filtros_vivos_js(self):
        r = self.ir()
        self.assertContains(r, 'data-filtros-vivos')
        self.assertContains(r, 'data-resultados="resultadosGestion"')
        self.assertContains(r, 'id="resultadosGestion"')
        self.assertContains(r, 'js/filtros_vivos.js')

    def test_la_peticion_ajax_devuelve_la_misma_zona_de_resultados(self):
        self.entrar(self.u.staff)
        r = self.client.get(reverse('gacha:item_gestionar'), {'q': 'jiyan'},
                            headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertContains(r, 'id="resultadosGestion"')
        self.assertContains(r, 'Jiyan')
        self.assertNotContains(r, 'Calcharo')


class GestionarBannersTests(Base):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        for n in range(11):  # 4 del mundo + 11 = 15 -> 2 paginas
            Banner.objects.create(nombre=f'Banner Extra {n:02d}', tipo='permanente')

    def ir(self, **params):
        self.entrar(self.u.staff)
        return self.client.get(reverse('gacha:banner_gestionar'), params)

    def test_pagina_de_a_10(self):
        r = self.ir()
        self.assertEqual((len(r.context['pagina']), r.context['total']), (10, 15))
        self.assertEqual(len(self.ir(page=2).context['pagina']), 5)

    def test_buscador_y_tipo(self):
        self.assertEqual(self.ir(q='prueba').context['total'], 3)
        self.assertEqual(self.ir(tipo='arma').context['total'], 2)
        self.assertEqual([b.nombre for b in self.ir(q='prueba', tipo='arma').context['pagina']], ['Arma Prueba'])

    def test_tipo_invalido_no_revienta(self):
        r = self.ir(tipo='inventado')
        self.assertEqual((r.status_code, r.context['total']), (200, 15))

    def test_trae_los_marcadores_del_filtro_en_vivo(self):
        r = self.ir()
        self.assertContains(r, 'data-filtros-vivos')
        self.assertContains(r, 'id="resultadosGestion"')


class DatosParaElJavaScriptTests(Base):
    """El JS del formulario depende del formato exacto de estos datos."""

    def test_grupos_incluyen_todos_los_banners_con_tipo_e_items(self):
        grupos = views._grupos_probabilidad()
        self.assertEqual(set(grupos), {str(b.id) for b in Banner.objects.all()})
        self.assertEqual(grupos[str(self.m.vacio.id)], {'tipo': 'arma', 'items': []})
        self.assertEqual(grupos[str(self.m.perm.id)]['tipo'], 'permanente')

    def test_cada_item_trae_categoria_y_destacado(self):
        items = views._grupos_probabilidad()[str(self.m.lim_arma.id)]['items']
        verdant = next(i for i in items if i['nombre'] == 'Verdant Summit')
        self.assertEqual(verdant, {'id': self.m.verdant.id, 'nombre': 'Verdant Summit', 'rareza': 5,
                                   'peso': 10, 'categoria': 'arma', 'destacado': True})

    def test_el_formulario_de_items_los_publica_en_el_html(self):
        self.entrar(self.u.admin)
        for url in (reverse('gacha:item_crear'), reverse('gacha:item_editar', args=[self.m.danjin.id])):
            datos = json_script(self.client.get(url).content.decode(), 'datos-prob')
            self.assertIn(str(self.m.lim_pj.id), datos, url)

    def test_resumen_de_items_de_un_banner(self):
        self.assertEqual(views._resumen_items_banner(self.m.perm),
                         {'personajes': 4, 'armas': 0, 'destacados': 0, 'cinco_sin_destacado': 2})
        self.assertEqual(views._resumen_items_banner(self.m.lim_arma),
                         {'personajes': 0, 'armas': 2, 'destacados': 1, 'cinco_sin_destacado': 0})

    def test_el_formulario_de_banner_publica_el_resumen_solo_al_editar(self):
        self.entrar(self.u.admin)
        html = self.client.get(reverse('gacha:banner_editar', args=[self.m.lim_arma.id])).content.decode()
        self.assertEqual(json_script(html, 'datos-banner')['destacados'], 1)
        self.assertIn('js/banner_reglas.js', html)
        html = self.client.get(reverse('gacha:banner_crear')).content.decode()
        self.assertIsNone(json_script(html, 'datos-banner'))
        self.assertNotIn('banner_reglas.js', html)


class CrearItemTests(Base):
    def setUp(self):
        self.entrar(self.u.admin)
        self.url = reverse('gacha:item_crear')

    def test_crear_item_valido_redirige_al_detalle_con_mensaje(self):
        r = self.client.post(self.url, datos_item(self.m.perm, nombre='Aalto'), follow=True)
        self.assertRedirects(r, reverse('gacha:item_detalle', args=['aalto']))
        self.assertIn('Se creó «Aalto»', self.mensajes(r)[0])
        self.assertTrue(Item.objects.filter(nombre='Aalto').exists())

    def test_item_invalido_no_se_guarda_y_marca_el_campo(self):
        antes = Item.objects.count()
        r = self.client.post(self.url, datos_item(self.m.lim_pj, categoria='arma'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'solo admite personajes')
        self.assertEqual(Item.objects.count(), antes)

    def test_segundo_destacado_se_rechaza_con_el_nombre_del_actual(self):
        r = self.client.post(self.url, datos_item(self.m.lim_arma, categoria='arma', rareza='5',
                                                  es_destacado='on'))
        self.assertContains(r, 'ya tiene un destacado (Verdant Summit)')

    def test_5_estrellas_sin_destacado_en_limitado_se_rechaza(self):
        r = self.client.post(self.url, datos_item(self.m.vacio, categoria='arma', rareza='5'))
        self.assertContains(r, 'debe ser el destacado')

    def test_banner_se_puede_preseleccionar_por_la_url(self):
        r = self.client.get(self.url, {'banner': self.m.lim_pj.id})
        self.assertEqual(r.context['form'].initial['banner'], str(self.m.lim_pj.id))


class EditarItemTests(Base):
    def test_staff_edita_la_probabilidad(self):
        self.entrar(self.u.staff)
        r = self.client.post(reverse('gacha:item_editar', args=[self.m.sanhua.id]),
                             datos_item(self.m.perm, nombre='Sanhua', probabilidad='50'), follow=True)
        self.assertIn('Se actualizó «Sanhua»', self.mensajes(r)[0])
        self.m.sanhua.refresh_from_db()
        self.assertEqual(self.m.sanhua.probabilidad, 50)

    def test_editar_con_error_muestra_aviso_y_no_guarda(self):
        self.entrar(self.u.staff)
        r = self.client.post(reverse('gacha:item_editar', args=[self.m.sanhua.id]),
                             datos_item(self.m.perm, nombre='Sanhua', probabilidad='500'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('No se pudo guardar', self.mensajes(r)[0])
        self.m.sanhua.refresh_from_db()
        self.assertEqual(self.m.sanhua.probabilidad, 10)

    def test_el_destacado_de_un_limitado_se_edita_con_campos_fijos(self):
        self.entrar(self.u.admin)
        url = reverse('gacha:item_editar', args=[self.m.verdant.id])
        r = self.client.get(url)
        self.assertTrue(r.context['form'].destacado_fijo)
        self.assertContains(r, 'quedan fijos')
        self.assertContains(r, 'Arma Prueba')  # el aviso nombra el banner
        # el formulario real no envia los campos fijos (disabled): solo nombre y datos libres
        r = self.client.post(url, {'nombre': 'Verdant Nueva', 'categoria': 'arma', 'probabilidad': '10',
                                   'descripcion': ''}, follow=True)
        self.assertIn('Se actualizó', self.mensajes(r)[0])
        self.m.verdant.refresh_from_db()
        self.assertEqual((self.m.verdant.nombre, self.m.verdant.rareza, self.m.verdant.es_destacado),
                         ('Verdant Nueva', 5, True))

    def test_regresion_post_manipulado_no_deja_al_banner_sin_destacado(self):
        """El hueco original: bajar a 4★ + desmarcar + mover de banner en un solo envio."""
        self.entrar(self.u.admin)
        self.client.post(reverse('gacha:item_editar', args=[self.m.verdant.id]),
                         datos_item(self.m.perm, nombre='Verdant Summit', categoria='arma', rareza='4'))
        self.m.verdant.refresh_from_db()
        self.assertEqual((self.m.verdant.rareza, self.m.verdant.es_destacado, self.m.verdant.banner_id),
                         (5, True, self.m.lim_arma.id))
        self.assertEqual(self.m.lim_arma.item_destacado(), self.m.verdant)

    def test_un_item_normal_no_trae_campos_fijos_ni_aviso(self):
        self.entrar(self.u.admin)
        r = self.client.get(reverse('gacha:item_editar', args=[self.m.espada4.id]))
        self.assertFalse(r.context['form'].destacado_fijo)
        self.assertNotContains(r, 'quedan fijos')

    def test_item_inexistente_da_404(self):
        self.entrar(self.u.admin)
        self.assertEqual(self.client.get(reverse('gacha:item_editar', args=[99999])).status_code, 404)


class BannerCrudTests(Base):
    def test_crear_banner_valido(self):
        self.entrar(self.u.admin)
        r = self.client.post(reverse('gacha:banner_crear'), datos_banner(nombre='Nuevo Banner'), follow=True)
        self.assertIn('Se creó el banner «Nuevo Banner»', self.mensajes(r)[0])

    def test_crear_banner_con_nombre_repetido(self):
        self.entrar(self.u.admin)
        r = self.client.post(reverse('gacha:banner_crear'), datos_banner(nombre='Banner Vacio'))
        self.assertContains(r, 'Ya existe un banner')

    def test_cambio_de_tipo_incompatible_no_se_guarda(self):
        self.entrar(self.u.admin)
        url = reverse('gacha:banner_editar', args=[self.m.lim_arma.id])
        r = self.client.post(url, datos_banner(nombre='Arma Prueba', tipo='permanente'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'no tiene item destacado')
        self.m.lim_arma.refresh_from_db()
        self.assertEqual(self.m.lim_arma.tipo, 'arma')

    def test_cambio_de_tipo_compatible_se_guarda(self):
        self.entrar(self.u.staff)
        url = reverse('gacha:banner_editar', args=[self.m.vacio.id])
        r = self.client.post(url, datos_banner(nombre='Banner Vacio', tipo='personaje'), follow=True)
        self.assertIn('Se actualizó el banner', self.mensajes(r)[0])
        self.m.vacio.refresh_from_db()
        self.assertEqual(self.m.vacio.tipo, 'personaje')

    def test_el_resumen_llega_al_contexto_tambien_cuando_hay_error(self):
        self.entrar(self.u.admin)
        r = self.client.post(reverse('gacha:banner_editar', args=[self.m.lim_arma.id]),
                             datos_banner(nombre='Arma Prueba', tipo='personaje'))
        self.assertEqual(r.context['resumen_items']['armas'], 2)


class EliminarTests(Base):
    def setUp(self):
        self.entrar(self.u.admin)

    def test_eliminar_item_sin_tiradas(self):
        r = self.client.post(reverse('gacha:item_eliminar', args=[self.m.sanhua.id]), follow=True)
        self.assertIn('Se eliminó «Sanhua»', self.mensajes(r)[0])
        self.assertFalse(Item.objects.filter(pk=self.m.sanhua.id).exists())

    def test_item_con_tiradas_queda_protegido(self):
        Tirada.objects.create(usuario=self.u.jugador, banner=self.m.perm, item=self.m.danjin, pity_en_momento=3)
        r = self.client.post(reverse('gacha:item_eliminar', args=[self.m.danjin.id]), follow=True)
        self.assertIn('No se puede eliminar «Danjin»', self.mensajes(r)[0])
        self.assertIn('1 tirada', self.mensajes(r)[0])
        self.assertTrue(Item.objects.filter(pk=self.m.danjin.id).exists())

    def test_banner_vacio_se_elimina(self):
        self.client.post(reverse('gacha:banner_eliminar', args=[self.m.vacio.id]))
        self.assertFalse(Banner.objects.filter(pk=self.m.vacio.id).exists())

    def test_banner_con_items_queda_protegido_y_dice_cuantos(self):
        r = self.client.post(reverse('gacha:banner_eliminar', args=[self.m.lim_arma.id]), follow=True)
        self.assertIn('2 items asociados', self.mensajes(r)[0])
        self.assertTrue(Banner.objects.filter(pk=self.m.lim_arma.id).exists())

    def test_banner_con_pity_registrado_tambien_queda_protegido(self):
        EstadoPity.objects.create(usuario=self.u.jugador, banner=self.m.vacio, pity_actual=5)
        r = self.client.post(reverse('gacha:banner_eliminar', args=[self.m.vacio.id]), follow=True)
        self.assertIn('1 registro de pity', self.mensajes(r)[0])
        self.assertTrue(Banner.objects.filter(pk=self.m.vacio.id).exists())
