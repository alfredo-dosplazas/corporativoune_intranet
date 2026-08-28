import 'vite/modulepreload-polyfill';
import {createInertiaApp} from '@inertiajs/react'
import {initRoutes} from "./utils/routes.ts";

import './index.css'

initRoutes().then(() => {
    createInertiaApp({
        strictMode: true,
        http: {
            xsrfCookieName: 'csrftoken',
            xsrfHeaderName: 'X-CSRFToken',
        },
    })
});
