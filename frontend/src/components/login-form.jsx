// SHADCN
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Toaster } from "@/components/ui/sonner"

// ME
import { useForm } from 'react-hook-form'; // Manage form state and validation
import { useMutation } from '@tanstack/react-query'; //Perform asynch ops, manage state
import { authServices } from '../services/auth';
import { useNavigate } from "react-router-dom";
import { toast } from "sonner"


export function LoginForm({className,...props}) {

  const navigate = useNavigate()

  // Register is a function to register form fields, handleSubmit handles the form submission
  const {register, handleSubmit} = useForm()

  const loginMutation = useMutation({
    mutationFn: authServices.login, // perform login

    // If successful set tokens and redirect
    onSuccess: (data) => {
      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);
      navigate("/")
    },

    // If failed, we should display error component to user
    onError: (error) => {
      const errorData = error.response?.data; // See if we have custom error
      let errorMessage = 'An error occurred';

      if (errorData) {
        errorMessage = errorData.detail; // Set to custom message
      } else {

        // Collect all error messages from different keys
        const messages = []
        Object.keys(errorData).forEach(key => {
          const message = errorData[key]
          if (Array.isArray(message)) {
            messages.push(...message);
          } else {
            messages.push(message)
          }
        })

        errorMessage = messages.join(' ') || errorMessage;
      }
      toast.warning(errorMessage);
    }
  })

  const onSubmit = (data) => {
    // Trigger the mutation, send email and password
    loginMutation.mutate({
      email: data.email,
      password: data.password
    })
  }

  return (
    (<form className={cn("flex flex-col gap-6", className)} {...props} onSubmit={handleSubmit(onSubmit)}>
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Login to your account</h1>
        <p className="text-muted-foreground text-sm text-balance">
          Enter your email below to login to your account
        </p>
      </div>
      <div className="grid gap-6">
        <div className="grid gap-3">
          <Label htmlFor="email">Email/Username</Label>
          {/* Registers the field with react hook form so it can track inputs */}
          {/* and handle validation  also adds onchange and other attributes*/}
          <Input {...register('email')} id="email" type="text" placeholder="m@example.com" required />
        </div>
        <div className="grid gap-3">
          <div className="flex items-center">
            <Label htmlFor="password">Password</Label>
            <a href="/forgot-password" className="ml-auto text-sm underline-offset-4 hover:underline">
              Forgot your password?
            </a>
          </div>
          <Input {...register('password')} id="password" type="password" required />
        </div>
        <Button type="submit" className="w-full" disabled={loginMutation.isPending}>
          {loginMutation.isPending ? 'Logging in...' : 'Login'}
        </Button>
      </div>
      <div className="text-center text-sm">
        Don&apos;t have an account?{" "}
        <a href="/register" className="underline underline-offset-4">
          Sign up
        </a>
      </div>
      <Toaster position='bottom-left' />
    </form>)
  );
}
