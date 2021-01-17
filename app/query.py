from django.db.models import Q
from app.models import Image
import random


def get_images_close_to_hue(hue: int, margin: int) -> 'QuerySet':
    q_effective = Q(effective_to=None)
    q_hue1 = Q(
        hue1__lte=hue+margin,
        hue1__gte=hue-margin,
    )
    q_hue2 = Q(
        hue2__lte=hue+margin,
        hue2__gte=hue-margin,
    )
    q_hue3 = Q(
        hue3__lte=hue+margin,
        hue3__gte=hue-margin,
    )
    q_hue4 = Q(
        hue4__lte=hue+margin,
        hue4__gte=hue-margin,
    )

    return Image.objects.filter(q_effective & (q_hue1 | q_hue2 | q_hue3 | q_hue4))


def get_n_random_images_with_hue_and_margin(n: int, hue: int, margin: int) -> 'QuerySet':
    # This has to be performed in two queries because we don't want to kill the database with
    #   Django's .order_by('?')
    # Of course this would also be a good place use caching (ie: memcached), but to reduce the
    #   number of dependecies for this small project I am not doing this.
    # Moreover, this returns images that are close in hue to 0, since that's the initial page state

    # We first get ids of all non-expired images in the database
    image_ids = list(get_images_close_to_hue(hue, margin).values_list('id', flat=True))

    # No pics in the database!
    if len(image_ids) == 0:
        return Image.objects.none()

    # We then pick n ids with replacement to use
    selected_ids = [ random.choice(image_ids) for i in range(n) ]

    # And lastly we query the database for these selected images
    return Image.objects.filter(id__in=selected_ids)
