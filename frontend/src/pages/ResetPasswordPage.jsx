import { ResetPasswordForm } from "../components/reset-password-form";
import {Card, CardHeader, CardTitle, CardDescription, CardContent} from "../components/ui/card"

export default function ResetPasswordPage() {
    return (
      <div className="flex items-center justify-center m-auto h-[100vh]">
        <Card className="w-xl pt-4">
          <CardContent>
            <ResetPasswordForm />
          </CardContent>
        </Card>
      </div>
      )
}