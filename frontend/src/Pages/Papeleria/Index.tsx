import {AppLayout} from "@/layouts/AppLayout.tsx";
import {type ModuloItem} from "@/components/shared/ModuloCard.tsx";
import ModulosGrid from "@/components/shared/ModulosGrid.tsx";

type Props = {
    modulos: ModuloItem[];
}

export default function Index({modulos}: Props) {
    return (
        <AppLayout title="Papelería">
            <ModulosGrid modulos={modulos}/>
        </AppLayout>
    )
}