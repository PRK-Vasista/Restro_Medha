export const metadata = {
  title: "Restro Medha POS",
  description: "Offline-first POS dashboard"
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
