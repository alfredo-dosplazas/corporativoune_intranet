import React from 'react';
import {toast, type Toast} from 'react-hot-toast';

export type DjangoFlashMessage = {
    level: 'success' | 'info' | 'warning' | 'error' | 'debug' | string;
    message: string;
};

const LEVEL_CONFIG = {
    success: {
        borderClass: 'border-l-4 border-success',
        iconBg: 'bg-success/10 text-success',
        icon: 'icon-[heroicons--check-circle-20-solid]',
        title: 'Éxito',
    },
    error: {
        borderClass: 'border-l-4 border-error',
        iconBg: 'bg-error/10 text-error',
        icon: 'icon-[heroicons--x-circle-20-solid]',
        title: 'Error',
    },
    warning: {
        borderClass: 'border-l-4 border-warning',
        iconBg: 'bg-warning/10 text-warning',
        icon: 'icon-[heroicons--exclamation-triangle-20-solid]',
        title: 'Atención',
    },
    info: {
        borderClass: 'border-l-4 border-info',
        iconBg: 'bg-info/10 text-info',
        icon: 'icon-[heroicons--information-circle-20-solid]',
        title: 'Información',
    },
    debug: {
        borderClass: 'border-l-4 border-neutral',
        iconBg: 'bg-neutral/10 text-neutral-content',
        icon: 'icon-[heroicons--code-bracket-20-solid]',
        title: 'Debug',
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
                pointer-events-auto flex items-start gap-3 w-full max-w-sm 
                bg-base-100 text-base-content p-3.5 rounded-xl shadow-xl border border-base-200/80
                ${config.borderClass}
                transform transition-all duration-300 ease-out
                ${
                t.visible
                    ? 'opacity-100 translate-y-0 scale-100'
                    : 'opacity-0 translate-y-2 scale-95'
            }
            `}
        >
            <div className={`p-1.5 rounded-lg shrink-0 ${config.iconBg}`}>
                <span className={`${config.icon} text-lg`}/>
            </div>

            <div className="flex-1 pt-0.5 min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-wider text-base-content/50 mb-0.5">
                    {config.title}
                </p>
                <p className="text-xs font-medium text-base-content/90 leading-relaxed break-words">
                    {item.message}
                </p>
            </div>

            <button
                type="button"
                onClick={() => toast.dismiss(t.id)}
                className="btn btn-ghost btn-xs btn-circle text-base-content/40 hover:text-base-content shrink-0 -mr-1 -mt-1"
                title="Cerrar"
            >
                <span className="icon-[heroicons--x-mark-20-solid] text-sm"/>
            </button>
        </div>
    );
};

export const showDjangoToast = (item: DjangoFlashMessage) => {
    const toastId = `${item.level}-${item.message}`;

    toast.custom((t) => <ToastNotification t={t} item={item}/>, {
        id: toastId,
        duration: 4000,
        position: 'top-right',
    });
};