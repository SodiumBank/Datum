import { ErrorProvider } from "../lib/error-handler";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ErrorProvider>{children}</ErrorProvider>
      </body>
    </html>
  );
}
