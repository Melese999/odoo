# -*- coding: utf-8 -*-

from . import controllers
from . import models

def pre_init_hook(cr):
    """Initialize module dependencies"""
    pass

def post_init_hook(cr, registry):
    """Initialize module data after installation"""
    pass
