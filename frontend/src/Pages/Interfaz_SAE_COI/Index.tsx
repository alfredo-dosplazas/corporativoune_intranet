import {AppLayout} from "@/layouts/AppLayout.tsx";
import type {PaginatedResponse} from "@/types/pagination.ts";
import DocumentosSaeTable from "@/components/interfaz_sae_coi/documentos/DocumentosTable.tsx";
import type {DocumentoSAE} from "@/types/sae.ts";

type Props = {
    data: PaginatedResponse<DocumentoSAE>;
    filters: {
        q: string;
        mes: string;
        anio: string;
        almacen: string;
        estado_conta: string;
        tipo_documento: string;
    };
    options: {
        tipos_documentos: { value: string; label: string }[];
        almacenes: string[];
    };
};

export default function Interfaz_SAE_COI({data, filters, options}: Props) {
    return (
        <AppLayout title="Documentos SAE" scrollable={false}>
            <DocumentosSaeTable
                paginatedData={data}
                filters={filters}
                options={options}
            />
        </AppLayout>
    );
}