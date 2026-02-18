'use client';

interface LikertScaleProps {
  label: string;
  name: string;
  value: number;
  onChange: (value: number) => void;
  min?: string;
  max?: string;
  count?: number;
  required?: boolean;
}

export default function LikertScale({
  label,
  name,
  value,
  onChange,
  min = '1',
  max = '5',
  count = 5,
  required = false,
}: LikertScaleProps) {
  const points = Array.from({ length: count }, (_, i) => i + 1);

  return (
    <fieldset className="mb-6">
      <legend className="text-base font-medium text-gray-900 mb-3">
        {label}
        {required && <span className="text-red-500 ml-1">*</span>}
      </legend>

      {/* Desktop: labels on sides */}
      <div className="hidden sm:flex items-center justify-between gap-2">
        <span className="text-sm text-gray-500 w-24 text-center shrink-0">{min}</span>
        <div className="flex gap-3 flex-1 justify-center">
          {points.map((point) => (
            <label key={point} className="flex flex-col items-center cursor-pointer">
              <input
                type="radio"
                name={name}
                value={point}
                checked={value === point}
                onChange={() => onChange(point)}
                className="sr-only"
              />
              <span
                className={`w-12 h-12 rounded-full flex items-center justify-center text-base font-medium transition-all ${
                  value === point
                    ? 'bg-blue-600 text-white shadow-md scale-110'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {point}
              </span>
            </label>
          ))}
        </div>
        <span className="text-sm text-gray-500 w-24 text-center shrink-0">{max}</span>
      </div>

      {/* Mobile: labels above, buttons below */}
      <div className="sm:hidden">
        <div className="flex justify-between mb-2 px-1">
          <span className="text-xs text-gray-500">{min}</span>
          <span className="text-xs text-gray-500">{max}</span>
        </div>
        <div className="flex gap-2 justify-center">
          {points.map((point) => (
            <label key={point} className="flex flex-col items-center cursor-pointer flex-1">
              <input
                type="radio"
                name={`${name}-mobile`}
                value={point}
                checked={value === point}
                onChange={() => onChange(point)}
                className="sr-only"
              />
              <span
                className={`w-11 h-11 rounded-full flex items-center justify-center text-sm font-medium transition-all ${
                  value === point
                    ? 'bg-blue-600 text-white shadow-md scale-110'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {point}
              </span>
            </label>
          ))}
        </div>
      </div>
    </fieldset>
  );
}
