import { SignIn } from "@clerk/react";
import "./react-login-signup.css";

export default function Login() {
  return (
    <div className="login-container">
      <SignIn routing="hash" />
    </div>
  );
}
