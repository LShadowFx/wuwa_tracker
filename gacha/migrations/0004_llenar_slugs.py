from django.db import migrations
from django.utils.text import slugify


def llenar_slugs(apps, schema_editor):
    Item = apps.get_model('gacha', 'Item')
    for item in Item.objects.filter(slug='').order_by('id'):
        base = slugify(item.nombre) or 'item'
        slug = base
        numero = 1
        while Item.objects.filter(slug=slug).exclude(pk=item.pk).exists():
            slug = f'{base}-{numero}'
            numero += 1
        item.slug = slug
        item.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('gacha', '0003_item_slug'),
    ]

    operations = [
        migrations.RunPython(llenar_slugs, migrations.RunPython.noop),
    ]