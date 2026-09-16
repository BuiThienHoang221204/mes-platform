/**
 * Sinh cả bộ icon PWA từ MỘT nguồn duy nhất — logo Amphenol RF.
 *
 *   node scripts/generate-pwa-icons.mjs
 *
 * Vì sao phải sinh chứ không vẽ tay từng cái: bốn tệp dưới đây phải giống hệt
 * nhau, mà sửa tay bốn lần thì sớm muộn lệch một cái, và cái lệch đó chỉ lộ ra
 * trên màn hình chính của iPad — nơi không ai để ý.
 *
 *   icon-192x192.png       Android, danh sách ứng dụng
 *   icon-512x512.png       Android, màn hình chờ khi mở app
 *   icon-maskable-512.png  Android tự bo góc — phải chừa lề an toàn 20%
 *   apple-touch-icon.png   iOS BỎ QUA manifest.json, chỉ đọc thẻ <link> này
 *
 * Logo gốc là chữ TRẮNG + VÀNG vẽ cho nền tối, nên nền icon luôn là màu tối của
 * app. Không được để nền trong suốt: iOS tự độn nền ĐEN, còn Android độn TRẮNG —
 * cùng một tệp ra hai kết quả khác nhau.
 */
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import sharp from "sharp";

const PUBLIC = path.join(process.cwd(), "public");
const LOGO = path.join(PUBLIC, "AmphenolRF-Logo.svg");
const GROUND = "#0D0F12"; // --color-bg của lớp `.dark`

/** Tỉ lệ bề ngang logo chiếm trong ô vuông. Maskable hẹp hơn vì bị bo góc ăn mất. */
const BO = [
  { ten: "icon-192x192.png", canh: 192, rong: 0.78 },
  { ten: "icon-512x512.png", canh: 512, rong: 0.78 },
  { ten: "icon-maskable-512.png", canh: 512, rong: 0.6 },
  { ten: "apple-touch-icon.png", canh: 180, rong: 0.78 },
];

const ACCENT = "#22B8CF"; // --color-accent của theme tối

/**
 * Chữ "MES" to ở giữa, logo Amphenol nhỏ bên dưới.
 *
 * Logo gốc là chữ NẰM NGANG tỉ lệ 241×35: nhét nguyên vào ô vuông thì ở cỡ 192px
 * nó chỉ cao 22px — nhìn từ màn hình chính iPad gần như không đọc được. Icon phải
 * nhận ra trong nửa giây, nên phần to là chữ MES, logo chỉ để ghi nhận thương hiệu.
 */
async function sinh({ ten, canh, rong }) {
  const wLogo = Math.round(canh * rong);
  const hLogo = Math.round((wLogo * 35) / 241);

  const logo = await sharp(LOGO, { density: 900 })
    .resize(wLogo, hLogo, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .png()
    .toBuffer();

  // Chữ vẽ bằng SVG để không phụ thuộc font cài trên máy — sharp tự dựng hình.
  const coChu = Math.round(canh * rong * 0.42);
  const chu = Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${canh}" height="${canh}">
       <text x="50%" y="46%" text-anchor="middle" dominant-baseline="middle"
             font-family="Arial Black, Arial, sans-serif" font-weight="700"
             font-size="${coChu}" letter-spacing="${Math.round(coChu * 0.04)}"
             fill="${ACCENT}">MES</text>
     </svg>`,
  );

  const out = await sharp({
    create: { width: canh, height: canh, channels: 4, background: GROUND },
  })
    .composite([
      { input: chu, top: 0, left: 0 },
      // Toạ độ TƯỜNG MINH: truyền cả `gravity` lẫn `top/left` thì sharp lấy
      // top/left và bỏ qua gravity — logo sẽ dán lên góc trên, đè vào chữ.
      { input: logo, top: canh - hLogo - Math.round(canh * 0.1), left: Math.round((canh - wLogo) / 2) },
    ])
    // R27 — iOS độn nền ĐEN vào chỗ trong suốt, Android độn TRẮNG: cùng một tệp
    // ra hai kết quả. `flatten` trộn nền vào, `removeAlpha` bỏ hẳn kênh alpha —
    // thiếu bước hai thì tệp vẫn còn 4 kênh và vẫn có công cụ hiểu nhầm là có nền trong.
    .flatten({ background: GROUND })
    .removeAlpha()
    .png()
    .toBuffer();

  await writeFile(path.join(PUBLIC, ten), out);
  console.log(`  ${ten.padEnd(24)} ${canh}×${canh}  chữ ${coChu}px  logo ${wLogo}×${hLogo}`);
}

await mkdir(PUBLIC, { recursive: true });
console.log("Sinh icon PWA từ AmphenolRF-Logo.svg:");
for (const b of BO) await sinh(b);
console.log("Xong. Nhớ chạy lại nếu logo đổi.");
