import {useEffect} from 'react';
import {usePage} from '@inertiajs/react';
import {type DjangoFlashMessage, showDjangoToast} from "@/components/ui/ToastNotification.tsx";

export function useFlashMessages() {
    const {flash} = usePage<{ flash?: DjangoFlashMessage[] | DjangoFlashMessage }>().props;

    useEffect(() => {
        if (!flash) return;

        const messages: DjangoFlashMessage[] = Array.isArray(flash) ? flash : [flash];

        messages.forEach((msg) => {
            if (!msg || !msg.message) return;

            if (msg.level !== 'error') {
                showDjangoToast(msg);
            }
        });
    }, [flash]);
}