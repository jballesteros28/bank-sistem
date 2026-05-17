import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { LogIn } from "lucide-react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { getApiErrorMessage, getApiErrorStatus, getApiValidationErrors } from "../../../shared/api/apiError";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { useAuth } from "../../../shared/hooks/useAuth";
import { getCurrentUser, login } from "../api";
import { loginSchema } from "../schemas";

function getLoginErrorMessage(error) {
  if (getApiErrorStatus(error) === 400) {
    return "Credenciales inv\u00e1lidas o usuario inexistente.";
  }
  return getApiErrorMessage(error);
}

export function LoginForm() {
  const navigate = useNavigate();
  const { loginSuccess, logout } = useAuth();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const loginMutation = useMutation({
    mutationFn: async (payload) => {
      const session = await login(payload);
      loginSuccess(session.accessToken, session.user);
      const user = session.user || (await getCurrentUser());
      const token = session.accessToken;
      return { token, user };
    },
    onSuccess: ({ token, user }) => {
      loginSuccess(token, user);
      navigate("/dashboard", { replace: true });
    },
    onError: (error) => {
      logout({ redirect: false });
      const validationErrors = getApiValidationErrors(error);
      Object.entries(validationErrors).forEach(([field, message]) => {
        setError(field, { message });
      });
      setError("root", { message: getLoginErrorMessage(error) });
    },
  });

  const onSubmit = (values) => {
    if (loginMutation.isPending) {
      return;
    }
    loginMutation.mutate(values);
  };

  return (
    <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
      {errors.root?.message ? (
        <p role="alert" className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">
          {errors.root.message}
        </p>
      ) : null}
      <Input label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register("email")} />
      <Input label="Password" type="password" autoComplete="current-password" error={errors.password?.message} {...register("password")} />
      <Button type="submit" className="w-full" icon={LogIn} loading={loginMutation.isPending}>
        Ingresar
      </Button>
    </form>
  );
}
