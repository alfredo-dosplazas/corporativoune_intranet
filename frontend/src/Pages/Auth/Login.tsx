import React, {useState} from "react";
import {useForm} from "@inertiajs/react";
import {AuthLayout} from "@/layouts/AuthLayout";
import {getUrl} from "@/utils/routes.ts";

export default function Login() {
    const [showPassword, setShowPassword] = useState(false);

    const {data, setData, post, processing, errors} = useForm({
        username: "",
        password: "",
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post(getUrl('login'));
    };

    return (
        <AuthLayout title="Iniciar Sesión">
            {/* Header Formulario */}
            <div className="text-center lg:text-left space-y-2">
                {/* Logo móvil (visible solo en pantallas pequeñas) */}
                <div className="lg:hidden flex justify-center mb-4">
                    <div className="p-3 bg-primary/10 rounded-2xl text-primary">
                        <span className="icon-[tabler--building-skyscraper] size-10 block"/>
                    </div>
                </div>

                <h2 className="text-2xl font-black tracking-tight text-base-content">
                    Iniciar Sesión
                </h2>
                <p className="text-sm text-base-content/60">
                    Ingresa con tus credenciales institucionales.
                </p>
            </div>

            {/* Formulario */}
            <form onSubmit={handleSubmit} className="space-y-4">
                {/* Campo Usuario */}
                <div className="form-control w-full">
                    <label className="label">
                        <span className="label-text font-semibold">Usuario o Correo</span>
                    </label>
                    <input
                        type="text"
                        className={`input input-bordered w-full ${errors.username ? 'input-error' : ''}`}
                        placeholder="ejemplo@corporativo.com"
                        value={data.username}
                        onChange={(e) => setData("username", e.target.value)}
                    />
                    {errors.username && (
                        <label className="label">
                            <span className="label-text-alt text-error">{errors.username}</span>
                        </label>
                    )}
                </div>

                {/* Campo Contraseña */}
                <div className="form-control w-full">
                    <label className="label">
                        <span className="label-text font-semibold">Contraseña</span>
                    </label>
                    <div className="relative">
                        <input
                            type={showPassword ? "text" : "password"}
                            className={`input input-bordered w-full pr-10 ${errors.password ? 'input-error' : ''}`}
                            placeholder="••••••••"
                            value={data.password}
                            onChange={(e) => setData("password", e.target.value)}
                        />
                        <button
                            type="button"
                            className="absolute inset-y-0 right-0 pr-3 flex items-center text-base-content/60 hover:text-base-content"
                            onClick={() => setShowPassword(!showPassword)}
                        >
                            <span
                                className={`size-5 block ${showPassword ? 'icon-[tabler--eye-off]' : 'icon-[tabler--eye]'}`}/>
                        </button>
                    </div>
                    {errors.password && (
                        <label className="label">
                            <span className="label-text-alt text-error">{errors.password}</span>
                        </label>
                    )}
                </div>

                {/* Botón Submit */}
                <button
                    type="submit"
                    disabled={processing}
                    className="btn btn-primary w-full mt-2"
                >
                    {processing ? (
                        <span className="loading loading-spinner loading-sm"/>
                    ) : (
                        "Ingresar al Sistema"
                    )}
                </button>
            </form>

            {/* Ayuda / Footer del card */}
            <div className="pt-4 border-t border-base-200 text-center text-xs text-base-content/50">
                <p className="flex items-center justify-center gap-1.5">
                    <span className="icon-[tabler--lock] size-4 text-primary"/>
                    Conexión cifrada y segura
                </p>
            </div>
        </AuthLayout>
    );
}