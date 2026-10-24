export default function StudentDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          Trang chủ
        </h1>

        <p className="mt-1 text-sm text-gray-400">
          Tổng quan hoạt động học tập
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {[1, 2, 3].map((item) => (
          <div
            key={item}
            className="h-28 rounded-xl border border-gray-200 bg-white"
          />
        ))}
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="font-semibold text-gray-900">
          Lịch học sắp tới
        </h2>

        <p className="mt-2 text-sm text-gray-400">
          Dữ liệu sẽ được tải từ API nghiệp vụ.
        </p>
      </div>

      <div className="rounded-xl border border-gray-200 bg-white p-5">
        <h2 className="font-semibold text-gray-900">
          Kiểm tra & Thi
        </h2>
      </div>
    </div>
  );
}