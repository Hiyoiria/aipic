'use client';

interface TextAreaProps {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  maxLength?: number;
  required?: boolean;
  rows?: number;
}

export default function TextArea({
  label,
  name,
  value,
  onChange,
  placeholder = '',
  maxLength = 500,
  required = false,
  rows = 4,
}: TextAreaProps) {
  return (
    <div className="mb-6">
      <label htmlFor={name} className="block text-base font-medium text-gray-900 mb-2">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <textarea
        id={name}
        name={name}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        maxLength={maxLength}
        rows={rows}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-gray-700"
      />
      {maxLength && (
        <p className="text-sm text-gray-400 mt-1 text-right">
          {value.length}/{maxLength}
        </p>
      )}
    </div>
  );
}
