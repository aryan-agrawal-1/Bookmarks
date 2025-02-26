// SHADCN
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Toaster } from "@/components/ui/sonner"

// Mine
import { useForm } from 'react-hook-form'; // Manage form state and validation
import { useMutation } from "@tanstack/react-query"
import { authServices } from "../services/auth"
import { toast } from "sonner"

export function ForgotPasswordForm({className, ...props}) {

    const {register, handleSubmit} = useForm()

    const forgotPassMutation = useMutation({
        mutationFn: authServices.forgotPassword,

        onSettled: () => {
            toast.success('Email sent', {
                description: 'If an account with this email exists, an email has been sent',
              })
        }
    })

    const onSubmit = (data) => {
        forgotPassMutation.mutate(data)
    }

    return (
        <form className={cn("flex flex-col gap-6", className)} {...props} onSubmit={handleSubmit(onSubmit)}>
            <div className="flex flex-col items-center gap-2 text-center">
                <h1 className="text-2xl font-bold">Reset Password</h1>
                <p className="text-muted-foreground text-sm text-balance">
                Enter your email below to reset your password
                </p>
            </div>

            <div className="grid gap-6">
                <div className="grid gap-3">
                    <Label htmlFor="email">Email</Label>
                    {/* Registers the field with react hook form so it can track inputs */}
                    {/* and handle validation  also adds onchange and other attributes*/}
                    <Input {...register('email')} id="email" type="email" placeholder="m@example.com" required />
                </div>

                <Button type="submit" className="w-full" disabled={forgotPassMutation.isPending}>
                    {forgotPassMutation.isPending ? 'Sending Email...' : 'Send Email'}
                </Button>
            </div>
            <Toaster />
        </form>
    )
}