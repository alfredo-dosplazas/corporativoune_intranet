import {ModuloCard, type ModuloItem} from "@/components/shared/ModuloCard.tsx";


interface Props {
    modulos: ModuloItem[];
}

export default function ModulosGrid({modulos}: Props) {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {modulos.map((modulo) => (
                <ModuloCard key={modulo.nombre} modulo={modulo}/>
            ))}
        </div>
    );
}