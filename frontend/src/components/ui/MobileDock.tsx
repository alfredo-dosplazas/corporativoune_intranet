import React from "react";
import {Link, usePage} from "@inertiajs/react";
import {getUrl} from "@/utils/routes.ts";
import type {DockItem} from "@/types/navigation.ts";

type SharedProps = {
    mobile_dock?: DockItem[];
}

type Props = {
    menu?: DockItem[];
};

export const MobileDock: React.FC<Props> = ({menu}) => {
    const {props} = usePage<SharedProps>();

    // Usar la prop `menu` si se proporciona; de lo contrario, caer en `props.mobile_dock`
    const items = menu ?? props.mobile_dock ?? [];

    if (!items || items.length === 0) return null;

    return (
        <div className="dock md:hidden z-40 bg-base-100 border-t border-base-200">
            {items.map((item, index) => {
                const active = item.active;
                const targetUrl = getUrl(item.url_name, ...(item.args || []));

                return (
                    <Link
                        key={`${item.url_name}-${index}`}
                        href={targetUrl}
                        className={active ? "dock-active text-primary" : "text-base-content/70 hover:text-primary"}
                    >
                        {/* Icono adaptable */}
                        <span className={`${item.icon} size-6`}/>
                        <span className="dock-label text-[10px] font-medium">{item.nombre}</span>
                    </Link>
                );
            })}
        </div>
    );
};