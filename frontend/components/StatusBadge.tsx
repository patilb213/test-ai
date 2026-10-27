import { TestStatus } from "../types";

export default function StatusBadge({
  status,
}: {
  status: TestStatus;
}) {
  const styles: Record<
    TestStatus,
    string
  > = {
    PASS: "bg-green-500/10 text-green-400",
    HEALED: "bg-purple-500/10 text-purple-400",
    FAIL: "bg-red-500/10 text-red-400",
    SKIPPED: "bg-gray-500/10 text-gray-400",
  };

  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-semibold ${styles[status]}`}
    >
      {status}
    </span>
  );
}