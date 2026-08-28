import djangoJsReverse from 'django-js-reverse';

let urlsInstance: any = null;

/**
 * Inicializa las rutas de Django cargando el JSON de urls_json
 */
export async function initRoutes() {
  if (!urlsInstance) {
    const response = await fetch('/jsreverse.json');
    const data = await response.json();
    urlsInstance = djangoJsReverse(data);
  }
  return urlsInstance;
}

/**
 * Genera la URL de Django usando el nombre en camelCase
 */
export function getUrl(name: string, ...args: any[]): string {
  if (urlsInstance && typeof urlsInstance[name] === 'function') {
    return urlsInstance[name](...args);
  }
  console.warn(`La ruta "${name}" no está cargada o no existe.`);
  return '#';
}