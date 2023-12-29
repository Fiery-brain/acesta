user_form_fieldset = (
    (
        None,
        {
            "fields": (
                "username",
                "password",
                "registered",
                "is_active",
                "is_superuser",
            )
        },
    ),
    (
        "Персональная информация",
        {
            "fields": (
                "last_name",
                "first_name",
                "middle_name",
            )
        },
    ),
    (
        "Работа",
        {
            "fields": (
                "company",
                "position",
            )
        },
    ),
    (
        "Контакты",
        {
            "fields": (
                "city",
                "email",
                "phone",
                "purpose",
                "subscription",
                "points",
                "note",
            )
        },
    ),
    (
        "Регионы и виды туризма",
        {
            "fields": (
                "regions",
                "region",
                "current_region",
                "period_info",
                "tourism_types",
            )
        },
    ),
    ("Даты", {"fields": ("last_hit", "last_login", "date_joined")}),
)
