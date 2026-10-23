from django.urls import path
from apps.explorador import views

urlpatterns = [
    # --- Servidor DP ---
    path(
        "explorador-red-dp/",
        views.RedExploradorView.as_view(),
        {"server_root_attr": "DP_SERVER_ROOT", "url_prefix": "explorador-red-dp"},
        name="explorador_red_dp_root",
    ),
    path(
        "explorador-red-dp/archivo/<path:ruta>/",
        views.ver_archivo_red,
        {"server_root_attr": "DP_SERVER_ROOT"},
        name="explorador_red_dp_archivo",
    ),
    path(
        "explorador-red-dp/onlyoffice-token/<path:ruta>/",
        views.token_onlyoffice_view,
        {"server_root_attr": "DP_SERVER_ROOT", "url_prefix": "explorador-red-dp"},
        name="onlyoffice_dp_token",
    ),
    path(
        "explorador-red-dp/<path:ruta>/",
        views.RedExploradorView.as_view(),
        {"server_root_attr": "DP_SERVER_ROOT", "url_prefix": "explorador-red-dp"},
        name="explorador_red_dp_path",
    ),

    # --- Servidor FP ---
    path(
        "explorador-red/",
        views.RedExploradorView.as_view(),
        {"server_root_attr": "FP_SERVER_ROOT", "url_prefix": "explorador-red"},
        name="explorador_red_root",
    ),
    path(
        "explorador-red/archivo/<path:ruta>/",
        views.ver_archivo_red,
        {"server_root_attr": "FP_SERVER_ROOT"},
        name="explorador_red_archivo",
    ),
    path(
        "explorador-red/onlyoffice-token/<path:ruta>/",
        views.token_onlyoffice_view,
        {"server_root_attr": "FP_SERVER_ROOT", "url_prefix": "explorador-red"},
        name="onlyoffice_token",
    ),
    path(
        "explorador-red/<path:ruta>/",
        views.RedExploradorView.as_view(),
        {"server_root_attr": "FP_SERVER_ROOT", "url_prefix": "explorador-red"},
        name="explorador_red_path",
    ),
]