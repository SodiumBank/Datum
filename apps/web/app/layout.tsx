import { ErrorProvider } from "../lib/error-handler";
import { AuthProvider } from "../lib/auth";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ErrorProvider>
          <AuthProvider>{children}</AuthProvider>
        </ErrorProvider>
      </body>
    </html>
  );
}
