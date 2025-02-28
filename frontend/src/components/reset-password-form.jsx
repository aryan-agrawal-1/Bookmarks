// SHADCN
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";

// Mine
import { useForm } from "react-hook-form"; // Manage form state and validation
import { useMutation } from "@tanstack/react-query";
import { authServices } from "../services/auth";
import { useParams } from "react-router-dom"; // Get dynamic parameters from the URL
import { useNavigate } from "react-router-dom";

export function ResetPasswordForm({ className, ...props }) {
  const { register, handleSubmit } = useForm();
  const navigate = useNavigate();
  const { uid, token } = useParams(); // Get UID and token from URL

  const resetPasswordMutation = useMutation({
    mutationFn: authServices.resetPassword,

    onSuccess: () => {
      toast.success("Your password has been updated");
      navigate("/login");
    },

    onError: (error) => {
      const errorData = error.response?.data; // See if we have custom error
      let errorMessage = "An error occurred";

      if (errorData) {
        errorMessage = errorData.detail; // Set to custom message
      } else {
        // Collect all error messages from different keys
        const messages = [];
        Object.keys(errorData).forEach((key) => {
          const message = errorData[key];
          if (Array.isArray(message)) {
            messages.push(...message);
          } else {
            messages.push(message);
          }
        });

        errorMessage = messages.join(" ") || errorMessage;
      }
      toast.warning(errorMessage);
    },
  });

  const onSubmit = (data) => {
    resetPasswordMutation.mutate({
      uid,
      token,
      new_pass: data.newPassword,
      conf_pass: data.confPassword,
    });
  };

  return (
    <form
      className={cn("flex flex-col gap-6", className)}
      {...props}
      onSubmit={handleSubmit(onSubmit)}
    >
      <div className="flex flex-col items-center gap-2 text-center">
        <h1 className="text-2xl font-bold">Reset your password</h1>
        <p className="text-muted-foreground text-sm text-balance">
          Enter your new password below
        </p>
      </div>

      <div className="grid gap-6">

        <div className="grid gap-3">
          <Label htmlFor="newPassword">Password</Label>
          {/* Registers the field with react hook form so it can track inputs */}
          {/* and handle validation  also adds onchange and other attributes*/}
          <Input
            {...register("newPassword")}
            id="newPassword"
            type="password"
            required
          />
        </div>

        <div className="grid gap-3">
          <Label htmlFor="confPassword">Confirm Password</Label>
          <Input
            {...register("confPassword")}
            id="confPassword"
            type="password"
            required
          />
        </div>
        
        <Button
          type="submit"
          className="w-full"
          disabled={resetPasswordMutation.isPending}
        >
          {resetPasswordMutation.isPending ? "Resetting..." : "Reset"}
        </Button>
      </div>

      <Toaster position = 'bottom-left' />
    </form>
  );
}
