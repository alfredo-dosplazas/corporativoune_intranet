import React, { useState, useEffect, useRef, useTransition } from 'react';

export interface AutocompleteOption {
  id: string | number;
  label: string;
  sublabel?: string;
}

export interface FormAsyncAutocompleteProps {
  name?: string;
  label?: string;
  error?: string;
  value?: string | number;
  onChange: (value: string | number, option?: AutocompleteOption) => void;
  fetchUrl: string;
  placeholder?: string;
  initialLabel?: string;
  disabled?: boolean;
  className?: string;
}

export const FormAsyncAutocomplete: React.FC<FormAsyncAutocompleteProps> = ({
  label,
  error,
  onChange,
  fetchUrl,
  placeholder = 'Buscar...',
  initialLabel = '',
  disabled = false,
  className = '',
}) => {
  const [query, setQuery] = useState(initialLabel);
  const [selectedLabel, setSelectedLabel] = useState(initialLabel);
  const [options, setOptions] = useState<AutocompleteOption[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState<number>(-1);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [, startTransition] = useTransition();

  useEffect(() => {
    setQuery(initialLabel);
    setSelectedLabel(initialLabel);
  }, [initialLabel]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setHighlightedIndex(-1);
        if (query !== selectedLabel) {
          setQuery(selectedLabel);
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [query, selectedLabel]);

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

          const mappedOptions: AutocompleteOption[] = rawItems.map((item: any) => ({
            id: item.id,
            label: item.text || item.label || '',
            sublabel: item.sublabel || '',
          }));

          startTransition(() => {
            setOptions(mappedOptions);
            setHighlightedIndex(-1);
          });
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
    setSelectedLabel(option.label);
    onChange(option.id, option);
    setIsOpen(false);
    setHighlightedIndex(-1);
  };

  const handleClear = () => {
    setQuery('');
    setSelectedLabel('');
    onChange('');
    setOptions([]);
    setIsOpen(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev < options.length - 1 ? prev + 1 : 0));
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex((prev) => (prev > 0 ? prev - 1 : options.length - 1));
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < options.length) {
          handleSelect(options[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        setQuery(selectedLabel);
        break;
    }
  };

  return (
    <div className="form-control w-full">
      {label && (
        <label className="label py-0.5">
          <span className="label-text text-xs">{label}</span>
        </label>
      )}

      <div ref={containerRef} className={`dropdown w-full ${isOpen ? 'dropdown-open' : ''} ${className}`}>
        <div className="relative flex items-center w-full">
          <input
            ref={inputRef}
            type="text"
            value={query}
            disabled={disabled}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            onFocus={() => setIsOpen(true)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={`input input-xs input-bordered w-full pr-12 text-xs ${
              error ? 'input-error' : ''
            }`}
          />

          {/* Botón de limpiar / Indicador de estado estilo DaisyUI */}
          <div className="absolute right-2 flex items-center gap-1">
            {query && !disabled && !loading && (
              <button
                type="button"
                onClick={handleClear}
                className="btn btn-ghost btn-xs btn-square h-4 w-4 min-h-0 text-base-content/50 hover:text-base-content"
                title="Limpiar"
              >
                ✕
              </button>
            )}

            {loading ? (
              <span className="loading loading-spinner loading-xs text-base-content/40" />
            ) : (
              <span className="icon-[heroicons--chevron-down-20-solid] text-xs text-base-content/40 pointer-events-none" />
            )}
          </div>
        </div>

        {/* Menu Dropdown 100% Nativo de DaisyUI */}
        {isOpen && (
          <ul
            tabIndex={0}
            className="dropdown-content menu menu-xs z-50 mt-1 w-full p-1 shadow-lg bg-base-100 rounded-box border border-base-200 max-h-48 overflow-y-auto"
          >
            {loading && options.length === 0 ? (
              <li className="disabled">
                <span className="text-xs text-base-content/60 justify-center">Buscando...</span>
              </li>
            ) : options.length === 0 ? (
              <li className="disabled">
                <span className="text-xs text-base-content/60 justify-center">Sin resultados</span>
              </li>
            ) : (
              options.map((opt, index) => {
                const isHighlighted = index === highlightedIndex;
                return (
                  <li key={opt.id}>
                    <button
                      type="button"
                      onClick={() => handleSelect(opt)}
                      onMouseEnter={() => setHighlightedIndex(index)}
                      className={`flex flex-col items-start gap-0 py-1.5 px-2 text-xs rounded-md ${
                        isHighlighted ? 'active' : ''
                      }`}
                    >
                      <span className="font-medium text-base-content">{opt.label}</span>
                      {opt.sublabel && (
                        <span className="text-[10px] opacity-70">{opt.sublabel}</span>
                      )}
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        )}
      </div>

      {error && (
        <label className="label py-0.5">
          <span className="label-text-alt text-error text-[10px]">{error}</span>
        </label>
      )}
    </div>
  );
};