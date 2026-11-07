import {SignIn , SignUp} from "@clerk/react";

export default function Login(){
  return(
    <div>
      <SignIn/>
      <SignUp/>
    </div>
  );
}
