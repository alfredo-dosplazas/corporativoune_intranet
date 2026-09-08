import type {Empresa} from "@/types/empresas.ts";

type Props = {
    empresas: Empresa[];
};

export const Footer = ({
                           empresas,
                       }: Props) => {
    return (
        <footer className={`footer sm:footer-horizontal items-center py-2 px-4 bg-primary text-primary-content`}>
            <aside className="grid-flow-col items-center">
                <p>
                    © Corporativo UNE {new Date().getFullYear()} · Todos los derechos reservados.
                </p>
            </aside>
            <nav className="grid-flow-col gap-4 items-center md:place-self-center md:justify-self-end">
                {empresas.map((empresa: Empresa) => {
                    if (!empresa.logo_url) return null;

                    return (
                        <div
                            key={empresa.id || empresa.nombre}
                            title={empresa.nombre}
                            className={`size-6 transition-opacity hover:opacity-100 opacity-80 bg-white`}
                            style={{
                                maskImage: `url(${empresa.logo_url})`,
                                WebkitMaskImage: `url(${empresa.logo_url})`,
                                maskRepeat: "no-repeat",
                                WebkitMaskRepeat: "no-repeat",
                                maskPosition: "center",
                                WebkitMaskPosition: "center",
                                maskSize: "contain",
                                WebkitMaskSize: "contain",
                            }}
                        />
                    );
                })}
            </nav>
        </footer>
    );
};