import { SignIn } from "@clerk/react";

export default function Login() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-50 dark:bg-zinc-950 p-4">
      <SignIn routing="hash" />
    </div>
  );
}