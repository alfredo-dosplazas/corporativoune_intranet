import React from 'react';

// Wrapper para Inputs (Texto, Date, Number)
interface FormInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const FormInput: React.FC<FormInputProps> = ({ label, error, className = '', ...props }) => (
  <div className="form-control w-full">
    {label && (
      <label className="label py-0.5">
        <span className="label-text text-xs">{label}</span>
      </label>
    )}
    <input
      {...props}
      className={`input input-xs input-bordered w-full text-xs ${error ? 'input-error' : ''} ${className}`}
    />
    {error && (
      <label className="label py-0.5">
        <span className="label-text-alt text-error text-[10px]">{error}</span>
      </label>
    )}
  </div>
);

// Wrapper para Selects
interface FormSelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  options?: { value: string | number; label: string }[];
}

export const FormSelect: React.FC<FormSelectProps> = ({ label, error, options, children, className = '', ...props }) => (
  <div className="form-control w-full">
    {label && (
      <label className="label py-0.5">
        <span className="label-text text-xs">{label}</span>
      </label>
    )}
    <select
      {...props}
      className={`select select-xs select-bordered w-full text-xs ${error ? 'select-error' : ''} ${className}`}
    >
      {options
        ? options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))
        : children}
    </select>
    {error && (
      <label className="label py-0.5">
        <span className="label-text-alt text-error text-[10px]">{error}</span>
      </label>
    )}
  </div>
);

// Wrapper para Textarea
interface FormTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  error?: string;
}

export const FormTextarea: React.FC<FormTextareaProps> = ({ label, error, className = '', ...props }) => (
  <div className="form-control w-full">
    {label && (
      <label className="label py-0.5">
        <span className="label-text text-xs">{label}</span>
      </label>
    )}
    <textarea
      {...props}
      className={`textarea textarea-xs textarea-bordered w-full ${error ? 'textarea-error' : ''} ${className}`}
    />
    {error && (
      <label className="label py-0.5">
        <span className="label-text-alt text-error text-[10px]">{error}</span>
      </label>
    )}
  </div>
);