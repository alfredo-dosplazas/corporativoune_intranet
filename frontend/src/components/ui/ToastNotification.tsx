import React from 'react';
import {toast, type Toast} from 'react-hot-toast';

export type DjangoFlashMessage = {
    level: 'success' | 'info' | 'warning' | 'error' | 'debug' | string;
    message: string;
};

// Configuración visual por nivel de Django
const LEVEL_CONFIG = {
    success: {
        alertClass: 'alert-success',
        icon: 'icon-[heroicons--check-circle-20-solid]',
    },
    error: {
        alertClass: 'alert-error',
        icon: 'icon-[heroicons--x-circle-20-solid]',
    },
    warning: {
        alertClass: 'alert-warning',
        icon: 'icon-[heroicons--exclamation-triangle-20-solid]',
    },
    info: {
        alertClass: 'alert-info',
        icon: 'icon-[heroicons--information-circle-20-solid]',
    },
    debug: {
        alertClass: 'alert-neutral',
        icon: 'icon-[heroicons--code-bracket-20-solid]',
    },
};

interface ToastNotificationProps {
    t: Toast;
    item: DjangoFlashMessage;
}

export const ToastNotification: React.FC<ToastNotificationProps> = ({t, item}) => {
    const config = LEVEL_CONFIG[item.level as keyof typeof LEVEL_CONFIG] || LEVEL_CONFIG.info;

    return (
        <div
            className={`
                alert ${config.alertClass} shadow-lg rounded-xl flex items-center gap-3 max-w-md w-full
                transform transition-all duration-300 ease-in-out pointer-events-auto
                ${
                t.visible
                    ? 'opacity-100 translate-y-0 scale-100' // Estado Visible (Entrada)
                    : 'opacity-0 -translate-y-4 scale-95'   // Estado Oculto (Salida)
            }
            `}
        >
            <span className={`${config.icon} text-xl flex-none`}/>
            <div className="flex-1 text-sm font-medium leading-tight">
                {item.message}
            </div>
            <button
                type="button"
                onClick={() => toast.dismiss(t.id)}
                className="btn btn-ghost btn-xs btn-circle opacity-70 hover:opacity-100"
            >
                <span className="icon-[heroicons--x-mark-20-solid] text-base"/>
            </button>
        </div>
    );
};

export const showDjangoToast = (item: DjangoFlashMessage) => {
    toast.custom((t) => <ToastNotification t={t} item={item}/>, {
        duration: 4000,
    });
};