'use client';

interface CheckboxGroupProps {
  label: string;
  name: string;
  options: { value: string; label: string }[];
  values: string[];
  onChange: (values: string[]) => void;
  required?: boolean;
}

export default function CheckboxGroup({
  label,
  name,
  options,
  values,
  onChange,
  required = false,
}: CheckboxGroupProps) {
  const handleToggle = (value: string) => {
    if (values.includes(value)) {
      onChange(values.filter((v) => v !== value));
    } else {
      onChange([...values, value]);
    }
  };

  return (
    <fieldset className="mb-6">
      <legend className="text-base font-medium text-gray-900 mb-3">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </legend>
      <div className="space-y-2">
        {options.map((option) => (
          <label
            key={option.value}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors min-h-[48px] ${
              values.includes(option.value)
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:bg-gray-50'
            }`}
          >
            <input
              type="checkbox"
              name={name}
              value={option.value}
              checked={values.includes(option.value)}
              onChange={() => handleToggle(option.value)}
              className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
            />
            <span className="text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}
