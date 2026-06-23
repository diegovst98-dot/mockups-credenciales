# -*- coding: utf-8 -*-
"""Importar cada módulo de modelo puebla el registro central (registrar())."""
from . import clasica, gafete, premium  # noqa: F401
# verticales del folleto
from . import (mv1_accion, mv2_boka, mv3_banda, mv4_bandanombre,  # noqa: F401
               mv5_tech, mv6_minimal, mv7_medico, mv8_ondas)
# horizontales del folleto
from . import (mh1_digitalworld, mh2_heartfit, mh3_digitalist,  # noqa: F401
               mh4_gaio, mh5_podcast, mh6_rosestore, mh7_vegetata)
