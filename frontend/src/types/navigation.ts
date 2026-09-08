export type MenuItem = {
    key: string;
    title: string;
    icon: string;
    url_name: string;
    perms: string[];
    active_patterns: string;
    url: string;
    active: boolean;
}

export interface DockItem {
    nombre: string;
    icon: string;
    url_name: string;
    args?: any[];
    active_patterns?: string[];
    active: boolean;
    exact?: boolean;
    perms?: string[];
}

export type BreadcrumbItem = {
    label: string;
    url?: string;
    icon?: string;
};