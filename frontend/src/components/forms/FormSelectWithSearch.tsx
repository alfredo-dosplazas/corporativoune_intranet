import React, {useState, useRef, useEffect} from 'react';

export interface Option {
    id: number | string;
    nombre: string;
}

interface SelectWithSearchProps {
    options: Option[];
    value: string | number;
    onChange: (value: string) => void;
    placeholder: string;
    label?: string;
    disabled?: boolean;
    className?: string;
}

export const SelectWithSearch: React.FC<SelectWithSearchProps> = ({
                                                                      options,
                                                                      value,
                                                                      onChange,
                                                                      placeholder,
                                                                      disabled = false,
                                                                      className = "",
                                                                  }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState("");
    const dropdownRef = useRef<HTMLDivElement>(null);

    const selectedOption = options.find((opt) => String(opt.id) === String(value));

    const filteredOptions = options.filter((opt) =>
        opt.nombre.toLowerCase().includes(search.toLowerCase())
    );

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleSelect = (id: number | string) => {
        onChange(String(id));
        setIsOpen(false);
        setSearch("");
    };

    const handleClear = (e: React.MouseEvent) => {
        e.stopPropagation();
        onChange("");
        setSearch("");
    };

    return (
        <div ref={dropdownRef} className={`relative ${className}`}>
            <div
                onClick={() => !disabled && setIsOpen(!isOpen)}
                className={`input input-bordered input-sm flex items-center justify-between cursor-pointer text-xs bg-base-100 ${
                    disabled ? "opacity-50 cursor-not-allowed" : "hover:border-primary"
                }`}
            >
                <span className="truncate">
                    {selectedOption ? selectedOption.nombre : placeholder}
                </span>

                <div className="flex items-center gap-1">
                    {value && !disabled && (
                        <button
                            type="button"
                            onClick={handleClear}
                            className="text-base-content/40 hover:text-error text-xs p-0.5"
                        >
                            <span className="icon-[lucide--x] block"></span>
                        </button>
                    )}
                    <span className="icon-[lucide--chevron-down] text-xs text-base-content/50"></span>
                </div>
            </div>

            {isOpen && (
                <div
                    className="absolute z-50 left-0 right-0 mt-1 bg-base-100 border border-base-200 rounded-lg shadow-xl max-h-56 flex flex-col p-1.5 animate-in fade-in zoom-in-95 duration-100">
                    <div className="relative mb-1">
                        <input
                            type="text"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder="Buscar..."
                            autoFocus
                            className="input input-bordered input-xs w-full text-xs pr-6"
                        />
                        {search && (
                            <button
                                type="button"
                                onClick={() => setSearch("")}
                                className="absolute right-2 top-1.5 text-base-content/40"
                            >
                                <span className="icon-[lucide--x] text-[10px]"></span>
                            </button>
                        )}
                    </div>

                    <ul className="overflow-y-auto flex-1 divide-y divide-base-200/50">
                        <li
                            onClick={() => handleSelect("")}
                            className={`px-2 py-1.5 text-xs rounded cursor-pointer hover:bg-primary/10 ${
                                !value ? "bg-primary/10 font-bold text-primary" : ""
                            }`}
                        >
                            {placeholder}
                        </li>
                        {filteredOptions.length > 0 ? (
                            filteredOptions.map((opt) => (
                                <li
                                    key={opt.id}
                                    onClick={() => handleSelect(opt.id)}
                                    className={`px-2 py-1.5 text-xs rounded cursor-pointer hover:bg-primary/10 truncate ${
                                        String(value) === String(opt.id)
                                            ? "bg-primary/10 font-bold text-primary"
                                            : ""
                                    }`}
                                >
                                    {opt.nombre}
                                </li>
                            ))
                        ) : (
                            <li className="px-2 py-2 text-xs text-center text-base-content/40">
                                Sin coincidencias
                            </li>
                        )}
                    </ul>
                </div>
            )}
        </div>
    );
};