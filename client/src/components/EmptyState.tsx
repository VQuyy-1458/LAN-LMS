interface Props {
  message: string;
}

export default function EmptyState({
  message,
}: Props) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-6 text-center text-sm text-gray-400">
      {message}
    </div>
  );
}