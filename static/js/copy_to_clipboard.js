function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast("Copiado al portapapeles 📋", "success");
    }).catch(() => {
        showToast("No se pudo copiar", "error");
    });
}