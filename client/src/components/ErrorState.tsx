interface Props {
  message: string;
}

export default function ErrorState({
  message,
}: Props) {
  return (
    <div className="rounded-xl border border-red-100 bg-red-50 p-4 text-sm text-red-600">
      {message}
    </div>
  );
}