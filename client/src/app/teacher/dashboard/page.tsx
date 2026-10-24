export default function TeacherDashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">
          Trang chủ
        </h1>

        <p className="mt-1 text-sm text-gray-400">
          Tổng quan hoạt động giảng dạy
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[1, 2, 3, 4].map((item) => (
          <div
            key={item}
            className="h-28 rounded-xl border border-gray-200 bg-white"
          />
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <div className="h-72 rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900">
            Lịch giảng dạy
          </h2>

          <p className="mt-2 text-sm text-gray-400">
            Dữ liệu sẽ được tải từ API nghiệp vụ.
          </p>
        </div>

        <div className="h-72 rounded-xl border border-gray-200 bg-white p-5">
          <h2 className="font-semibold text-gray-900">
            Kiểm tra & Thi
          </h2>
        </div>
      </div>
    </div>
  );
}