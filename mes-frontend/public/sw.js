// R24/R25 — service worker VIẾT TAY. Không dùng next-pwa: Workbox cache rất hăng,
// mà MES thì mọi con số đều là số sống. Cache nhầm một hàng đợi là người ở trạm
// nhìn thấy lệnh đã bị trạm khác lấy mất.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("fetch", (event) => {
  // Chỉ đụng tới điều hướng trang. API đi thẳng, KHÔNG qua tay service worker.
  // Handler này gần như không làm gì — nhưng phải có, vì trình duyệt đòi có nó
  // mới cho cài ứng dụng. Đừng thấy nó rỗng rồi xoá đi.
  if (event.request.mode !== "navigate") return;
  event.respondWith(fetch(event.request));
});
