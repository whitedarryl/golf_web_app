from flask import Blueprint

score_calc_bp = Blueprint(
    'score_calc',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/score-calc'
)

from . import routes  # Import routes to attach them
