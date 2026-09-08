import type {ReactNode} from "react";

interface FormFieldProps {
    label: string;
    name: string;
    error?: string | string[];
    helpText?: string;
    required?: boolean;
    children: ReactNode;
    className?: string;
}

export const FormField: React.FC<FormFieldProps> = ({
                                                        label,
                                                        name,
                                                        error,
                                                        helpText,
                                                        required = false,
                                                        children,
                                                        className = '',
                                                    }) => {
    const errorMessages = Array.isArray(error) ? error : error ? [error] : [];
    const hasError = errorMessages.length > 0;

    return (
        <div className={`form-control w-full ${className}`}>
            <label htmlFor={name} className="py-0.5 flex justify-between items-center">
                <span className="text-[11px] font-semibold text-base-content/80 uppercase tracking-tight">
                    {label} {required && <span className="text-error">*</span>}
                </span>
            </label>

            {children}

            {helpText && !hasError && (
                <span className="text-[10px] text-base-content/50 mt-0.5">{helpText}</span>
            )}

            {hasError && (
                <div className="space-y-0.5 mt-0.5">
                    {errorMessages.map((msg, index) => (
                        <div key={index}
                             className="flex items-center gap-1 text-[10px] text-error leading-tight font-medium">
                            <span className="icon-[heroicons--exclamation-circle-20-solid] text-xs flex-none"/>
                            <span>{msg}</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};