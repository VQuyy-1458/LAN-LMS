export default function Feedback({
  error,
  message,
}: {
  error?: string;
  message?: string;
}) {
  return (
    <>
      {error && (
        <div className="alert error" role="alert">
          {error}
        </div>
      )}
      {message && (
        <div className="alert success" role="status">
          {message}
        </div>
      )}
    </>
  );
}
