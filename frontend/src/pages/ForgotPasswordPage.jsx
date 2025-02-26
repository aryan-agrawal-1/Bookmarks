import { ForgotPasswordForm } from "../components/forgot-password-form";
import {Card, CardHeader, CardTitle, CardDescription, CardContent} from "../components/ui/card"

export default function ForgotPasswordPage() {
    return (
      <div className="flex items-center justify-center m-auto h-[100vh]">
        <Card className="w-xl pt-4">
          <CardContent>
            <ForgotPasswordForm />
          </CardContent>
        </Card>
      </div>
      )
}