def get_redirect_url(user):

    role = user.role

    routing = {
        "super_admin": "/dashboard/",

        "managing_director": "/dashboard/executive/",

        "operations_manager": "/dashboard/operations/",

        "finance_manager": "/finance/dashboard/",

        "hr_manager": "/hr/dashboard/",

        "inventory_officer": "/inventory/dashboard/",

        "collection_officer": "/waste/dashboard/",

        "data_entry_clerk": "/dashboard/data-entry/",

        "viewer": "/dashboard/",
    }

    return routing.get(role, "/dashboard/")