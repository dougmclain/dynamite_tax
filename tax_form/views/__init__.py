# tax_form/views/__init__.py
from .main import *  # Import all from main.py
from .association import AssociationView
from .financial import *
from . import create_association
from .dashboard import DashboardView
from .edit_association import EditAssociationView
from .edit_tax_year_info import EditTaxYearInfoView
from .extension import ExtensionFormView