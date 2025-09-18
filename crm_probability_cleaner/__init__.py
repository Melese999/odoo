# __init__.py at module root
from . import models

def post_init_remove_probability(env):
    from .models.ir_view_patch import remove_probability_from_views
    remove_probability_from_views(env)
