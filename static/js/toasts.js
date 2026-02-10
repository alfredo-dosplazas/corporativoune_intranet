function showToast(message, type = "success", timeout = 2500) {
    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");
    toast.className = `
        alert alert-${type} shadow-lg
        transition-opacity duration-300 ease-in-out
        opacity-0
    `;

    toast.innerHTML = `<span>${message}</span>`;
    container.appendChild(toast);

    // 🔥 Forzar repaint para que el fade-in funcione
    requestAnimationFrame(() => {
        toast.classList.remove("opacity-0");
    });

    // ⏳ Fade-out
    setTimeout(() => {
        toast.classList.add("opacity-0");
        setTimeout(() => toast.remove(), 300);
    }, timeout);
}