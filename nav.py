from flask_nav import Nav
from flask_nav.elements import Navbar, View, Subgroup


# navbar itself
def top_nav(username, balance):
    if username is None:
        return Navbar(
            View('TopItUp', 'frontend.index'),
            View('Log in', 'login_bp.index'),
        )
    else:
        return Navbar(
            View('TopItUp', 'frontend.index'),
            Subgroup(
                username,
                View('Logout', 'login_bp.logout')
            ),
            Subgroup(
                "Your balance: "+str(balance),
                View('Add more credits', 'siema.new'),
                View('Your invoices history', 'siema.index'),
            ),
        )

nav = Nav()
