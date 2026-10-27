import { ReactNode } from "react";

interface Props {
  title: string;
  value: string | number;
  description?: string;
  icon?: ReactNode;
}

export default function StatCard({
  title,
  value,
  description,
  icon,
}: Props) {
  return (
    <div className="rounded-2xl border border-white/10 bg-[#0d1117] p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-gray-400">
            {title}
          </p>

          <h3 className="mt-2 text-3xl font-bold">
            {value}
          </h3>
        </div>

        {icon && (
          <div className="rounded-xl bg-purple-500/10 p-3 text-purple-400">
            {icon}
          </div>
        )}
      </div>

      {description && (
        <p className="mt-3 text-xs text-gray-500">
          {description}
        </p>
      )}
    </div>
  );
}