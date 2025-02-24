// SHADCN
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

// ME
import { useForm } from 'react-hook-form'; // Manage form state and validation
import { useMutation } from '@tanstack/react-query'; //Perform asynch ops, manage state
import { authServices } from '../services/auth';
import { useNavigate } from "react-router-dom";
import { Toaster } from "sonner";

export function RegisterForm({className,...props}) {

  const navigate = useNavigate()

  // Register is a function to register form fields, handleSubmit handles the form submission
  const {register, handleSubmit} = useForm()

  const registerMutation = useMutation({
    mutationFn: authServices.register, // perform register

    // If successful set tokens and redirect
    onSuccess: (data) => {
      localStorage.setItem('access', data.access);
      localStorage.setItem('refresh', data.refresh);
      navigate("/")
    },

    // If failed, we should display error component to user
    onError: (error) => {
      toast.warning(error.response?.data?.detail || "An error occurred")
    }
  })

  const onSubmit = (data) => {
    // Trigger the mutation, send email and password
    registerMutation.mutate({
      name: data.name,
      email: data.email,
      username: data.username,
      password: data.password,
      conf_password: data.conf_password,
    })
  }

  return (
    (<form className={cn("flex flex-col gap-6", className)} {...props} onSubmit={handleSubmit(onSubmit)}>

      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Register</h1>
        <p className="text-muted-foreground text-sm text-balance">
          Enter the details below
        </p>
      </div>

      <div className="grid gap-6">

      <div className="grid gap-3">
          <Label htmlFor="name">Full Name</Label>
          {/* Registers the field with react hook form so it can track inputs */}
          {/* and handle validation  also adds onchange and other attributes*/}
          <Input {...register('name')} id="name" type="text" placeholder="First Last" required />
        </div>

        <div className="grid gap-3">
          <Label htmlFor="email">Email</Label>
          <Input {...register('email')} id="email" type="email" placeholder="m@example.com" required />
        </div>

        <div className="grid gap-3">
          <Label htmlFor="username">Username</Label>
          <Input {...register('username')} id="username" type="text" placeholder="username" required />
        </div>

        <div className="grid gap-3">
          <Label htmlFor="password">Password</Label>
          <Input {...register('password')} id="password" type="password" required />
        </div>

        <div className="grid gap-3">
          <Label htmlFor="conf_password">Confirm Password</Label>
          <Input {...register('conf_password')} id="conf_password" type="password" required />
        </div>

        <Button type="submit" className="w-full" disabled={registerMutation.isPending}>
          {registerMutation.isPending ? 'Creating Account...' : 'Register'}
        </Button>
      </div>
      <div className="text-center text-sm">
        Already have an account?{" "}
        <a href="/login" className="underline underline-offset-4">
          Login
        </a>
      </div>
      <Toaster position="bottom-left" /> 
    </form>)
  );
}
