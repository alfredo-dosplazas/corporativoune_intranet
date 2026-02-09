from waitress import serve
from intranet.wsgi import application

serve(
    application,
    listen="0.0.0.0:8004",
    trusted_proxy="127.0.0.1",
    trusted_proxy_headers=["x-forwarded-for", "x-forwarded-proto"],
    clear_untrusted_proxy_headers=True,
    threads=4
)