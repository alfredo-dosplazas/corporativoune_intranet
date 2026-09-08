import React from "react";
import {Link} from "@inertiajs/react";
import type {BreadcrumbItem} from "@/types/navigation.ts";

type Props = {
    breadcrumbs?: BreadcrumbItem[];
};

export const Breadcrumbs: React.FC<Props> = ({breadcrumbs}) => {
    const items = breadcrumbs && breadcrumbs.length > 0 ? breadcrumbs : [];

    if (!items.length) return null;

    return (
        /* Oculto en pantallas pequeñas, visible en medianas en adelante */
        <div className="hidden md:block bg-base-100 px-6 text-xs breadcrumbs py-1.5 border-b border-base-200">
            <ul>
                {items.map((item, index) => {
                    const isLast = index === items.length - 1;

                    return (
                        <li key={index} className={isLast ? "font-semibold text-primary" : ""}>
                            {isLast ? (
                                <span className="inline-flex items-center gap-1.5 text-primary">
                                    {item.icon && <span className={`${item.icon} text-base shrink-0`}/>}
                                    {item.label}
                                </span>
                            ) : (
                                <Link
                                    href={item.url || '#'}
                                    className="inline-flex items-center gap-1.5 text-base-content/70 hover:text-primary transition-colors"
                                >
                                    {item.icon && <span className={`${item.icon} text-base shrink-0`}/>}
                                    {item.label}
                                </Link>
                            )}
                        </li>
                    );
                })}
            </ul>
        </div>
    );
};