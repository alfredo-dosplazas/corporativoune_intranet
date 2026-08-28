import {AppLayout} from "@/layouts/AppLayout.tsx";

type Props = {
    contacto: any;
}

export default function Directorio({contacto}: Props) {
    return (
        <AppLayout>
            {JSON.stringify(contacto, null, 2)}
        </AppLayout>
    )
}