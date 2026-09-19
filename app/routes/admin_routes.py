from flask import Blueprint, render_template
from flask_login import login_required

from app.models.user import User
from app.models.farm import Farm
from app.models.listing import Listing
from app.utils.decorators import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@roles_required("admin")
def index():
    return render_template(
        "admin/index.html",
        users=User.query.order_by(User.id.desc()).all(),
        farm_count=Farm.query.count(),
        listing_count=Listing.query.count(),
    )
