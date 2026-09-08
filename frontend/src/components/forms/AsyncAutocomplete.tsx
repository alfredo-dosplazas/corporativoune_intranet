import React, { useState, useEffect, useRef } from 'react';

export interface AutocompleteOption {
    id: string | number;
    label: string;
    sublabel?: string;
}

interface AsyncAutocompleteProps {
    value?: string | number;
    onChange: (value: string | number, option?: AutocompleteOption) => void;
    fetchUrl: string;
    placeholder?: string;
    initialLabel?: string;
    error?: boolean;
    disabled?: boolean;
    className?: string;
}

export const AsyncAutocomplete: React.FC<AsyncAutocompleteProps> = ({
    value,
    onChange,
    fetchUrl,
    placeholder = 'Buscar...',
    initialLabel = '',
    error = false,
    disabled = false,
    className = '',
}) => {
    const [query, setQuery] = useState(initialLabel);
    const [options, setOptions] = useState<AutocompleteOption[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Sincronizar etiqueta inicial cuando cambien las props
    useEffect(() => {
        if (initialLabel) setQuery(initialLabel);
    }, [initialLabel]);

    // Cerrar al hacer clic fuera
    useEffect(() => {
        const handleClickOutside = (e: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Búsqueda server-side con Debounce (300ms)
    useEffect(() => {
        if (!isOpen || disabled) return;

        const timer = setTimeout(async () => {
            setLoading(true);
            try {
                const separator = fetchUrl.includes('?') ? '&' : '?';
                const res = await fetch(`${fetchUrl}${separator}q=${encodeURIComponent(query)}`);
                if (res.ok) {
                    const data = await res.json();
                    const rawItems = data.results || data || [];

                    // MAPEADOR: Soporta tanto DAL (text) como APIs estándar (label)
                    const mappedOptions: AutocompleteOption[] = rawItems.map((item: any) => ({
                        id: item.id,
                        label: item.text || item.label || '',
                        sublabel: item.sublabel || ''
                    }));

                    setOptions(mappedOptions);
                }
            } catch (err) {
                console.error('Error fetching autocomplete options:', err);
            } finally {
                setLoading(false);
            }
        }, 300);

        return () => clearTimeout(timer);
    }, [query, isOpen, fetchUrl, disabled]);

    const handleSelect = (option: AutocompleteOption) => {
        setQuery(option.label);
        onChange(option.id, option);
        setIsOpen(false);
    };

    const handleClear = () => {
        setQuery('');
        onChange('');
        setOptions([]);
    };

    return (
        <div ref={containerRef} className={`relative w-full ${className}`}>
            <div className="relative flex items-center">
                <input
                    type="text"
                    value={query}
                    disabled={disabled}
                    onChange={(e) => {
                        setQuery(e.target.value);
                        setIsOpen(true);
                    }}
                    onFocus={() => setIsOpen(true)}
                    placeholder={placeholder}
                    className={`input input-xs input-bordered w-full pr-12 text-xs font-normal ${
                        error ? 'input-error' : ''
                    }`}
                />
                <div className="absolute right-1.5 flex items-center gap-1">
                    {loading && <span className="loading loading-spinner loading-xs text-base-content/40" />}
                    {query && !disabled && (
                        <button
                            type="button"
                            onClick={handleClear}
                            className="text-base-content/40 hover:text-base-content text-xs px-1"
                        >
                            ✕
                        </button>
                    )}
                </div>
            </div>

            {/* Dropdown de Resultados */}
            {isOpen && (
                <div className="absolute z-50 w-full mt-1 bg-base-100 border border-base-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                    {loading && options.length === 0 ? (
                        <div className="p-2 text-xs text-base-content/60 text-center">Buscando...</div>
                    ) : options.length === 0 ? (
                        <div className="p-2 text-xs text-base-content/60 text-center">Sin resultados</div>
                    ) : (
                        options.map((opt) => (
                            <div
                                key={opt.id}
                                onClick={() => handleSelect(opt)}
                                className="px-2.5 py-1.5 text-xs hover:bg-primary/10 cursor-pointer flex flex-col border-b border-base-200/50 last:border-0"
                            >
                                <span className="font-semibold text-base-content">{opt.label}</span>
                                {opt.sublabel && (
                                    <span className="text-[10px] text-base-content/60">{opt.sublabel}</span>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};